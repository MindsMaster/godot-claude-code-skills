import argparse
import concurrent.futures
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
DATA = Path(__file__).resolve().parent / "data"

BANNED = ["显著", "大幅", "彻底", "真正", "其实", "确实", "正是", "恰好", "值得注意的是", "换句话说", "顺带", "顺手", "——"]
FENCE = re.compile(r"^(\s*)```([\w#+-]*)\s*$")
CHECK_TAG = re.compile(r"<!--\s*check:\s*(.+?)\s*-->")
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


@dataclass
class Block:
    path: Path
    line: int
    lang: str
    code: str
    tags: dict = field(default_factory=dict)


@dataclass
class Doc:
    path: Path
    text: str
    prose: list
    blocks: list


@dataclass
class Report:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def err(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def parse_tags(raw: str) -> dict:
    tags = {}
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        key, _, value = part.partition(" ")
        tags[key] = value.strip()
    return tags


def parse_doc(path: Path) -> Doc:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    prose = []
    blocks = []
    i = 0
    pending = {}
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m:
            start = i
            lang = m.group(2).lower()
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i][len(m.group(1)):] if lines[i].startswith(m.group(1)) else lines[i])
                i += 1
            blocks.append(Block(path, start + 1, lang, "\n".join(body) + "\n", pending))
            pending = {}
            i += 1
            continue
        tag = CHECK_TAG.search(lines[i])
        if tag:
            pending = parse_tags(tag.group(1))
        elif lines[i].strip():
            pending = {}
        prose.append((i + 1, lines[i]))
        i += 1
    return Doc(path, text, prose, blocks)


def frontmatter(text: str):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    fields = {}
    for line in text[4:end].split("\n"):
        key, sep, value = line.partition(":")
        if sep and not line.startswith(" "):
            fields[key.strip()] = value.strip().strip('"')
    return fields


def lint(docs: list, rep: Report) -> None:
    for d in docs:
        where = rel(d.path)
        if d.path.name == "SKILL.md":
            fm = frontmatter(d.text)
            if fm is None:
                rep.err(where, "缺少 frontmatter")
            else:
                name = fm.get("name", "")
                if name != d.path.parent.name or not NAME_RE.match(name):
                    rep.err(where, f"name 须与目录名一致且为小写连字符 实为 {name!r}")
                desc = fm.get("description", "")
                if not desc or len(desc) > 1024:
                    rep.err(where, f"description 长度 {len(desc)} 须在 1 到 1024")
            n = d.text.count("\n")
            if n > 500:
                rep.err(where, f"SKILL.md {n} 行 超过 500 行 拆到 references/")
        for lineno, line in d.prose:
            for word in BANNED:
                if word in line:
                    rep.err(f"{where}:{lineno}", f"禁用措辞 {word}")
            for target in LINK_RE.findall(line):
                if "://" in target:
                    continue
                if not (d.path.parent / target).exists():
                    rep.err(f"{where}:{lineno}", f"链接不存在 {target}")
        for b in d.blocks:
            if b.lang in ("gd", "py", "python", "c#", "cs"):
                rep.err(f"{where}:{b.line}", f"代码块语言写 gdscript 或 csharp 实为 {b.lang}")


def snake(name: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    s = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", s)
    return s.lower()


class Api:
    def __init__(self) -> None:
        with gzip.open(DATA / "godot_api.json.gz", "rt", encoding="utf-8") as f:
            self.raw = json.load(f)
        self.classes = self.raw["classes"]
        self.builtins = self.raw["builtins"]
        self.deprecated = self.raw["deprecated"]
        self.version = self.raw["version"]
        allow = (DATA / "allow_names.txt").read_text(encoding="utf-8").split()
        self.allow = set(allow)
        self.settings = set(self.raw["project_settings"])
        self.setting_roots = {name.split("/")[0] for name in self.settings}

    def is_type(self, name: str) -> bool:
        return (
            name in self.classes
            or name in self.builtins
            or name in self.raw["global_enums"]
            or name in self.allow
        )

    def members(self, cls: str) -> set:
        out = set()
        if cls in self.builtins:
            b = self.builtins[cls]
            out.update(b["methods"], b["members"], b["constants"], b["enums"])
            for values in b["enums"].values():
                out.update(values)
            return out
        while cls in self.classes:
            c = self.classes[cls]
            out.update(c["methods"], c["properties"], c["signals"], c["constants"], c["enums"])
            for values in c["enums"].values():
                out.update(values)
            cls = c["inherits"]
        return out

    def has_member(self, cls: str, member: str) -> bool:
        names = self.members(cls)
        if member in names or snake(member) in names:
            return True
        upper = snake(member).upper()
        return upper in names


def api_check(docs: list, api: Api, rep: Report) -> None:
    camel = re.compile(r"^[A-Z][A-Za-z0-9]*[a-z][A-Za-z0-9]*$")
    setting = re.compile(r"^[a-z0-9_]+(/[a-z0-9_]+)+(\.[a-z0-9_]+)?$")
    member_ref = re.compile(r"^([A-Z][A-Za-z0-9]*)\.([A-Za-z_][A-Za-z0-9_]*)(?:\(.*\))?$")
    for d in docs:
        where = rel(d.path)
        text_versions = set(re.findall(r"4\.(\d+)\+", d.text))
        for lineno, line in d.prose:
            for token in INLINE_CODE.findall(line):
                token = token.strip()
                m = member_ref.match(token)
                if m:
                    cls, member = m.groups()
                    if (cls in api.classes or cls in api.builtins) and not api.has_member(cls, member):
                        rep.err(f"{where}:{lineno}", f"{cls} 没有成员 {member}")
                    continue
                if setting.match(token) and token.split("/")[0] in api.setting_roots:
                    if token.split(".")[0] not in api.settings and not any(n.startswith(token + "/") for n in api.settings):
                        rep.err(f"{where}:{lineno}", f"项目设置不存在 {token}")
                    continue
                if camel.match(token) and not api.is_type(token):
                    rep.warn(f"{where}:{lineno}", f"未知类型名 {token} 引擎没有 也不在 allow_names.txt")
        for b in d.blocks:
            if b.lang not in ("gdscript", "csharp"):
                continue
            for cls, members in api.deprecated.items():
                if "" in members and re.search(rf"\b{cls}\b", b.code) and "deprecated" not in b.tags:
                    rep.err(f"{where}:{b.line}", f"代码块用了已弃用的 {cls}")
        for name in set(re.findall(r"\b[A-Z][A-Za-z0-9]+\b", d.text)):
            c = api.classes.get(name)
            if c and c["since"] > "4.4" and c["since"].split(".")[1] not in text_versions:
                rep.warn(where, f"{name} 自 {c['since']} 起才有 正文未标 {c['since']}+")


def run(cmd: list, cwd: Path, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


GD_RUNNER = """extends SceneTree

func _init() -> void:
\tfor path in OS.get_cmdline_user_args():
\t\tvar s: GDScript = load(path)
\t\tif s == null or not s.can_instantiate():
\t\t\tprinterr("CHECK_FAIL ", path)
\tquit()
"""

GD_PROJECT = """config_version=5

[application]

config/name="snippets"

[debug]

gdscript/warnings/untyped_declaration=2
"""


def gd_check_doc(godot: str, blocks: list, work: Path) -> list:
    proj = work / blocks[0].path.stem
    proj.mkdir(parents=True)
    (proj / "project.godot").write_text(GD_PROJECT)
    (proj / "_runner.gd").write_text(GD_RUNNER)
    files = {}
    for n, b in enumerate(blocks):
        code = b.code
        ext = b.tags.get("extends")
        if ext and not re.search(r"^extends\b", code, re.M):
            code = f"extends {ext}\n\n{code}"
        name = f"s{n}_{b.line}.gd"
        (proj / name).write_text(code)
        files[name] = b
    run([godot, "--headless", "--path", str(proj), "--import"], proj)
    res = run([godot, "--headless", "--path", str(proj), "-s", "_runner.gd", "--", *[f"res://{f}" for f in files]], proj)
    out = (res.stdout + res.stderr).split("\n")
    problems = []
    for i, line in enumerate(out[:-1]):
        m = re.search(r"res://(s\d+_\d+\.gd):(\d+)", out[i + 1])
        if not m or m.group(1) not in files:
            continue
        b = files[m.group(1)]
        offset = int(m.group(2))
        if b.tags.get("extends") and not re.search(r"^extends\b", b.code, re.M):
            offset -= 2
        if "Parse Error" in line or "SCRIPT ERROR" in line:
            problems.append((b, f"{line.strip()} 代码块第 {offset} 行"))
        elif line.startswith("WARNING") and b.tags.get("warn") != "ok":
            problems.append((b, f"{line.strip()} 代码块第 {offset} 行"))
    failed = {line.split("res://")[1].strip() for line in out if line.startswith("CHECK_FAIL")}
    reported = {id(b) for b, _ in problems}
    for name in failed:
        if id(files[name]) not in reported:
            problems.append((files[name], "加载失败"))
    return problems


def gd_check(docs: list, rep: Report, godot: str, jobs: int) -> None:
    groups = []
    for d in docs:
        blocks = [b for b in d.blocks if b.lang == "gdscript" and "skip" not in b.tags]
        if blocks:
            groups.append(blocks)
    with tempfile.TemporaryDirectory(prefix="gdsnip") as tmp:
        work = Path(tmp)
        for i, g in enumerate(groups):
            (work / str(i)).mkdir()
        with concurrent.futures.ThreadPoolExecutor(jobs) as pool:
            futures = [pool.submit(gd_check_doc, godot, g, work / str(i)) for i, g in enumerate(groups)]
            for f in futures:
                for b, msg in f.result():
                    rep.err(f"{rel(b.path)}:{b.line}", f"gdscript {msg}")
    print(f"gdscript 片段 {sum(len(g) for g in groups)} 个")


CS_PROJECT = """<Project Sdk="Godot.NET.Sdk/{version}">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>disable</Nullable>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <NoWarn>CS0105;CS0168;CS0169;CS0219;CS0414;CS0649;CS8019</NoWarn>
  </PropertyGroup>
</Project>
"""

CS_EDITORCONFIG = """root = true

[*.cs]
csharp_prefer_braces = true:error
dotnet_diagnostic.IDE0011.severity = error
csharp_preserve_single_line_statements = false
"""

CS_USINGS = """global using Godot;
global using System;
global using System.Collections.Generic;
global using System.Linq;
global using System.Threading.Tasks;
"""

TYPE_DECL = re.compile(r"^\s*(public|internal|file)?\s*(static\s+|sealed\s+|abstract\s+|partial\s+)*(class|struct|record|interface|enum)\s", re.M)


def cs_wrap(b: Block, n: int) -> str:
    code = b.code
    ns = f"Snippets.S{n}"
    if re.search(r"^\s*namespace\s", code, re.M):
        return code
    if TYPE_DECL.search(code):
        lines = code.split("\n")
        k = 0
        while k < len(lines) and (lines[k].startswith("using ") or not lines[k].strip()):
            k += 1
        return "\n".join(lines[:k] + [f"namespace {ns};", ""] + lines[k:])
    ext = b.tags.get("extends", "Node")
    body = "\n".join("    " + line if line.strip() else line for line in code.split("\n"))
    return f"namespace {ns};\n\npublic partial class Fragment : {ext}\n{{\n{body}\n}}\n"


def cs_check(docs: list, rep: Report, dotnet: str, version: str) -> None:
    blocks = [b for d in docs for b in d.blocks if b.lang == "csharp" and "skip" not in b.tags]
    if not blocks:
        return
    with tempfile.TemporaryDirectory(prefix="cssnip") as tmp:
        proj = Path(tmp)
        (proj / "Snippets.csproj").write_text(CS_PROJECT.format(version=version))
        (proj / ".editorconfig").write_text(CS_EDITORCONFIG)
        (proj / "GlobalUsings.cs").write_text(CS_USINGS)
        files = {}
        for n, b in enumerate(blocks):
            name = f"S{n}.cs"
            (proj / name).write_text(cs_wrap(b, n))
            files[name] = b
        res = run([dotnet, "build", "-nologo", "-v", "q", "-clp:NoSummary"], proj)
        seen = set()
        for line in (res.stdout + res.stderr).split("\n"):
            m = re.search(r"(S\d+\.cs)\((\d+),\d+\): error (\w+): (.*?)(?: \[|$)", line)
            if m and m.group(1) in files and line not in seen:
                seen.add(line)
                b = files[m.group(1)]
                rep.err(f"{rel(b.path)}:{b.line}", f"csharp {m.group(3)} {m.group(4)} 生成文件第 {m.group(2)} 行")
        if res.returncode != 0 and not seen:
            rep.err("csharp", "构建失败\n" + (res.stdout + res.stderr)[-2000:])
    print(f"csharp 片段 {len(blocks)} 个")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("steps", nargs="*", default=["lint", "api", "gd", "cs"])
    ap.add_argument("--godot", default=os.environ.get("GODOT_BIN", "godot"))
    ap.add_argument("--dotnet", default=os.environ.get("DOTNET_BIN", "dotnet"))
    ap.add_argument("--sdk-version", default=os.environ.get("GODOT_SDK_VERSION", "4.7.2"))
    ap.add_argument("--only", help="只查路径含此子串的文件")
    ap.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--strict", action="store_true", help="警告也算失败")
    args = ap.parse_args()

    paths = sorted(SKILLS.rglob("*.md"))
    if args.only:
        paths = [p for p in paths if args.only in str(p)]
    docs = [parse_doc(p) for p in paths]
    rep = Report()
    if "lint" in args.steps:
        lint(docs, rep)
    if "api" in args.steps:
        api_check(docs, Api(), rep)
    if "gd" in args.steps:
        if shutil.which(args.godot) is None:
            rep.err("gd", f"找不到 Godot {args.godot} 设 GODOT_BIN")
        else:
            gd_check(docs, rep, args.godot, args.jobs)
    if "cs" in args.steps:
        if shutil.which(args.dotnet) is None:
            rep.err("cs", f"找不到 dotnet {args.dotnet} 设 DOTNET_BIN")
        else:
            cs_check(docs, rep, args.dotnet, args.sdk_version)

    for w in rep.warnings:
        print("WARN ", w)
    for e in rep.errors:
        print("ERROR", e)
    print(f"{len(docs)} 个文件 {len(rep.errors)} 错误 {len(rep.warnings)} 警告")
    failed = rep.errors or (args.strict and rep.warnings)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
