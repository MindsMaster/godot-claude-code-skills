import re
from pathlib import Path

from markdown import frontmatter

BANNED = ["显著", "大幅", "彻底", "真正", "其实", "确实", "正是", "恰好", "值得注意的是", "换句话说", "顺带", "顺手", "——"]
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
MAX_SKILL_LINES = 300
WRONG_LANG = {"gd", "py", "python", "c#", "cs"}
SKELETON = ["范围", "先查内置", "做法", "陷阱", "参考"]
MAX_BULLET_CHARS = 40
CODE_SPAN_RE = re.compile(r"`[^`]*`")
SKILL_REF_RE = re.compile(r"\bgodot-[a-z0-9-]+")
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
WORD_RE = re.compile(r"[A-Za-z0-9_+.#/-]+")


def is_migrated(skill_dir: Path) -> bool:
    skill = skill_dir / "SKILL.md"
    return skill.exists() and "\n## 范围\n" in skill.read_text(encoding="utf-8")


def check_bullets(d, skip_section: str = "") -> list:
    out = []
    section = ""
    for lineno, line in d.prose:
        if line.startswith("## "):
            section = line[3:].strip()
        elif line.startswith("- ") and section != skip_section:
            n = len(WORD_RE.sub("x", CODE_SPAN_RE.sub("x", MD_LINK_RE.sub("x", line[2:]))).replace(" ", ""))
            if n > MAX_BULLET_CHARS:
                out.append(("WARNING", f"{d.where}:{lineno}", f"列表项 {n} 字 超过 {MAX_BULLET_CHARS} 拆条或改表格"))
    return out


def block_line(b) -> int:
    return int(b.where.rsplit(":", 1)[1])


def method_sections(d) -> tuple:
    heads = []
    section = ""
    for lineno, line in d.prose:
        if line.startswith("## "):
            section = line[3:].strip()
            heads.append((lineno, None))
        elif line.startswith("### "):
            heads.append((lineno, line[4:].strip() if section == "做法" else None))
    with_gd = set()
    for b in d.blocks:
        if b.lang != "gdscript" or "gdonly" in b.tags:
            continue
        owner = None
        for lineno, name in heads:
            if lineno < block_line(b):
                owner = name
        if owner:
            with_gd.add(owner)
    return {name for _, name in heads if name}, with_gd


def check_csharp_pairs(d) -> list:
    out = []
    for i, b in enumerate(d.blocks):
        if b.lang == "gdscript" and "gdonly" not in b.tags:
            nxt = d.blocks[i + 1] if i + 1 < len(d.blocks) else None
            if nxt is None or nxt.lang != "csharp":
                out.append(("ERROR", b.where, "GDScript 代码块后须紧跟 C# 版本 只有 GDScript 才有的加 gdonly"))
    return out


def check_csharp_mirror(skill_doc, docs: list) -> list:
    path = skill_doc.path.parent / "references" / "csharp.md"
    allowed, want = method_sections(skill_doc)
    if not want:
        return []
    mirror = next((x for x in docs if x.path == path), None)
    if mirror is None:
        return [("ERROR", skill_doc.where, "缺少 references/csharp.md")]
    have = {l[3:].strip() for _, l in mirror.prose if l.startswith("## ")}
    out = []
    for name in sorted(want - have):
        out.append(("ERROR", mirror.where, f"缺少 ## {name} 对应 SKILL.md 的 ### {name}"))
    for name in sorted(have - allowed):
        out.append(("ERROR", mirror.where, f"## {name} 在 SKILL.md 的做法里没有同名 ###"))
    return out


def check_skeleton(d) -> list:
    out = []
    heads = [(n, l[3:].strip()) for n, l in d.prose if l.startswith("## ")]
    if "范围" not in [h for _, h in heads]:
        return out
    if [h for _, h in heads] != SKELETON:
        out.append(("ERROR", d.where, f"## 须依次为 {' '.join(SKELETON)} 实为 {' '.join(h for _, h in heads)}"))
    skills = d.path.parent.parent
    section = ""
    for lineno, line in d.prose:
        if line.startswith("## "):
            section = line[3:].strip()
        elif section == "范围" and line.startswith("|"):
            for name in SKILL_REF_RE.findall(line):
                if not (skills / name).is_dir():
                    out.append(("ERROR", f"{d.where}:{lineno}", f"范围里的 skill 不存在 {name}"))
    return out + check_bullets(d, "参考")


def check(docs: list) -> list:
    out = []
    for d in docs:
        if d.path.name == "SKILL.md":
            fm = frontmatter(d.text)
            if fm is None:
                out.append(("ERROR", d.where, "缺少 frontmatter"))
            else:
                name = fm.get("name", "")
                if name != d.path.parent.name or not NAME_RE.match(name):
                    out.append(("ERROR", d.where, f"name 须与目录名一致且为小写连字符 实为 {name!r}"))
                desc = fm.get("description", "")
                if not desc or len(desc) > 1024:
                    out.append(("ERROR", d.where, f"description 长度 {len(desc)} 须在 1 到 1024"))
            n = d.text.count("\n")
            if n > MAX_SKILL_LINES:
                out.append(("ERROR", d.where, f"SKILL.md {n} 行 超过 {MAX_SKILL_LINES} 行 拆到 references/"))
            out += check_skeleton(d)
            if is_migrated(d.path.parent):
                out += check_csharp_mirror(d, docs)
        elif d.path.parent.name == "references" and is_migrated(d.path.parent.parent):
            out += check_bullets(d)
            if d.path.name != "csharp.md":
                out += check_csharp_pairs(d)
        for lineno, line in d.prose:
            for word in BANNED:
                if word in line:
                    out.append(("ERROR", f"{d.where}:{lineno}", f"禁用措辞 {word}"))
            for target in LINK_RE.findall(line):
                if "://" not in target and not (d.path.parent / target).exists():
                    out.append(("ERROR", f"{d.where}:{lineno}", f"链接不存在 {target}"))
        for b in d.blocks:
            if b.lang in WRONG_LANG:
                out.append(("ERROR", b.where, f"代码块语言写 gdscript 或 csharp 实为 {b.lang}"))
    return out
