"""汇总 claude plugin eval --json 的结果。

用法：python3 evals/score.py results/a.json [results/b.json ...] [--ignore 名字,名字]
多个文件的同名用例合并运行次数。

通过：除 with-only 指示项外的评分器全部通过
      且同目录有 <结果>-load.json 时 该次运行在引擎里检查通过 见 load_check.py
带 error 的运行没有产出 不计入 单独列出
--ignore 跳过之后删掉的评分器
--exclude 文件:用例 丢弃某个文件里某个用例的运行 用于评分器改动后重跑
--extra {运行目录名: {评分器: 是否通过}} 对已有运行补评新评分器 或写入核对后的结果 同名评分器被替换
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+")
    ap.add_argument("--ignore", default="")
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--extra")
    args = ap.parse_args()
    ignore = {n for n in args.ignore.split(",") if n}

    extra = json.load(open(args.extra, encoding="utf-8")) if args.extra else {}

    def outcome(g: dict) -> bool:
        return not g.get("withOnly") and g["name"] not in ignore and not g["name"].startswith("b-")

    runs = defaultdict(list)
    skipped = []
    for path in args.results:
        data = json.load(open(path, encoding="utf-8"))
        load_path = Path(re.sub(r"\.json$", "-load.json", path))
        load = json.load(open(load_path, encoding="utf-8")) if load_path.exists() else {}
        print(f"<!-- {path} claude {data.get('claudeVersion')} {data.get('startedAt')} "
              f"${data.get('costUsd') or 0:.2f} load_check={'yes' if load else 'no'} -->")
        for case in data["cases"]:
            if f"{path}:{case['name']}" in args.exclude:
                continue
            for arm, arm_runs in case["arms"].items():
                for i, r in enumerate(arm_runs):
                    if r.get("error"):
                        skipped.append((case["name"], arm, path, r["error"]))
                        continue
                    lc = load.get(case["name"], {}).get(arm, [])
                    key = (r.get("tracePath") or "").split("/")[2:3]
                    add = extra.get(key[0], {}) if key else {}
                    if add:
                        kept = [g for g in r["graders"] if g["name"] not in add]
                        r = dict(r, graders=kept + [
                            {"name": n, "passed": v, "explanation": "补评或核对"} for n, v in add.items()])
                    runs[(case["name"], arm)].append((r, lc[i] if i < len(lc) else None))

    print("| 用例 | 安装 | 未安装 | 安装时加载 skill |")
    print("| --- | --- | --- | --- |")
    totals = {"with": [0, 0], "without": [0, 0]}
    failures = []
    for name in sorted({c for c, _ in runs}):
        cells = {}
        for arm in ("with", "without"):
            rs = runs.get((name, arm), [])
            ok = 0
            for i, (r, lc) in enumerate(rs):
                bad = [g for g in r["graders"] if outcome(g) and not g["passed"]]
                load_bad = lc is not None and not lc["ok"]
                if not bad and not load_bad:
                    ok += 1
                else:
                    failures.append((name, arm, i, bad, lc["errors"] if load_bad else []))
            cells[arm] = (ok, len(rs))
            totals[arm][0] += ok
            totals[arm][1] += len(rs)
        fired = sum(1 for r, _ in runs.get((name, "with"), [])
                    if any(g.get("withOnly") and g["passed"] for g in r["graders"]))
        w, wo = cells["with"], cells["without"]
        print(f"| {name} | {w[0]}/{w[1]} | {wo[0]}/{wo[1]} | {fired}/{w[1]} |")
    t = lambda arm: f"{totals[arm][0]}/{totals[arm][1]}"
    print(f"| 合计 | {t('with')} | {t('without')} | |")
    print()
    for name, arm, i, bad, load_errors in failures:
        print(f"- {name} {arm} #{i + 1}")
        for g in bad:
            print(f"  - {g['name']}: {(g.get('explanation') or '').strip()[:300]}")
        for e in load_errors[:3]:
            print(f"  - load_check: {e[:300]}")
    for name, arm, path, err in skipped:
        print(f"- 未计入 {name} {arm} {path}: {err[:200]}")


if __name__ == "__main__":
    main()
