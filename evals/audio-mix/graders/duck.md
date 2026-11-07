---
type: llm
criteria: 下面只有 default_bus_layout.tres 侧链总线上是否真有怪物出招的声音由别的评分项检查 这里假定有 Weapon 和 Music 两条总线上各有一个 AudioEffectCompressor sidechain 指向 MonsterAttack 或另一条专门放怪物出招声音的总线 侧链总线序号大于被压总线时 侧链读到的是乘过它自身音量和静音之后的信号 此时它静音或音量听不见等于不压 判失败 threshold 低于 0 dB 不写或为 0 dB 时完全不压 判失败 压低量约为 2.08 乘以 -12 减 threshold 的 dB 数再乘 1 减 1/ratio 侧链总线另设了音量时按它调整 Weapon 或 Music 的压低量低于 2 dB 或超过 6 dB 判失败 只按结果判 不因为没用某个特定 API 或写法判失败
focus: { source: file, path: default_bus_layout.tres }
---
