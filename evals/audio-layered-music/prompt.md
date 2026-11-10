---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 项目。`explore.wav` 和 `combat.wav` 是同一首曲子的两条分轨，长度相同，必须严格同拍地一起循环播放。默认只听到探索轨。调 `music.gd` 的 `enter_combat()` 时战斗轨 1 秒内淡入，探索轨继续响；调 `exit_combat()` 时战斗轨 1 秒内淡出。音乐走 Music 总线，游戏开始就响。直接改项目文件，不用运行。
