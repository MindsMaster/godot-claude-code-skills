"""盲评 claude plugin eval 留下的工程，每次运行只调用一次模型。

用法：python3 evals/judge.py results/a.json [--model claude-sonnet-5-5] [--base-dir 目录]
eval 须带 --keep-temp。用例目录有 judge.md 才评，其中每个 `## 名字` 是一个评判项。
评审只看题目和相对原工程的 diff，看不到轨迹和是否安装插件。
--base-dir 下放预先生成的原工程 <目录>/<用例>，缺省时就地运行 scaffold.sh。
结果写成 <结果>-judge.json：{运行目录名: {case, arm, cost, lines, checks: {名字: {pass, why}}}}，由 score.py 读入。
"""
import argparse
import difflib
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from load_check import workspace

HERE = Path(__file__).resolve().parent
TEXT = {".gd", ".cs", ".gdshader", ".tscn", ".tres", ".godot", ".import", ".cfg", ".csproj", ".json", ".csv", ".md"}
CODE = {".gd", ".cs", ".gdshader"}
SKIP_DIRS = {".godot", ".git", ".eval-artifacts", ".bin"}
CLEAN = (
    "只判写法是否干净 结果对错由别的项检查 这里假定结果正确 不要求某个特定 API 题目要求的部分不算多余 "
    "有以下任一情况判失败 引擎已有现成的节点 属性 资源或效果器能直接实现 却用脚本自己实现一套 "
    "能在场景或资源里直接设好的 改成脚本在运行时设置 或每帧重复计算 "
    "加了题目没要求的功能或系统 如存档 设置持久化 通用管理器 "
    "留下没用到的代码 变量或调试输出 同一件事写了两套机制"
)
SYSTEM = "你是 Godot 4.7 代码评审。只依据给出的题目和 diff 判断，不猜测 diff 之外的内容。"


def strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S).strip()


def read_checks(case_dir: Path) -> dict:
    path = case_dir / "judge.md"
    if not path.exists():
        return {}
    parts = re.split(r"^## (\S+)\n", path.read_text(encoding="utf-8"), flags=re.M)
    checks = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}
    if "clean" in checks:
        checks["clean"] = f"{CLEAN} 本题还包括 {checks['clean']}"
    return checks


def text_files(root: Path) -> dict:
    out = {}
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if p.is_file() and p.suffix in TEXT and not SKIP_DIRS & set(rel.parts):
            out[rel.as_posix()] = p.read_text(encoding="utf-8", errors="replace")
    return out


def scaffold(case_dir: Path) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="evalbase-"))
    try:
        subprocess.run(["bash", str(case_dir / "scaffold.sh")], cwd=tmp, check=True, stdin=subprocess.DEVNULL)
        return text_files(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def make_diff(base: dict, new: dict) -> str:
    lines = []
    for rel in sorted(base.keys() | new.keys()):
        a, b = base.get(rel, ""), new.get(rel, "")
        if a != b:
            lines += difflib.unified_diff(a.splitlines(), b.splitlines(), f"a/{rel}", f"b/{rel}", lineterm="", n=3)
    return "\n".join(lines)


def code_lines(files: dict) -> int:
    n = 0
    for rel, text in files.items():
        if Path(rel).suffix in CODE:
            n += sum(1 for line in text.splitlines() if line.strip() and not re.match(r"\s*(#|//)", line))
    return n


def ask(prompt: str, model: str) -> tuple:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_EFFORT_LEVEL"}
    cmd = [*shlex.split(os.environ.get("CLAUDE_BIN", "claude")), "-p", "--model", model, "--effort", "high",
           "--output-format", "json", "--tools", "", "--setting-sources", "", "--strict-mcp-config",
           "--no-session-persistence", "--disable-slash-commands", "--system-prompt", SYSTEM]
    with tempfile.TemporaryDirectory(prefix="evaljudge-", ignore_cleanup_errors=True) as cwd:
        r = subprocess.run(cmd, cwd=cwd, env=env, input=prompt, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-500:] or r.stdout[-500:])
    outer = json.loads(r.stdout)
    return outer.get("result", ""), outer.get("total_cost_usd") or 0.0


def judge_run(task: str, checks: dict, diff: str, model: str) -> tuple:
    items = "\n".join(f"- {name}：{text}" for name, text in checks.items())
    prompt = (f"题目原文：\n{task}\n\n评判项：\n{items}\n\n相对原工程的 diff：\n```diff\n{diff}\n```\n\n"
              "逐项判定。只输出一个 JSON 对象，键是评判项名字，值是 "
              '{"pass": true 或 false, "why": "一句话依据，引用 diff 里的内容"}。')
    cost = 0.0
    for _ in range(2):
        text, c = ask(prompt, model)
        cost += c
        m = re.search(r"\{.*\}", text, re.S)
        try:
            data = json.loads(m.group()) if m else {}
        except json.JSONDecodeError:
            data = {}
        if set(checks) <= set(data):
            return {n: {"pass": bool(data[n]["pass"]), "why": str(data[n].get("why", ""))} for n in checks}, cost
    return {n: {"pass": False, "why": "评审输出无法解析"} for n in checks}, cost


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("-o", "--out")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("-j", type=int, default=4)
    ap.add_argument("--base-dir")
    ap.add_argument("--prefix-map", nargs=2, action="append", default=[], metavar=("FROM", "TO"))
    args = ap.parse_args()
    data = json.load(open(args.results, encoding="utf-8"))
    out_path = args.out or re.sub(r"\.json$", "-judge.json", args.results)
    base_cache = {}

    def one(case_name: str, task: str, checks: dict, arm: str, run: dict) -> tuple:
        key = run["tracePath"].split("/")[2]
        src = workspace(run["tracePath"], args.prefix_map)
        new = text_files(src)
        base = base_cache[case_name]
        diff = make_diff(base, new)
        verdict, cost = judge_run(task, checks, diff, args.model)
        return key, {"case": case_name, "arm": arm, "cost": cost,
                     "lines": code_lines(new) - code_lines(base), "checks": verdict}

    jobs = []
    for case in data["cases"]:
        case_dir = HERE / case["name"]
        checks = read_checks(case_dir)
        if not checks:
            continue
        if args.base_dir:
            base_cache[case["name"]] = text_files(Path(args.base_dir) / case["name"])
        else:
            base_cache[case["name"]] = scaffold(case_dir)
        task = strip_frontmatter((case_dir / "prompt.md").read_text(encoding="utf-8"))
        for arm, runs in case["arms"].items():
            for run in runs or []:
                if run.get("tracePath") and not run.get("error"):
                    jobs.append((case["name"], task, checks, arm, run))

    result = {}
    with ThreadPoolExecutor(args.j) as pool:
        for key, entry in pool.map(lambda j: one(*j), jobs):
            result[key] = entry
            bad = [n for n, v in entry["checks"].items() if not v["pass"]]
            print(f"{entry['case']} {entry['arm']}: {'ok' if not bad else 'FAIL ' + ','.join(bad)} ${entry['cost']:.3f}",
                  flush=True)
    json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"写入 {out_path} 评审 ${sum(e['cost'] for e in result.values()):.2f}")


if __name__ == "__main__":
    main()
