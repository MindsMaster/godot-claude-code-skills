---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 3D 项目。`main.tscn` 里的 `CaveZone` 是山洞的范围。在山洞里发出的声音要带明显的混响，山洞外发出的声音保持干声。敌人吼叫和火把声都来自 `enemy.tscn`、`torch.tscn` 里的 3D 播放器，以后关卡还会放更多敌人和火把，它们也可能走进走出山洞。直接改项目文件，不用运行。
