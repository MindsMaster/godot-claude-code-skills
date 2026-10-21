---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 C# 项目。Enemy.cs 挂在带着色器材质的 Sprite2D 上，flash.gdshader 里有 flash 参数，0 是原色，1 是纯白。给 Enemy 加受击闪白：受伤时变白，0.1 秒内恢复。TakeDamage 里触发。直接改项目文件，不用运行。
