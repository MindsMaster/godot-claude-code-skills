---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 2D 项目。子弹时间 `BulletTime.enter()` 把画面放慢了，但声音还是原速，很出戏。让子弹时间里所有声音都按同样的比例慢下来、音调变低，音乐也算，子弹时间期间才生成的敌人发出的声音也要一样；`BulletTime.exit()` 之后全部恢复正常。直接改项目文件，不用运行。
