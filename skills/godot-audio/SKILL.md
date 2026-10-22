---
name: godot-audio
description: Godot 4 音频，Audio bus 布局 default_bus_layout Music SFX Voice 总线，设置菜单音量 AudioServer.set_bus_volume_db linear_to_db，AudioStreamPlayer bus 属性，AudioStreamRandomizer 随机音效，max_polyphony 与 AudioStreamPolyphonic 代替播放器池，AudioStreamInteractive Playlist Synchronized 动态音乐，导入设置里设循环，2D 3D 空间音频，AudioEffectHardLimiter。在写音效 音乐 音量设置 脚步声 受击音 战斗音乐切换 时用。audio bus volume music sfx randomizer polyphony.
---

# Godot 音频

先建总线布局，播放器用 `bus` 属性选总线，音量只在总线上调。不管动画里的音频轨道，见 `godot-animation`。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 音乐 音效 语音分开调音量 | Audio bus 布局加 `AudioServer.set_bus_volume_db` | 每个播放器写常量 `volume_db` |
| 同一音效不重复随机选 | AudioStreamRandomizer 的 `PLAYBACK_RANDOM_NO_REPEATS`，已是默认 `playback_mode` | 手写随机下标加上次记录 |
| 音高音量随机 | AudioStreamRandomizer 的 `random_pitch` `random_volume_offset_db` | `pitch_scale = randf_range()` |
| 同一音效叠播 | `max_polyphony` | 复制多个 AudioStreamPlayer |
| 大量不同的一次性音效 | AudioStreamPolyphonic | 自建 16 个播放器的池 |
| 战斗与探索音乐切换 分层配器 曲目列表 | AudioStreamInteractive Synchronized Playlist | 多个播放器手动淡入淡出和对时间 |
| 限制爆音 | Master 上的 AudioEffectHardLimiter | 逐个调低音量 |
| 说话时压低音乐 | Music 总线加 AudioEffectCompressor，`sidechain` 设为 Voice | 脚本里逐帧调音乐音量 |
| 循环 | 导入设置里的循环选项 | 运行时改共享 stream 的 `loop` |

## 总线布局

编辑器底部 Audio 面板建 Music SFX Voice，发送到 Master，保存为 `default_bus_layout.tres`，即项目设置 `audio/buses/default_bus_layout` 的默认路径 `res://default_bus_layout.tres`：

```ini
[gd_resource type="AudioBusLayout" format=3]

[sub_resource type="AudioEffectHardLimiter" id="AudioEffectHardLimiter_1"]
ceiling_db = -1.0

[resource]
bus/0/effect/0/effect = SubResource("AudioEffectHardLimiter_1")
bus/0/effect/0/enabled = true
bus/1/name = &"Music"
bus/1/volume_db = 0.0
bus/1/send = &"Master"
bus/2/name = &"SFX"
bus/2/volume_db = 0.0
bus/2/send = &"Master"
```

- 播放器的 `bus` 属性填总线名。总线不存在时回退到 Master，拼错不报错
- 限幅放 Master 上，用 AudioEffectHardLimiter，AudioEffectLimiter 已弃用
- Area2D 与 Area3D 的 `audio_bus_override` 加 `audio_bus_name` 给区域内的声音换总线，做洞穴混响。只对 AudioStreamPlayer2D 与 3D 生效，播放器的 `area_mask` 默认 0，要勾上区域的 collision layer

## 音量设置

```gdscript
extends HSlider

@export var bus_name: StringName = &"Music"

func _ready() -> void:
	min_value = 0.0
	max_value = 1.0
	step = 0.01
	value = AudioServer.get_bus_volume_linear(AudioServer.get_bus_index(bus_name))
	value_changed.connect(_on_value_changed)

func _on_value_changed(linear: float) -> void:
	var bus := AudioServer.get_bus_index(bus_name)
	AudioServer.set_bus_volume_linear(bus, linear)
	AudioServer.set_bus_mute(bus, linear <= 0.0)
```

- 滑块用线性 0 到 1，设置时转 dB，直接当 `volume_db` 听感不均匀
- `AudioServer.set_bus_volume_linear` 与 `get_bus_volume_linear` 4.4+，内部做 `linear_to_db`。4.3 及以前用 `set_bus_volume_db(bus, linear_to_db(linear))`
- 0 对应负无穷 dB，同时 `set_bus_mute`

## 随机音效

编辑器里新建 AudioStreamRandomizer 拖入音效，或代码构造：

```gdscript
extends AudioStreamPlayer

@export var hits: Array[AudioStream] = []

func _ready() -> void:
	var random := AudioStreamRandomizer.new()
	random.playback_mode = AudioStreamRandomizer.PLAYBACK_RANDOM_NO_REPEATS
	random.random_pitch = 1.1
	random.random_volume_offset_db = 2.0
	for hit in hits:
		random.add_stream(-1, hit)
	stream = random
```

`random_pitch` 是倍率，1.1 表示在 1/1.1 到 1.1 之间随机，设置时同步改 `random_pitch_semitones`。`random_volume_offset_db` 2.0 表示正负 2 dB。按半音设用 `random_pitch_semitones` 4.6+。`add_stream` 第一个参数小于 0 追加到末尾，第三个参数是权重，默认 1.0。

## 同时多声

| 情况 | 做法 |
|---|---|
| 同一音效连续触发，如机枪 | `max_polyphony` 设 4 到 8，再次 `play()` 叠加，超出时切掉最老的。默认 1，新声音会切掉旧声音 |
| 很多不同的一次性音效 | 一个播放器挂 AudioStreamPolyphonic，用 `play_stream()` |
| 每个实体自己的位置声 | 每个实体一个 AudioStreamPlayer2D 或 3D |

```gdscript
extends AudioStreamPlayer

var _poly: AudioStreamPlaybackPolyphonic

func _ready() -> void:
	var poly := AudioStreamPolyphonic.new()
	poly.polyphony = 16
	bus = &"SFX"
	stream = poly
	play()
	_poly = get_stream_playback()

func play_sfx(sound: AudioStream, gain_db: float = 0.0) -> int:
	return _poly.play_stream(sound, 0.0, gain_db)
```

- 声音走播放器的 `bus`，4.7.2 实测 Stream 播放类型下 `play_stream` 的 `bus` 参数无效。要分总线就按总线各挂一个播放器
- 返回值是播放 ID，给 `stop_stream` `set_stream_volume` `is_stream_playing` 用。并发数满了返回 `AudioStreamPlaybackPolyphonic.INVALID_ID`

## 动态音乐 4.3+

| 资源 | 用途 |
|---|---|
| AudioStreamInteractive | 多个片段加转场表，按状态切片段，在拍点或小节处淡入淡出 |
| AudioStreamPlaylist | 按顺序或乱序播放子流，可淡入淡出与循环 |
| AudioStreamSynchronized | 多条子流同时开始，分层配器，用音量加减层 |

切换片段用 `set(&"parameters/switch_to_clip", &"Combat")`。转场表、拍点对齐和分层音量见 `references/dynamic-music.md`。

## 循环

- 在导入设置里设。WAV 用 `edit/loop_mode` `edit/loop_begin` `edit/loop_end`，单位是采样数，`loop_end` 为 -1 取文件末尾，`loop_mode` 默认 Detect From WAV 跟随文件元数据。Ogg Vorbis 与 MP3 用 `loop` 与 `loop_offset`，单位是秒。改完点 Reimport
- 不要运行时对共享的 stream 写 `loop = true`，所有引用同一资源的播放器一起变，缓存也被改。需要不同循环行为就导入两份，或 `duplicate()` 后再改
- 循环音频的播放器不发 `finished`

## 空间音频

- 2D 与 3D 播放器都有 `max_distance` `panning_strength` `area_mask`。衰减 2D 用 `attenuation` 指数，默认 1.0，3D 用 `attenuation_model` 加 `unit_size`。多普勒只有 3D 的 `doppler_tracking`
- 3D 听者是当前 Camera3D，2D 没有 AudioListener2D 时以视口中心为听点。要把听者放在别处，用 AudioListener2D 或 AudioListener3D 的 `make_current()`
- 全局声像强度见项目设置 `audio/general/2d_panning_strength` 与 `audio/general/3d_panning_strength`

## 陷阱

- 每个播放器写 `volume_db = -6` 当音量设置，玩家无法分开调音乐与音效，改用总线
- 网页导出默认按 sample 方式播放，AudioEffect 不生效。需要总线效果的播放器把 `playback_type` 设为 `AudioServer.PLAYBACK_TYPE_STREAM`，或改 `audio/general/default_playback_type.web`

## 参考

- [音频总线](https://docs.godotengine.org/en/stable/tutorials/audio/audio_buses.html)
- `references/dynamic-music.md`
