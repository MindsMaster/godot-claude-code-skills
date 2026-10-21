---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 的 2D 平台跳跃项目。给 main.tscn 做一个可以在编辑器里直接绘制的关卡地图，角色要能站在上面，不会穿过去。地图素材用项目里的 tiles.png，它是一张 16x16 像素的单块图。关卡里要预先摆好一段地面和两处浮台，玩家出生在地面上方一点，打开工程直接运行就能站在地面上。直接改项目文件，不用运行。
