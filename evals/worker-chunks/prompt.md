---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 项目，`flock.gd` 每个物理帧用 `WorkerThreadPool` 并行算 4000 个鸟群单位的转向。我们 8 核的机器上 Profiler 显示 `_physics_process` 很高，系统监视器里只有两个核忙。单位数量、每帧都算、计算结果都不能变。帮我找原因改好，直接改项目文件，不用运行。
