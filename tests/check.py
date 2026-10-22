import argparse
import os
import shutil
import sys

import api
import csharp
import gdscript
import lint
import run
from markdown import ROOT, parse_doc


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

    paths = sorted((ROOT / "skills").rglob("*.md"))
    if args.only:
        paths = [p for p in paths if args.only in str(p)]
    docs = [parse_doc(p) for p in paths]

    findings = []
    if "lint" in args.steps:
        findings += lint.check(docs)
    if "api" in args.steps:
        findings += api.check(docs)
    if "gd" in args.steps:
        if shutil.which(args.godot):
            findings += gdscript.check(docs, args.godot, args.jobs)
        else:
            findings.append(("ERROR", "gd", f"找不到 Godot {args.godot} 设 GODOT_BIN"))
    if "run" in args.steps:
        if shutil.which(args.godot):
            findings += run.check(docs, args.godot, args.jobs)
        else:
            findings.append(("ERROR", "run", f"找不到 Godot {args.godot} 设 GODOT_BIN"))
    if "cs" in args.steps:
        if shutil.which(args.dotnet):
            findings += csharp.check(docs, args.dotnet, args.sdk_version)
        else:
            findings.append(("ERROR", "cs", f"找不到 dotnet {args.dotnet} 设 DOTNET_BIN"))

    findings.sort(key=lambda f: f[0] == "ERROR")
    for level, where, msg in findings:
        print(f"{level:5} {where}: {msg}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    print(f"{len(docs)} 个文件 {errors} 错误 {len(findings) - errors} 警告")
    return 1 if errors or (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
