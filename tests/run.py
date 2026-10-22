import concurrent.futures
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from api import load_index
from gdscript import PROJECT, source
from markdown import ROOT, parse_doc

FIXTURES = ROOT / "tests" / "run"
FRAMES = 60
TIMEOUT = 60
HEADING = re.compile(r"^##\s+(\S+)\s+`([^`]+)`\s*$")
OPTION = re.compile(r"<!--\s*run:\s*(.+?)\s*-->")
PROBLEM = re.compile(r"^(?:[A-Z]+ )*(?:ERROR|WARNING)\b|Parse Error|Assertion failed")
BENIGN = re.compile(r"resources still in use at exit|RID allocations of type .* were leaked at exit")
ANSI = re.compile(r"\x1b\[[0-9;]*m")
INPUT_CALL = re.compile(r"(?:Input\.\w+|is_action\w*)\s*\(([^)]*)\)")
STRING = re.compile(r"&?\"(\w+)\"")
ONREADY = re.compile(r"^@onready\s+var\s+\w+\s*:\s*(\w+)\s*=\s*([$%])(\"[^\"]+\"|[\w/]+)\s*$", re.M)
EXPORT = re.compile(r"^@export\s+var\s+(\w+)\s*:\s*([A-Z]\w*)\s*$", re.M)
PUBLIC_FUNC = re.compile(r"^(?:static\s+)?func\s+([a-z]\w*)\s*\(", re.M)
CLASS_NAME = re.compile(r"^class_name\s+(\w+)", re.M)
EXTENDS = re.compile(r"^extends\s+(\w+)", re.M)
EDITOR = re.compile(r"\bEditor[A-Z]\w*")


@dataclass
class Fixture:
    anchor: str
    where: str
    options: dict = field(default_factory=dict)
    prepare: str = ""
    setup: str = ""
    run: str = ""


@dataclass
class Job:
    doc: str
    block: object
    index: int
    blocks: list
    mode: str
    is_node: bool
    fixture: Fixture | None


def parse_fixtures(path: Path) -> dict:
    doc = parse_doc(path)
    lines = doc.text.split("\n")
    entries = []
    for n, line in enumerate(lines, 1):
        m = HEADING.match(line)
        if m:
            entries.append((n, m.group(1), Fixture(m.group(2), f"{doc.where}:{n}")))
            continue
        opt = OPTION.search(line)
        if opt and entries:
            for part in opt.group(1).split(";"):
                key, _, value = part.strip().partition(" ")
                entries[-1][2].options[key] = value.strip()
    for b in doc.blocks:
        start = int(b.where.rsplit(":", 1)[1])
        owner = [e for e in entries if e[0] < start]
        if not owner or b.lang != "gdscript":
            continue
        fx = owner[-1][2]
        part = "prepare" if "prepare" in b.tags else "setup" if "setup" in b.tags else "run"
        setattr(fx, part, getattr(fx, part) + b.code)
    out = {}
    for _, doc_path, fx in entries:
        out.setdefault(doc_path, []).append(fx)
    return out


def indent(body: str, default: str) -> str:
    body = body.strip("\n") or default
    return "\n".join("\t" + line if line else line for line in body.split("\n"))


def node_base(code: str, classes: dict, index: dict) -> bool:
    m = EXTENDS.search(code)
    name = m.group(1) if m else "RefCounted"
    seen = set()
    while name in classes and name not in seen:
        seen.add(name)
        m = EXTENDS.search(classes[name])
        name = m.group(1) if m else "RefCounted"
    while name:
        if name == "Node":
            return True
        name = index["classes"].get(name, {}).get("inherits")
    return False


def actions(job: Job) -> list:
    fx = job.fixture
    code = job.block.code + (fx.prepare + fx.setup + fx.run if fx else "")
    found = []
    for call in INPUT_CALL.findall(code):
        for name in STRING.findall(call):
            if name not in found and not name.startswith("ui_"):
                found.append(name)
    return found


def build_lines(job: Job) -> list:
    code = job.block.code
    out = ["node = Snippet.new()"]
    if job.is_node:
        for type_name, sigil, path in ONREADY.findall(code):
            out.append(f'_child("{path.strip(chr(34))}", "{type_name}", {"true" if sigil == "%" else "false"})')
    for prop, type_name in EXPORT.findall(code):
        out.append(f'_fill("{prop}", "{type_name}")')
    return out


FRAMES_HELPER = """
func frames(count: int) -> void:
	for i in count:
		await %s


func wait_real(seconds: float) -> void:
	var end := Time.get_ticks_msec() + int(seconds * 1000.0)
	while Time.get_ticks_msec() < end:
		await %s


func expect(ok: bool, what: String) -> void:
	if not ok:
		push_error("EXPECT " + what)


func make_tone(seconds: float = 0.2) -> AudioStreamWAV:
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = 22050
	var data := PackedByteArray()
	data.resize(int(seconds * wav.mix_rate) * 2)
	for i in range(0, data.size(), 2):
		data.encode_s16(i, int(sin(i * 0.05) * 8000.0))
	wav.data = data
	return wav


func make_texture(width: int = 32, height: int = 32, color: Color = Color.WHITE) -> ImageTexture:
	var image := Image.create_empty(width, height, false, Image.FORMAT_RGBA8)
	image.fill(color)
	return ImageTexture.create_from_image(image)


func make_scene(root_node: Node) -> PackedScene:
	for child in root_node.find_children("*", "", true, false):
		child.owner = root_node
	var packed := PackedScene.new()
	packed.pack(root_node)
	root_node.free()
	return packed
"""

MAKE_HELPER = """
func _make(type_name: String) -> Object:
	if ClassDB.class_exists(type_name):
		return ClassDB.instantiate(type_name) if ClassDB.can_instantiate(type_name) else null
	for info: Dictionary in ProjectSettings.get_global_class_list():
		if info["class"] == type_name:
			return (load(info["path"]) as GDScript).new()
	return null


func _fill(prop: String, type_name: String) -> void:
	if node.get(prop) != null:
		return
	var value := _make(type_name)
	if value == null:
		return
%s	node.set(prop, value)
"""

FILL_NODE = """	if value is Node:
		(value as Node).name = prop.to_pascal_case()
		node.add_child(value)
"""

CHILD_HELPER = """
func _child(path: String, type_name: String, unique: bool) -> void:
	var parent: Node = node
	var parts := path.split("/")
	for i in parts.size():
		var found := parent.get_node_or_null(parts[i])
		if found == null:
			found = _make(type_name if i == parts.size() - 1 else "Node") as Node
			found.name = parts[i]
			parent.add_child(found)
			found.owner = node
			found.unique_name_in_owner = unique
		parent = found
"""


def driver(job: Job, name: str) -> str:
    fx = job.fixture or Fixture("", "")
    frames_default = f"await frames({fx.options.get('frames', FRAMES)})"
    editor = job.mode == "editor"
    tree = "get_tree()" if editor else "self"
    attach = "EditorInterface.get_base_control()" if editor else "root"
    head = ["@tool", "extends EditorPlugin"] if editor else ["extends SceneTree"]
    body = [*head, "", f'const Snippet = preload("res://{name}")', "", "var node: Snippet", ""]
    if editor:
        body += ["func _enter_tree() -> void:", "\t_main.call_deferred()", ""]
    else:
        body += ["func _initialize() -> void:", "\t_main()", ""]
    body += ["", "func _main() -> void:"]
    if not editor:
        # _initialize 时 root 还不在树内
        body += ["\tawait process_frame"]
    if editor:
        body += ["\twhile EditorInterface.get_resource_filesystem().is_scanning():", "\t\tawait get_tree().process_frame"]
    body += ["\t" + line for line in build_lines(job)]
    body += ["\tawait _setup()"]
    if job.is_node:
        body += [f"\t{attach}.add_child(node)"]
    body += ["\tawait _run()", "\tawait frames(2)"]
    if job.is_node:
        body += ["\tif is_instance_valid(node):", "\t\tnode.queue_free()"]
    # 音频线程按真实时间回收播放实例
    body += ["\tnode = null", "\tawait wait_real(0.1)", '\tprint("RUN_DONE")', f"\t{tree}.quit()", ""]
    body += ["", "func _setup() -> void:", "\tawait frames(0)", indent(fx.setup, "pass"), ""]
    body += ["", "func _run() -> void:", "\tawait frames(0)", indent(fx.run, frames_default), ""]
    frame = "get_tree().process_frame" if editor else "physics_frame"
    body.append(FRAMES_HELPER % (frame, frame))
    body.append(MAKE_HELPER % (FILL_NODE if job.is_node else ""))
    if job.is_node:
        body.append(CHILD_HELPER)
    return "\n".join(body)


def godot_cmd(godot: str, job: Job, proj: Path, *args: str) -> list:
    if job.mode == "render":
        driver_name = job.fixture.options.get("driver", "vulkan") if job.fixture else "vulkan"
        return ["xvfb-run", "-a", godot, "--path", str(proj), "--rendering-driver", driver_name, "--audio-driver", "Dummy", *args]
    return [godot, "--headless", "--path", str(proj), *args]


def isolated(proj: Path) -> dict:
    env = dict(os.environ)
    for var in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        env[var] = str(proj / ".xdg" / var.lower())
    return env


def import_doc(godot: str, blocks: list, base: Path) -> None:
    # 每个文档导入一次 各代码块复制 .godot 再跑
    base.mkdir(parents=True)
    for n, b in enumerate(blocks):
        (base / f"s{n}.gd").write_text(source(b)[0])
    (base / "project.godot").write_text(PROJECT)
    cmd = [godot, "--headless", "--path", str(base), "--import"]
    subprocess.run(cmd, capture_output=True, timeout=TIMEOUT, env=isolated(base))


def run_job(godot: str, job: Job, base: Path, proj: Path) -> tuple:
    shutil.copytree(base, proj, ignore=shutil.ignore_patterns(".xdg"))
    env = isolated(proj)
    me = f"s{job.index}.gd"
    project = PROJECT + "\n[display]\n\nwindow/vsync/vsync_mode=0\n"
    # 示例默认工程里已配好这些动作
    names = actions(job)
    if names:
        project += "\n[input]\n\n" + "".join(f'{n}={{"deadzone": 0.2, "events": []}}\n' for n in names)
    if job.mode == "editor":
        plugin = proj / "addons" / "_run"
        plugin.mkdir(parents=True)
        (plugin / "plugin.cfg").write_text('[plugin]\n\nname="run"\ndescription=""\nauthor=""\nversion="1"\nscript="plugin.gd"\n')
        (plugin / "plugin.gd").write_text(driver(job, me))
        project += '\n[editor_plugins]\n\nenabled=PackedStringArray("res://addons/_run/plugin.cfg")\n'
    elif job.mode != "script":
        (proj / "_run.gd").write_text(driver(job, me))
    (proj / "project.godot").write_text(project)
    logs = []

    def call(*args: str) -> subprocess.CompletedProcess:
        try:
            res = subprocess.run(godot_cmd(godot, job, proj, *args), capture_output=True, text=True, timeout=TIMEOUT, env=env)
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            return subprocess.CompletedProcess(args, -1, out + "\nRUN_TIMEOUT", "")
        logs.append(ANSI.sub("", res.stdout + res.stderr))
        return res

    if job.fixture and job.fixture.prepare:
        wrap = "extends SceneTree\n\nfunc _initialize() -> void:\n" + indent(job.fixture.prepare, "pass") + "\n\tquit()\n"
        (proj / "_prepare.gd").write_text(wrap)
        call("-s", "res://_prepare.gd")
        call("--import")
    if job.mode == "editor":
        res = call("--editor")
    elif job.mode == "script":
        res = call("--fixed-fps", "60", "-s", f"res://{me}")
    else:
        res = call("--fixed-fps", "60", "-s", "res://_run.gd")
    if res.returncode == -1:
        logs.append(res.stdout)
    text = "\n".join(logs)
    problems = [ln.strip() for ln in text.split("\n") if PROBLEM.search(ln) and not BENIGN.search(ln)]
    done = job.mode == "script" or "RUN_DONE" in text
    ok = not problems and done and res.returncode == 0
    if "RUN_TIMEOUT" in text:
        detail = [f"{TIMEOUT} 秒超时", *problems[:3], *text.strip().split("\n")[-3:-1]]
    else:
        detail = problems[:4] or ([] if done else ["未跑完 " + " | ".join(text.strip().split("\n")[-4:])])
    if not detail and res.returncode != 0:
        detail = [f"退出码 {res.returncode}"]
    return ok, detail, text


def plan(docs: list, index: dict) -> tuple:
    fixtures = {}
    out = []
    for path in sorted(FIXTURES.glob("*.md")):
        for doc_path, items in parse_fixtures(path).items():
            fixtures[f"skills/{path.stem}/{doc_path}"] = items
    jobs = []
    for d in docs:
        blocks = [b for b in d.blocks if b.lang == "gdscript" and "skip" not in b.tags]
        classes = {}
        for b in blocks:
            m = CLASS_NAME.search(b.code)
            if m:
                classes[m.group(1)] = source(b)[0]
        doc_fixtures = fixtures.pop(d.where, [])
        for fx in doc_fixtures:
            hits = [b for b in blocks if fx.anchor in b.code]
            if len(hits) != 1:
                out.append(("ERROR", fx.where, f"run 锚点 {fx.anchor} 命中 {len(hits)} 个代码块"))
        for n, b in enumerate(blocks):
            fx = next((f for f in doc_fixtures if f.anchor in b.code), None)
            code = source(b)[0]
            opts = fx.options if fx else {}
            if "norun" in opts:
                jobs.append(("norun", b, opts["norun"]))
                continue
            if "mode" in opts:
                mode = opts["mode"]
            elif re.search(r"^extends\s+SceneTree\b", code, re.M):
                mode = "script"
            elif EDITOR.search(code):
                mode = "editor"
            else:
                mode = "game"
            jobs.append(Job(d.where, b, n, blocks, mode, node_base(code, classes, index), fx))
    for where in fixtures:
        if (ROOT / where).exists():
            continue
        out.append(("ERROR", f"tests/run/{where.split('/')[1]}.md", f"run 指向不存在的文档 {where}"))
    return jobs, out


def coverage(job: Job) -> list:
    called = job.fixture.setup + job.fixture.run if job.fixture else ""
    code = job.block.code
    missing = []
    for name in PUBLIC_FUNC.findall(code):
        used = len(re.findall(rf"\b{name}\b", code)) > 1
        if not used and not re.search(rf"\b{name}\b", called):
            missing.append(name)
    return missing


def check(docs: list, godot: str, jobs_n: int) -> list:
    index = load_index()
    jobs, out = plan(docs, index)
    runnable = [j for j in jobs if isinstance(j, Job)]
    if any(j.mode == "render" for j in runnable) and not shutil.which("xvfb-run"):
        out.append(("ERROR", "run", "找不到 xvfb-run"))
        runnable = [j for j in runnable if j.mode != "render"]
    with tempfile.TemporaryDirectory(prefix="gdrun") as tmp:
        bases = {}
        for j in runnable:
            bases.setdefault(j.doc, (Path(tmp) / f"doc{len(bases)}", j.blocks))
        with concurrent.futures.ThreadPoolExecutor(jobs_n) as pool:
            list(pool.map(lambda kv: import_doc(godot, kv[1], kv[0]), bases.values()))
            futures = {}
            for i, j in enumerate(runnable):
                futures[pool.submit(run_job, godot, j, bases[j.doc][0], Path(tmp) / str(i))] = j
            for f, j in futures.items():
                ok, detail, _ = f.result()
                if not ok:
                    out.append(("ERROR", j.block.where, f"run {j.mode} " + " / ".join(detail)))
                missing = coverage(j)
                if missing:
                    out.append(("WARN", j.block.where, "run 未调用 " + " ".join(missing)))
    counts = {}
    for j in runnable:
        counts[j.mode] = counts.get(j.mode, 0) + 1
    norun = [j for j in jobs if not isinstance(j, Job)]
    print("run " + " ".join(f"{k} {v}" for k, v in sorted(counts.items())) + f" norun {len(norun)}")
    for _, b, reason in norun:
        print(f"  norun {b.where} {reason}")
    return out
