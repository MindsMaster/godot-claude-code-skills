---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 项目。data/enemies.json 里是几种敌人的 hp、speed 和贴图路径，enemy.gd 在运行时读它。策划想在编辑器里直接改敌人数值，还想直接拖贴图进去，不想再改 JSON 文本。帮我把数据改成这种方式，并让 enemy.gd 配合。策划还在用表格工具导出 data/enemies.json 给另一个服务用，JSON 不能删，也不能出现 .tres 和 JSON 两边各改一份的情况。直接改项目文件，不用运行。
