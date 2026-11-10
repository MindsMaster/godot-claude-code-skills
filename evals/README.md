# 评测

用 `claude plugin eval` 比较装与不装本插件时 Claude Code 的结果。按 skill 分模块评，用例的 `tags` 写所属 skill。

只评约束类内容，即模型是否用好引擎。参考类的实践案例和可选方案不写用例，分类见根目录 `CLAUDE.md` 的定位一节。

## 三层

| 层 | 用例 | 量什么 |
| --- | --- | --- |
| 触发率 | `triggers/<模块>-*`，tag `<skill>-trigger` | 该加载时加载，不该加载时不加载 |
| 端到端 | `<用例>/`，tag `<skill>` | 结果对不对，写法干不干净 |
| 留出 | 触发率用例 tag 含 `holdout`，端到端用例 tag 含 `<skill>-holdout` | 改 description 和正文时不看，防止只对已有用例有效 |

## 判分

一次运行通过要同时满足：

- eval 自带的 regex 等免费评分器全过，`skill` 只作加载指示，不计分
- `load_check.py`：Godot 加载工程、跑 60 帧不报错，C# 工程能编译，用例目录有 `verify.gd` 时它不报 `VERIFY FAIL`
- `judge.py`：评审模型只看题目和相对原工程的 diff，看不到轨迹，也不知道装没装插件，按用例 `judge.md` 的各项判定，`clean` 项附加通用的写法干净要求

新增留出用例时先跑不装插件的一组，确认有缺口再改 skill。

能机械判断的放进 `verify.gd`，如总线顺序、压低量、`area_mask`，不交给评审模型。写 `verify.gd` 时用手写的正确解和踩坑解各跑一遍，确认前者通过、后者报错。

## 运行

`CLAUDE_CODE_EFFORT_LEVEL` 在外层 shell 设置，会传给被测进程。用例里的 `execution.env` 只允许 `EVAL_*`。

```
evals/run_module.sh godot-audio claude-haiku-5-5 3
```

改了 skill 后只需重跑装插件的一组：

```
CLAUDE_CODE_EFFORT_LEVEL=high claude plugin eval . --scaffold --trust-plugin \
  --allow-tools Edit Write Bash --tag godot-audio --ablation none \
  --model claude-haiku-5-5 --runs 3 --threshold 0 --no-publish --keep-temp \
  --json evals/results/audio-haiku-v1.json
python3 evals/load_check.py evals/results/audio-haiku-v1.json
python3 evals/judge.py evals/results/audio-haiku-v1.json
python3 evals/score.py evals/results/audio-haiku-v1.json evals/results/audio-haiku-v0.json \
  --drop evals/results/audio-haiku-v0.json:with
```

触发率：

```
CLAUDE_CODE_EFFORT_LEVEL=high claude plugin eval . --scaffold --trust-plugin \
  --allow-tools Edit Write --tag godot-audio-trigger --ablation none \
  --model claude-haiku-5-5 --threshold 0 --no-publish --keep-temp \
  --json evals/results/trig-audio.json
python3 evals/trigger_rate.py evals/results/trig-audio.json
```

- `--keep-temp` 留下的目录是封住的，先 `chmod 700 /tmp/claude-eval-X /tmp/claude-eval-X/sealed`
- 授予 Bash 需要 `bubblewrap` 与 `socat`
- PATH 含很慢的挂载目录时沙箱报超时，如 WSL 的 `/mnt/c`，先精简 PATH
- 先用 Haiku 迭代，费用约为 Opus 的二十分之一，Haiku 足够好再跑 Sonnet 与 Opus
