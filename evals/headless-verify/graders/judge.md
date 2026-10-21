---
type: llm
criteria: agent 修掉了 player.gd 里调用不存在方法的错误 limit_speed_to 改成 Vector2 实际存在的方法如 limit_length 或等价写法 修改后用 godot --headless 带 --import 或 --check-only 或 --quit 实际运行验证 并看到没有 SCRIPT ERROR 或 Parse Error 最终回复如实汇报验证命令和结果 没有只靠阅读代码就声称已验证
focus: trace
---
