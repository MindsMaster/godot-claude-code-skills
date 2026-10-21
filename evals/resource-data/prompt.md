---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 项目。data/enemies.json 里是几种敌人的 hp、speed 和贴图路径，enemy.gd 在运行时读它。策划想在编辑器里直接看到敌人数值，还想直接拖贴图进去，不想再改 JSON 文本。帮我把数据改成这种方式，并让 enemy.gd 配合。

数值仍然由策划的表格工具维护，它每周导出一次覆盖 data/enemies.json，这个流程不会变，也不会停用，导出的 JSON 以后只有 hp 和 speed 两项，贴图不归表格管，只在编辑器里拖。表格导出之后，编辑器里要能拿到新数值，而且已经拖进去的贴图不能丢。不能出现两边各改一份的情况。

data/waves.csv 是刷怪波次，同样由表格工具导出，wave_spawner.gd 运行时直接读它，这个不用改成别的方式。下周要打 Windows 包给测试，打出来的包里刷怪波次必须能读到。我没有配过导出，项目里还没有导出预设，你一并准备好。直接改项目文件，不用运行。
