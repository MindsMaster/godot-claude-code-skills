---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 项目。现在每个场景里各有一个 `Music` 播放器，切场景时音乐会断掉重头放。改成：`level_1` 和 `level_2` 用的是同一首 `level.wav`，从一关切到下一关音乐不能断也不能重头；换到不同曲子的场景时，旧曲 1 秒淡出，新曲同时 1 秒淡入。每个场景用哪首曲子仍然在各自场景里指定，以后加新场景不用改别处。音乐走 Music 总线。直接改项目文件，不用运行。
