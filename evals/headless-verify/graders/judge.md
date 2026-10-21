---
type: llm
criteria: agent 修掉了 player.gd 里调用不存在方法的错误 limit_speed_to 改成 Vector2 实际存在的方法如 limit_length 或等价写法 验证时在检查脚本之前跑过 godot --headless --import 或者看到 Could not find type Stats 后补跑 --import 再复查 没有为消除该报错删掉 stats 的 Stats 类型标注 没有改成 preload 或 load 也没有改动 stats.gd 修改后实际运行 godot 验证 输出里没有 SCRIPT ERROR 或 Parse Error 最终回复如实汇报验证命令和结果
focus: trace
---
