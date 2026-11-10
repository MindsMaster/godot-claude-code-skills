---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 2D 项目。按暂停（`PauseMenu.toggle()`）的时候现在所有声音都停了。想要的效果：暂停时音乐继续放，但要变闷，像隔着墙听；游戏里的音效照常暂停，恢复后从原处接着放；暂停菜单的按钮点击音要清楚，不能跟着变闷。恢复游戏后音乐回到原样。直接改项目文件，不用运行。
