import concurrent.futures
import re
import subprocess
import tempfile
from pathlib import Path

# 引擎默认报警告的项与 untyped_declaration 全升为错误
WARNINGS = """
assert_always_false assert_always_true confusable_capture_reassignment confusable_identifier
confusable_local_declaration confusable_local_usage confusable_temporary_modification
constant_used_as_function deprecated_keyword empty_file enum_variable_without_default
function_used_as_property incompatible_ternary int_as_enum_without_cast int_as_enum_without_match
integer_division missing_tool narrowing_conversion property_used_as_function redundant_await
redundant_static_unload shadowed_global_identifier shadowed_variable shadowed_variable_base_class
standalone_expression standalone_ternary static_called_on_instance unassigned_variable
unassigned_variable_op_assign unreachable_code unreachable_pattern unsafe_void_return
unused_local_constant unused_parameter unused_private_class_variable unused_signal unused_variable
untyped_declaration
""".split()

PROJECT = """config_version=5

[application]

config/name="snippets"

[debug]

""" + "".join(f"gdscript/warnings/{w}=2\n" for w in WARNINGS)

RUNNER = """extends SceneTree

func _init() -> void:
\tfor path in OS.get_cmdline_user_args():
\t\tvar s: GDScript = load(path)
\t\tif s == null or not s.can_instantiate():
\t\t\tprinterr("CHECK_FAIL ", path)
\tquit()
"""

LOCATION = re.compile(r"res://(s\d+\.gd):(\d+)")


def source(b) -> tuple:
    ext = b.tags.get("extends")
    if ext and not re.search(r"^extends\b", b.code, re.M):
        return f"extends {ext}\n\n{b.code}", 2
    return b.code, 0


def check_doc(godot: str, blocks: list, proj: Path) -> list:
    # 同一文档的片段共用一个工程 互相能引用 class_name
    proj.mkdir(parents=True)
    (proj / "project.godot").write_text(PROJECT)
    (proj / "_runner.gd").write_text(RUNNER)
    files = {}
    for n, b in enumerate(blocks):
        code, shift = source(b)
        (proj / f"s{n}.gd").write_text(code)
        files[f"s{n}.gd"] = (b, shift)
    subprocess.run([godot, "--headless", "--path", str(proj), "--import"], capture_output=True, timeout=600)
    args = [f"res://{name}" for name in files]
    res = subprocess.run(
        [godot, "--headless", "--path", str(proj), "-s", "_runner.gd", "--", *args],
        capture_output=True,
        text=True,
        timeout=600,
    )
    lines = (res.stdout + res.stderr).split("\n")
    out = []
    reported = set()
    for line, nxt in zip(lines, lines[1:]):
        m = LOCATION.search(nxt)
        if m and m.group(1) in files and ("Parse Error" in line or "SCRIPT ERROR" in line):
            b, shift = files[m.group(1)]
            out.append(("ERROR", b.where, f"gdscript {line.strip()} 代码块第 {int(m.group(2)) - shift} 行"))
            reported.add(m.group(1))
    for line in lines:
        if line.startswith("CHECK_FAIL"):
            name = line.split("res://")[1].strip()
            if name not in reported:
                out.append(("ERROR", files[name][0].where, "gdscript 加载失败"))
    return out


def check(docs: list, godot: str, jobs: int) -> list:
    groups = []
    for d in docs:
        blocks = [b for b in d.blocks if b.lang == "gdscript" and "skip" not in b.tags]
        if blocks:
            groups.append(blocks)
    out = []
    with tempfile.TemporaryDirectory(prefix="gdsnip") as tmp:
        with concurrent.futures.ThreadPoolExecutor(jobs) as pool:
            futures = [pool.submit(check_doc, godot, g, Path(tmp) / str(i)) for i, g in enumerate(groups)]
            for f in futures:
                out.extend(f.result())
    print(f"gdscript 片段 {sum(len(g) for g in groups)} 个")
    return out
