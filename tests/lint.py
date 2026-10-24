import re

from markdown import frontmatter

BANNED = ["显著", "大幅", "彻底", "真正", "其实", "确实", "正是", "恰好", "值得注意的是", "换句话说", "顺带", "顺手", "——"]
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
MAX_SKILL_LINES = 300
WRONG_LANG = {"gd", "py", "python", "c#", "cs"}


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
