---
runs: 1
max_turns: 25
allowed_tools: [Read, Glob, Grep, Edit, Write, Skill]
---

这是一个 Godot 4.7 项目。玩家的脚步声太机械：现在只放 `footstep_1.wav`，目录里有 4 个脚步素材，要随机放，不能连续两步放同一个，每步的音高和音量都有点变化。机枪连发时新的一发把上一发的尾音切断了，要让尾音能叠起来。脚步和枪声都走 SFX 总线。直接改项目文件，不用运行。
