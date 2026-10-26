---
runs: 1
max_turns: 30
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 俯视角射击项目。现在枪声、怪物出招、UI 点击都在一条 SFX 总线上，一起响的时候混成一团，策划没法单独调。要分开：武器开火、怪物出招、UI 各一条总线，名字用 Weapon、MonsterAttack、UI，风声这类环境音放 Ambience。策划要能单独调每一类的音量，但玩家设置里只要总音量、音乐、音效、环境四个滑条。怪物出招的时候，用 Godot 自带的压缩器侧链把枪声压低约 4 dB、音乐压低约 3 dB，出招结束后慢慢恢复。怪物出招素材的峰值约 -12 dBFS。直接改项目文件，不用运行。
