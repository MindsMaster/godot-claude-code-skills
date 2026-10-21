import gzip
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
INLINE_CODE = re.compile(r"`([^`\n]+)`")
CAMEL = re.compile(r"^[A-Z][A-Za-z0-9]*[a-z][A-Za-z0-9]*$")
SETTING = re.compile(r"^[a-z0-9_]+(/[a-z0-9_]+)+(\.[a-z0-9_]+)?$")
MEMBER_REF = re.compile(r"^([A-Z][A-Za-z0-9]*)\.([A-Za-z_][A-Za-z0-9_]*)(?:\(.*\))?$")
NEEDS_VERSION_AFTER = (4, 4)


def snake(name: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    s = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", s)
    return s.lower()


def load_index() -> dict:
    with gzip.open(DATA / "godot_api.json.gz", "rt", encoding="utf-8") as f:
        return json.load(f)


def members(index: dict, cls: str) -> set:
    out = set()
    if cls in index["builtins"]:
        b = index["builtins"][cls]
        out.update(b["methods"], b["members"], b["constants"], b["enums"])
        for values in b["enums"].values():
            out.update(values)
        return out
    while cls in index["classes"]:
        c = index["classes"][cls]
        out.update(c["methods"], c["properties"], c["signals"], c["constants"], c["enums"])
        for values in c["enums"].values():
            out.update(values)
        cls = c["inherits"]
    return out


def check(docs: list) -> list:
    index = load_index()
    classes = index["classes"]
    known_types = set(classes) | set(index["builtins"]) | set(index["global_enums"])
    allow = set((DATA / "allow_names.txt").read_text(encoding="utf-8").split())
    known_types |= allow
    settings = set(index["project_settings"]) | allow
    setting_roots = {name.split("/")[0] for name in settings}
    deprecated = [cls for cls, names in index["deprecated"].items() if "" in names]
    out = []
    for d in docs:
        for lineno, line in d.prose:
            where = f"{d.where}:{lineno}"
            for token in INLINE_CODE.findall(line):
                token = token.strip()
                m = MEMBER_REF.match(token)
                if m:
                    cls, member = m.groups()
                    if cls in classes or cls in index["builtins"]:
                        names = members(index, cls)
                        if not {member, snake(member), snake(member).upper()} & names:
                            out.append(("ERROR", where, f"{cls} 没有成员 {member}"))
                elif SETTING.match(token) and token.split("/")[0] in setting_roots:
                    base = token.split(".")[0]
                    if base not in settings and not any(n.startswith(base + "/") for n in settings):
                        out.append(("ERROR", where, f"项目设置不存在 {token}"))
                elif CAMEL.match(token) and token not in known_types:
                    out.append(("WARN", where, f"未知类型名 {token} 引擎没有 也不在 allow_names.txt"))
        for b in d.blocks:
            if b.lang in ("gdscript", "csharp") and "deprecated" not in b.tags:
                for cls in deprecated:
                    if re.search(rf"\b{cls}\b", b.code):
                        out.append(("ERROR", b.where, f"代码块用了已弃用的 {cls}"))
        marked = set(re.findall(r"4\.\d+(?=\+)", d.text))
        for name in set(re.findall(r"\b[A-Z][A-Za-z0-9]+\b", d.text)):
            since = classes.get(name, {}).get("since")
            if since and tuple(map(int, since.split("."))) > NEEDS_VERSION_AFTER and since not in marked:
                out.append(("WARN", d.where, f"{name} 自 {since} 起才有 正文未标 {since}+"))
    return out
