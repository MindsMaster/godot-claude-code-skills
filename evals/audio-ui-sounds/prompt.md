---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 项目。给游戏里所有按钮加上悬停音效 `hover.wav` 和点击音效 `click.wav`，走 UI 总线。现在有主菜单 `main_menu.tscn` 和暂停菜单 `pause_menu.tscn`，以后新做的界面、运行时生成的按钮也要自动有，不用每个按钮单独接。键盘和手柄移动焦点到按钮上时也要有悬停音。暂停菜单是在游戏暂停时用的。直接改项目文件，不用运行。
