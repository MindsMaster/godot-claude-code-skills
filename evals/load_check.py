"""在引擎里检查 claude plugin eval 留下的工程。

用法：python3 evals/load_check.py results/a.json [-o results/a-load.json]
eval 须带 --keep-temp 运行。每次运行的工程复制到临时目录后：
- 有 .csproj 的用 dotnet build 编译
- 其余先 --import 再跑主场景 60 帧 输出里有脚本或引擎错误即失败
- 用例目录下有 verify.gd 时在工程里执行 输出 VERIFY FAIL 即失败

结果写成 {用例: {arm: [{ok, errors}]}}，由 score.py 读入
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ERROR = re.compile(r"SCRIPT ERROR|Parse Error|^ERROR:|VERIFY FAIL", re.M)
# 退出时测试进程未释放资源 与工程无关
IGNORE = re.compile(r"resources still in use|RID allocations|ObjectDB instances")


def workspace(trace_path: str, prefix_map: list) -> Path:
    for src, dst in prefix_map:
        if trace_path.startswith(src):
            trace_path = dst + trace_path[len(src):]
    root = Path(trace_path).parent.parent
    for p in (root, root / "sealed"):
        try:
            os.chmod(p, 0o700)
        except OSError:
            pass
    return root / "sealed" / "home" / "cwd"


def run(cmd: list, cwd: Path, timeout: int, env: dict) -> str:
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.stdout + r.stderr
    except subprocess.TimeoutExpired as e:
        return f"ERROR: timeout {cmd[1:3]}\n{e.stdout or ''}"


def errors(text: str) -> list:
    return [line.strip() for line in text.splitlines() if ERROR.search(line) and not IGNORE.search(line)]


def check(src: Path, case: str, godot: str, dotnet: str) -> list:
    tmp = Path(tempfile.mkdtemp(prefix="evalload-"))
    proj = tmp / "p"
    shutil.copytree(src, proj, ignore=shutil.ignore_patterns(".godot", ".bin"))
    env = dict(os.environ)
    for k in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        env[k] = str(tmp / "xdg")
    out = []
    try:
        if list(proj.glob("*.csproj")):
            text = run([dotnet, "build", "-nologo", "-v", "q"], proj, 600, env)
            out += [line.strip() for line in text.splitlines() if re.search(r"\berror\b", line)]
        else:
            # 首次导入时 autoload 引用的素材还没导入会报加载失败 只算第二遍的错误
            run([godot, "--headless", "--path", str(proj), "--import"], proj, 300, env)
            out += errors(run([godot, "--headless", "--path", str(proj), "--import"], proj, 300, env))
            out += errors(run([godot, "--headless", "--path", str(proj), "--quit-after", "60"], proj, 120, env))
        verify = HERE / case / "verify.gd"
        if verify.exists():
            shutil.copy(verify, proj / "_verify.gd")
            out += errors(run([godot, "--headless", "--path", str(proj), "-s", "res://_verify.gd"], proj, 120, env))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return sorted(set(out))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("-o", "--out")
    ap.add_argument("--godot", default=os.environ.get("GODOT_BIN", "godot"))
    ap.add_argument("--dotnet", default=os.environ.get("DOTNET_BIN", "dotnet"))
    ap.add_argument("--prefix-map", nargs=2, action="append", default=[], metavar=("FROM", "TO"),
                    help="改写 tracePath 前缀 例如在 Windows 上读 WSL 的 /tmp")
    args = ap.parse_args()
    data = json.load(open(args.results, encoding="utf-8"))
    result = {}
    for case in data["cases"]:
        for arm, runs in case["arms"].items():
            for r in runs:
                entry = {"ok": False, "errors": ["没有工程"]}
                if r.get("tracePath"):
                    src = workspace(r["tracePath"], args.prefix_map)
                    if src.is_dir():
                        errs = check(src, case["name"], args.godot, args.dotnet)
                        entry = {"ok": not errs, "errors": errs}
                result.setdefault(case["name"], {}).setdefault(arm, []).append(entry)
                mark = "ok" if entry["ok"] else "FAIL " + " | ".join(entry["errors"])[:300]
                print(f"{case['name']} {arm}: {mark}", flush=True)
    out = args.out or re.sub(r"\.json$", "-load.json", args.results)
    json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"写入 {out}")


if __name__ == "__main__":
    sys.exit(main())
