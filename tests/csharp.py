import re
import subprocess
import tempfile
from pathlib import Path

PROJECT = """<Project Sdk="Godot.NET.Sdk/{version}">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>disable</Nullable>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <NoWarn>CS0105;CS0168;CS0169;CS0219;CS0414;CS0649;CS8019</NoWarn>
  </PropertyGroup>
</Project>
"""

EDITORCONFIG = """root = true

[*.cs]
csharp_prefer_braces = true:error
dotnet_diagnostic.IDE0011.severity = error
csharp_preserve_single_line_statements = false
"""

USINGS = """global using Godot;
global using System;
global using System.Collections.Generic;
global using System.Linq;
global using System.Threading.Tasks;
"""

TYPE_DECL = re.compile(r"^\s*(public|internal|file)?\s*(static\s+|sealed\s+|abstract\s+|partial\s+)*(class|struct|record|interface|enum)\s", re.M)
ERROR_LINE = re.compile(r"(S\d+\.cs)\((\d+),\d+\): error (\w+): (.*?)(?: \[|$)")


def wrap(b, n: int) -> str:
    # 每个片段单独命名空间 避免类名互撞
    ns = f"Snippets.S{n}"
    if re.search(r"^\s*namespace\s", b.code, re.M):
        return b.code
    if TYPE_DECL.search(b.code):
        lines = b.code.split("\n")
        k = 0
        while k < len(lines) and (lines[k].startswith("using ") or not lines[k].strip()):
            k += 1
        return "\n".join(lines[:k] + [f"namespace {ns};", ""] + lines[k:])
    body = "\n".join("    " + line if line.strip() else line for line in b.code.split("\n"))
    return f"namespace {ns};\n\npublic partial class Fragment : {b.tags.get('extends', 'Node')}\n{{\n{body}\n}}\n"


def check(docs: list, dotnet: str, version: str) -> list:
    blocks = [b for d in docs for b in d.blocks if b.lang == "csharp" and "skip" not in b.tags]
    if not blocks:
        return []
    out = []
    with tempfile.TemporaryDirectory(prefix="cssnip") as tmp:
        proj = Path(tmp)
        (proj / "Snippets.csproj").write_text(PROJECT.format(version=version))
        (proj / ".editorconfig").write_text(EDITORCONFIG)
        (proj / "GlobalUsings.cs").write_text(USINGS)
        files = {}
        for n, b in enumerate(blocks):
            (proj / f"S{n}.cs").write_text(wrap(b, n))
            files[f"S{n}.cs"] = b
        res = subprocess.run(
            [dotnet, "build", "-nologo", "-v", "q", "-clp:NoSummary"],
            cwd=proj,
            capture_output=True,
            text=True,
            timeout=600,
        )
        log = res.stdout + res.stderr
        seen = set()
        for m in ERROR_LINE.finditer(log):
            if m.group(1) in files and m.group(0) not in seen:
                seen.add(m.group(0))
                out.append(("ERROR", files[m.group(1)].where, f"csharp {m.group(3)} {m.group(4)} 生成文件第 {m.group(2)} 行"))
        if res.returncode != 0 and not seen:
            out.append(("ERROR", "csharp", "构建失败\n" + log[-2000:]))
    print(f"csharp 片段 {len(blocks)} 个")
    return out
