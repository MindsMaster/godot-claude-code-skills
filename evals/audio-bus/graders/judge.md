---
type: llm
criteria: 用 AudioServer 的 bus 布局实现 在 default_bus_layout.tres 或用 AudioServer.add_bus 建立 Music SFX Voice 总线 AudioStreamPlayer 的 bus 属性指向对应总线 滑条值经 AudioServer.set_bus_volume_linear 设置 或经 linear_to_db 转成 dB 再调用 set_bus_volume_db 总音量用 Master 总线 没有手写 volume_db 逐个播放器同步 没有把滑条值直接当 dB 传 没有自己写音量混合类 说话时压低音乐用 Music 总线上的 AudioEffectCompressor 并把 sidechain 设为 Voice 没有在脚本里逐帧或按信号手动调音乐音量 轨迹中间被省略的写入看不到时 以能看到的写入内容和最终回复对做法的描述为依据 看不到不等于违规
focus: trace
---
