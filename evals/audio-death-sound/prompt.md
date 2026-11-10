---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 2D 项目。敌人死的时候没有声音，给 `enemy.tscn` 加上死亡音效 `death.wav`，走 SFX 总线，声音要从敌人所在的位置发出，完整播完。敌人死了要像现在一样立刻消失，不能再被打到或碰到玩家。直接改项目文件，不用运行。
