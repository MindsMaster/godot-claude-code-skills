"""汇总触发率用例 用法：python3 evals/trigger_rate.py results/trig.json
评分器名 loaded 表示应加载 not-loaded 表示不应加载 命中按轨迹里实际加载的 skill 计
第 2 3 个参数可改写 tracePath 前缀
"""
import json
import re
import sys


def loaded(trace: str) -> list:
    try:
        text = open(trace, encoding="utf-8").read()
    except OSError:
        return ["?"]
    return sorted(set(re.findall(r'"name":"Skill","input":\{"skill":"(?:[\w-]+:)?([\w-]+)"', text)))


def main() -> None:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    remap = sys.argv[2:4]
    target = re.sub(r"^trigger-(\w+)-.*", r"godot-\1", data["cases"][0]["name"])
    hit = {True: [0, 0], False: [0, 0]}
    print(f"<!-- {sys.argv[1]} ${data.get('costUsd') or 0:.2f} -->")
    print("| 用例 | 应加载 | 命中 | 实际加载 |")
    print("| --- | --- | --- | --- |")
    for case in data["cases"]:
        runs = [r for r in case["arms"]["with"] if not r.get("error")]
        should = any(g["name"] == "loaded" for g in runs[0]["graders"]) if runs else True
        seen = []
        for r in runs:
            path = r.get("tracePath") or ""
            if remap:
                path = path.replace(remap[0], remap[1])
            seen.append("+".join(loaded(path)) or "无")
        ok = sum((target in s.split("+")) == should for s in seen)
        hit[should][0] += ok
        hit[should][1] += len(runs)
        holdout = " 留出" if "holdout" in case.get("tags", []) else ""
        print(f"| {case['name'].removeprefix('trigger-')}{holdout} | {'是' if should else '否'} | {ok}/{len(runs)} | {' / '.join(seen)} |")
    print(f"\n应加载命中 {hit[True][0]}/{hit[True][1]}  不应加载命中 {hit[False][0]}/{hit[False][1]}")


if __name__ == "__main__":
    main()
