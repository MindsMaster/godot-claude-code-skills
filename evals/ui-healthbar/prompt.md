---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 项目，player.gd 里已经有 health_changed 和 score_changed 两个信号。给游戏加 HUD：左上角显示血条，右上角显示分数。要能适配 16:9、4:3、竖屏等不同屏幕比例，窗口缩放时布局不乱。整个游戏里所有文字字体和字号风格要统一，以后换字体只改一处。HUD 做成单独的场景放进 main.tscn，通过导出变量拿到玩家节点。直接改项目文件，不用运行。
