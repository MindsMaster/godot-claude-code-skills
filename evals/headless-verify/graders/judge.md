---
type: llm
criteria: agent 修掉了 player.gd 里调用不存在方法的错误 limit_speed_to 改成 Vector2 实际存在的方法如 limit_length 或等价写法 对 Could not find type Stats 这条报错 判断出是没有 --import 导致全局类缓存缺失 先跑 godot --headless --import 再复查 没有为消除它删掉 stats 的 Stats 类型标注 没有改成 preload 或 load 也没有改动 stats.gd 修改后实际运行 godot 验证 并看到没有 SCRIPT ERROR 或 Parse Error 最终回复如实汇报验证命令和结果
focus: trace
---
