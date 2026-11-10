"""加载 ```ini 代码块里的 .tres 与 .tscn 文本，逐条核对属性名。

首行是 [gd_resource 或 [gd_scene 的代码块参与，`<!-- check: skip -->` 跳过。
ext_resource 指向的文件不存在时按类型补占位文件：音频、脚本、场景、贴图。
加载后每个段落里写的属性都要能在对应对象上 get 到，用来发现拼错的属性名。
"""
import concurrent.futures
import json
import re
import subprocess
import tempfile
from pathlib import Path

PROJECT = 'config_version=5\n\n[application]\n\nconfig/name="resources"\n'
HEADER = re.compile(r"^\[(gd_resource|gd_scene)\b")
SECTION = re.compile(r"^\[(\w+)(.*)\]\s*$")
ATTR = re.compile(r'(\w+)=("[^"]*"|\S+)')
KEY = re.compile(r"^([\w/]+) = ")
WAV = (b"RIFF\x24\x58\x01\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\xbb\x00\x00\x00\x77\x01\x00"
       b"\x02\x00\x10\x00data\x00\x58\x01\x00" + bytes(88064))
PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")

RUNNER = """extends SceneTree

var _fails := 0


func _init() -> void:
\tvar plan: Array = JSON.parse_string(FileAccess.get_file_as_string("res://_plan.json"))
\tfor item: Dictionary in plan:
\t\t_check(item)
\tquit(1 if _fails > 0 else 0)


func _check(item: Dictionary) -> void:
\tvar path: String = item.path
\tvar res := ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_IGNORE)
\tif res == null:
\t\t_fail(path, "加载失败")
\t\treturn
\tvar root: Object = res
\tif res is PackedScene:
\t\troot = (res as PackedScene).instantiate()
\tvar subs := {}
\t_collect(root, subs, {})
\tfor section: Dictionary in item.sections:
\t\tvar target: Object = null
\t\tmatch section.kind:
\t\t\t"resource":
\t\t\t\ttarget = res
\t\t\t"sub_resource":
\t\t\t\ttarget = subs.get(section.id)
\t\t\t"node":
\t\t\t\tif root is Node:
\t\t\t\t\ttarget = root if section.path == "" else (root as Node).get_node_or_null(NodePath(section.path))
\t\tif target == null:
\t\t\t_fail(path, "找不到 %s %s" % [section.kind, section.get("id", section.get("path", ""))])
\t\t\tcontinue
\t\tfor key: String in section.keys:
\t\t\tif target.get(key) == null:
\t\t\t\t_fail(path, "%s 没有属性 %s" % [target.get_class(), key])
\tif root is Node:
\t\t(root as Node).free()


func _collect(obj: Object, subs: Dictionary, seen: Dictionary) -> void:
\tif obj == null or seen.has(obj):
\t\treturn
\tseen[obj] = true
\tif obj is Resource and (obj as Resource).resource_scene_unique_id != "":
\t\tsubs[(obj as Resource).resource_scene_unique_id] = obj
\tif obj is Node:
\t\tfor child in (obj as Node).get_children():
\t\t\t_collect(child, subs, seen)
\tfor p in obj.get_property_list():
\t\tvar v: Variant = obj.get(p.name)
\t\tif v is Resource:
\t\t\t_collect(v, subs, seen)
\t\telif v is Array:
\t\t\tfor e: Variant in v:
\t\t\t\tif e is Resource:
\t\t\t\t\t_collect(e, subs, seen)


func _fail(path: String, msg: String) -> void:
\t_fails += 1
\tprinterr("RES_FAIL ", path, " ", msg)
"""


def stub(proj: Path, path: str, kind: str) -> None:
    dest = proj / path.removeprefix("res://")
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.suffix == ".wav":
        dest.write_bytes(WAV)
    elif dest.suffix == ".png":
        dest.write_bytes(PNG)
    elif dest.suffix == ".gd":
        dest.write_text("extends Node\n")
    elif dest.suffix == ".tscn":
        dest.write_text('[gd_scene format=3]\n\n[node name="Stub" type="Node"]\n')
    elif dest.suffix == ".tres":
        dest.write_text(f'[gd_resource type="{kind}" format=3]\n\n[resource]\n')


def plan(code: str, proj: Path, name: str) -> dict:
    sections = []
    current = None
    for line in code.split("\n"):
        m = SECTION.match(line)
        if m:
            kind, attrs = m.group(1), dict((k, v.strip('"')) for k, v in ATTR.findall(m.group(2)))
            current = None
            if kind == "ext_resource":
                stub(proj, attrs["path"], attrs.get("type", ""))
            elif kind == "sub_resource":
                current = {"kind": kind, "id": attrs["id"], "keys": []}
            elif kind == "resource":
                current = {"kind": kind, "keys": []}
            elif kind == "node" and "instance" not in attrs:
                parent = attrs.get("parent")
                path = "" if parent is None else (attrs["name"] if parent == "." else f"{parent}/{attrs['name']}")
                current = {"kind": kind, "path": path, "keys": []}
            if current is not None:
                sections.append(current)
            continue
        k = KEY.match(line)
        # 挂了脚本的节点 属性可能来自脚本的 @export 跳过
        if current is not None and k:
            if k.group(1) == "script":
                current["keys"] = None
            elif current["keys"] is not None and not line.rstrip().endswith("= null"):
                current["keys"].append(k.group(1))
    return {"path": f"res://{name}", "sections": [s for s in sections if s["keys"] is not None]}


def check_doc(godot: str, blocks: list, proj: Path) -> list:
    proj.mkdir(parents=True)
    (proj / "project.godot").write_text(PROJECT)
    (proj / "_runner.gd").write_text(RUNNER)
    items, where = [], {}
    for n, b in enumerate(blocks):
        name = f"r{n}.{'tscn' if b.code.startswith('[gd_scene') else 'tres'}"
        # Ogg MP3 造不出占位文件 换成同名 WAV 只验结构与属性名
        code = re.sub(r'path="(res://[^"]+\.(?:ogg|mp3))"', r'path="\1.wav"', b.code)
        (proj / name).write_text(code)
        items.append(plan(code, proj, name))
        where[f"res://{name}"] = b.where
    (proj / "_plan.json").write_text(json.dumps(items, ensure_ascii=False))
    subprocess.run([godot, "--headless", "--path", str(proj), "--import"], capture_output=True, timeout=600)
    res = subprocess.run([godot, "--headless", "--path", str(proj), "-s", "_runner.gd"],
                         capture_output=True, text=True, timeout=600)
    out = []
    lines = (res.stdout + res.stderr).split("\n")
    for line in lines:
        if line.startswith("RES_FAIL "):
            path, _, msg = line.removeprefix("RES_FAIL ").partition(" ")
            out.append(("ERROR", where.get(path, path), f"资源 {msg}"))
    for line, nxt in zip(lines, lines[1:]):
        m = re.search(r"res://(r\d+\.t\w+)", line + nxt)
        if m and line.startswith("ERROR:") and f"res://{m.group(1)}" in where:
            out.append(("ERROR", where[f"res://{m.group(1)}"], f"资源 {line.strip()}"))
    if res.returncode != 0 and not out:
        out.append(("ERROR", blocks[0].where, f"资源检查退出码 {res.returncode} {res.stderr[-300:]}"))
    return out


def check(docs: list, godot: str, jobs: int) -> list:
    groups = []
    for d in docs:
        blocks = [b for b in d.blocks if b.lang == "ini" and HEADER.match(b.code) and "skip" not in b.tags]
        if blocks:
            groups.append(blocks)
    out = []
    with tempfile.TemporaryDirectory(prefix="ressnip") as tmp:
        with concurrent.futures.ThreadPoolExecutor(jobs) as pool:
            futures = [pool.submit(check_doc, godot, g, Path(tmp) / str(i)) for i, g in enumerate(groups)]
            for f in futures:
                out.extend(f.result())
    print(f"资源片段 {sum(len(g) for g in groups)} 个")
    return out
