#!/usr/bin/env bash
# 用法 evals/run_module.sh <skill> <模型> [每用例次数]
# 例如 evals/run_module.sh godot-audio claude-haiku-5-5 1
# EVAL_EFFORT 默认 high  EVAL_BUDGET 是本轮费用上限 默认 10 美元
set -euo pipefail
cd "$(dirname "$0")/.."
module=$1
model=$2
runs=${3:-1}
effort=${EVAL_EFFORT:-high}
out=evals/results/${module#godot-}-${model#claude-}-$effort.json
mkdir -p evals/results

CLAUDE_CODE_EFFORT_LEVEL=$effort claude plugin eval . --scaffold --trust-plugin \
	--allow-tools Edit Write Bash --tag "$module" --model "$model" --judge-model claude-sonnet-5-5 \
	--runs "$runs" -j "${EVAL_JOBS:-4}" --threshold 0 --no-publish --keep-temp \
	--max-cost-usd "${EVAL_BUDGET:-10}" --json "$out"
python3 evals/load_check.py "$out"
python3 evals/judge.py "$out"
python3 evals/score.py "$out"
