---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 C# 项目。Enemy.cs 挂在带着色器材质的 Sprite2D 上，flash.gdshader 里有 flash 参数，0 是原色，1 是纯白。给 Enemy 加受击闪白：受伤时变白，0.1 秒内恢复。TakeDamage 里触发。场景里会同时刷 200 个这种敌人，都共用 main.tscn 里这一份材质，不要给每个敌人单独复制材质。中毒时每帧都会调 TakeDamage，也要正常闪白。直接改项目文件，不用运行。
