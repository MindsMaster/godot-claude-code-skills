---
type: llm
criteria: default_bus_layout.tres 里有 Weapon MonsterAttack UI Ambience 总线 Weapon MonsterAttack UI 的 send 指向 SFX 并且在布局里的序号大于 SFX 序号更小时引擎会改发 Master 算失败 gun.tscn monster.tscn hud.tscn wind.tscn 的播放器分别走 Weapon MonsterAttack UI Ambience 原来没写 bus 的怪物出招和风声都指定了总线 设置里是总音量 音乐 音效 环境四个滑条 音效滑条控制 SFX 总线 怪物出招时 Weapon 和 Music 两条总线上各有一个 AudioEffectCompressor sidechain 为 MonsterAttack threshold 低于 0 dB threshold 不写或为 0 dB 时完全不压 算失败 Godot 压缩器的压低量约为 2.08 乘峰值超出 threshold 的 dB 数再乘 1 减 1/ratio 按素材峰值 -12 dBFS 估算 Weapon 或 Music 的压低量低于 2 dB 或超过 6 dB 算失败 没有改用脚本逐帧调总线音量 轨迹中间被省略的写入看不到时 以能看到的写入内容和最终回复对做法的描述为依据 看不到不等于违规
focus: trace
---
