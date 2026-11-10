---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 像素风 2D 项目。为了整数倍缩放，我把游戏画面放进了 `main.tscn` 的 SubViewport 里。放进去之后，敌人的吼叫声（`enemy.tscn` 里的 `Growl`）完全听不到了，音乐和 UI 音效是正常的；单独运行 `game.tscn` 时吼叫是有的。找出原因并修好，吼叫要保留随距离衰减和左右声像。直接改项目文件，不用运行。
