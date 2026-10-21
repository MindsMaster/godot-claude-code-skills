---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 项目。给 main.tscn 里的玩家加一个跟随相机：平滑跟随，不能拍到关卡外面，关卡范围是 x 0 到 3200、y 0 到 720。受伤时要能震屏。玩家掉坑后会在检查点复活，复活直接设置 global_position，复活瞬间镜头要立刻到位，不能从坑里飞过去。直接改项目文件，不用运行。
