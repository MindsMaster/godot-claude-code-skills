---
name: godot-audio
description: 写音效 音乐 音量设置 脚步声 战斗音乐切换 节奏同步时用，音效在游戏里发闷 模糊 与原文件听感不一样时也用。Audio bus 布局 Music SFX Voice、滑条调音量 linear_to_db、说话时侧链压低音乐、AudioStreamRandomizer 随机音效、max_polyphony 代替播放器池、AudioStreamInteractive 动态音乐、2D 3D 空间音频、3D 距离滤波、WAV 导入压缩、多类音效同时响的混音 分类子总线 响度 LUFS 并发上限 怪物出招压低枪声与音乐。audio bus volume music sfx muffled import mix loudness ducking.
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
| 节奏游戏的歌曲时间 | `get_playback_position()` 加 `AudioServer.get_time_since_last_mix()` 减输出延迟 | 用 `_process` 的 delta 累加当歌曲时间 |
| 限制爆音 | Master 上的 AudioEffectHardLimiter | 逐个调低音量 |
| 说话时压低音乐 | Music 总线加 AudioEffectCompressor，`sidechain` 设为 Voice，`threshold` 调到触发声峰值以下，见混音 | 脚本里逐帧调音乐音量 |
| 多类音效同时响 分开调比例 | SFX 下按类别建子总线，见混音 | 所有音效挤在一条 SFX 总线 |
| 循环 | 导入设置里的循环选项 | 运行时改共享 stream 的 `loop` |
| 3D 音效在游戏里发闷 | 查 `attenuation_filter_cutoff_hz`，见空间音频 | 把 WAV 转成 Ogg 或提高采样率 |

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

## 混音

枪声、怪物出招、命中、UI 会同时响的游戏：

- 每个类别一条子总线，`send` 指向 SFX，策划在子总线上调比例。玩家只给总音量、音乐、音效、环境四个滑块，挂在 Master Music SFX Ambience 上
- 子总线在布局里排在 SFX 之后，发送只能指向序号更小的总线
- 素材进库先统一响度，短音效按最大瞬时响度 -19 LUFS-M，真峰值不超过 -1 dBTP。类别间的差值写在播放器或子总线的音量里，换素材不用重调
- 高射速武器每发比单发武器轻 2 到 4 dB，几发叠起来总响度会上去
- 同类声音限并发，枪 `max_polyphony` 4 到 8，命中反馈 4 左右
- Master 末尾放 AudioEffectHardLimiter

用压缩器侧链压低，参数要自己给：

<!-- check: extends Node -->
```gdscript
func _ready() -> void:
	var duck := AudioEffectCompressor.new()
	duck.sidechain = &"Voice"
	duck.threshold = -18.0
	duck.ratio = 1.5
	duck.release_ms = 400.0
	AudioServer.add_bus_effect(AudioServer.get_bus_index(&"Music"), duck)
```

- `threshold` 默认 0 dB，触发声峰值不到 0 dBFS 就完全不压
- 压低量约为 2.08 乘触发峰值超出 `threshold` 的 dB 数，再乘 1 减 1/`ratio`，是常见压缩器公式的两倍。4.7.2 实测触发峰值 -6 dBFS：-12 与 2 压 5 dB，-20 与 1.2 压 4 dB，-30 与 4 压 37 dB
- 压低量跟着触发声响度变。策划要写死 -4 dB 这种固定量，或一个类别同时压好几条总线，用电平加 AudioEffectAmplify，见 `references/mixing.md`

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

## 导入格式

| 素材 | 格式 | 导入设置 |
|---|---|---|
| 短音效 | WAV | `compress/mode` 默认 Quite OK Audio（4.3+），有损但接近原声，体积约 PCM 的 1/5。要逐位无损选 PCM |
| 音乐 长环境声 | Ogg Vorbis 或 MP3 | 动态音乐的 `bpm` `beat_count` 只有这两种有 |
| 3D 定位音源 | 单声道 WAV | `force/mono` 打开，或出素材时就导单声道 |

- 游戏里比原文件闷，先查播放器和总线，不是格式问题。WAV 转 Ogg 只会多一层有损压缩
- 96 kHz 24 bit 素材播放时按混音率重采样，多出的部分只占体积。打开 `force/max_rate` 并把 `force/max_rate_hz` 设为 48000，或出素材时导 48 kHz 16 bit
- 立体声素材在 3D 播放器里左右声道分别乘左右增益，声像宽度保留，定位不如单声道准

## 循环

- 在导入设置里设。WAV 用 `edit/loop_mode` `edit/loop_begin` `edit/loop_end`，单位是采样数，`loop_end` 为 -1 取文件末尾，`loop_mode` 默认 Detect From WAV 跟随文件元数据。Ogg Vorbis 与 MP3 用 `loop` 与 `loop_offset`，单位是秒。改完点 Reimport
- 不要运行时对共享的 stream 写 `loop = true`，所有引用同一资源的播放器一起变，缓存也被改。需要不同循环行为就导入两份，或 `duplicate()` 后再改
- 循环音频的播放器不发 `finished`

## 歌曲时间

节奏游戏要对齐音乐。`get_playback_position()` 按混音块更新，同一块内多次调用返回同一个值，要加上 `AudioServer.get_time_since_last_mix()`，再减输出延迟：

```gdscript
extends AudioStreamPlayer

var _latency: float = AudioServer.get_output_latency()

func song_time() -> float:
	return get_playback_position() + AudioServer.get_time_since_last_mix() - _latency
```

- `get_output_latency()` 开销大，类参考不建议每帧调，取一次存起来
- 结果有抖动，文档的做法是丢弃比上一帧小的值
- 几分钟的曲子，文档推荐另一种：`play()` 前记下 `Time.get_ticks_usec()`，再把 `AudioServer.get_time_to_next_mix()` 加输出延迟存为延迟，歌曲时间等于系统时钟走过的时间减延迟。不抖，但系统时钟与声卡时钟会慢慢漂移，长时间播放用上面的写法
- stream 是 AudioStreamInteractive 时 `get_playback_position()` 恒为 0.0

## 空间音频

- 2D 与 3D 播放器都有 `max_distance` `panning_strength` `area_mask`。衰减 2D 用 `attenuation` 指数，默认 1.0，3D 用 `attenuation_model` 加 `unit_size`。多普勒只有 3D 的 `doppler_tracking`
- 3D 听者是当前 Camera3D，2D 没有 AudioListener2D 时以视口中心为听点。要把听者放在别处，用 AudioListener2D 或 AudioListener3D 的 `make_current()`
- 全局声像强度见项目设置 `audio/general/2d_panning_strength` 与 `audio/general/3d_panning_strength`
- AudioStreamPlayer3D 默认带距离高频衰减，`attenuation_filter_cutoff_hz` 5000，`attenuation_filter_db` -24。强度按衰减后的音量算，`volume_db` 也计入，低于 0 dB 越多 5 kHz 以上压得越狠。俯视角、镜头距离固定、不需要空气吸收的游戏，把 `attenuation_filter_cutoff_hz` 设为 20500 关掉，类参考给的就是这个值。2D 播放器没有这个滤波

<!-- check: extends Node3D -->
```gdscript
@onready var _gun: AudioStreamPlayer3D = $Gun

func _ready() -> void:
	_gun.unit_size = 15.0
	_gun.volume_db = -8.0
	_gun.attenuation_filter_cutoff_hz = 20500.0
```

- 要保留远处发闷又想单独调小某个音效，别用 `volume_db` 调，改素材增益或给它单独一条总线调音量，总线音量不参与滤波计算

## 陷阱

- 3D 播放器写 `volume_db = -8` 调小音量，近处听也发闷。4.7.2 实测镜头 14 m、`unit_size` 15 时 8 kHz 以上被压约 24 dB。滤波按 `volume_db` 加距离衰减后的总量算，见空间音频
- AudioStreamPlayer3D 的 `volume_db` 加到距离衰减之后才被 `max_db` 截断。听者贴近声源时距离衰减有十几 dB 正值，`volume_db` 调低几 dB 听不出变化
- 每个播放器写 `volume_db = -6` 当音量设置，玩家无法分开调音乐与音效，改用总线
- 在会 `queue_free()` 的节点上播收尾音效，节点出树时声音被暂停，释放时被停止，播不完。交给关卡里常驻的播放器，如 AudioStreamPolyphonic 的 `play_stream()`
- `get_tree().paused = true` 时，`process_mode` 为默认的播放器会自动 `stream_paused`。暂停菜单的点击音，和暂停时要继续的音乐，把播放器的 `process_mode` 设为 `Node.PROCESS_MODE_ALWAYS`
- 压缩器侧链照默认参数写，`threshold` 0 dB 时一点都不压，调低后压低量又是公式的两倍左右，参数见混音
- 手写布局时子总线排在父总线前面，`send` 指向序号不小于自己的总线，引擎静默改发 Master，父总线的滑块管不到它
- 场景里的播放器 `bus` 留空就走 Master，音效和环境滑块都管不到。每个 `.tscn` 里的播放器都写 `bus`
- `AudioServer.get_bus_peak_volume_left_db` 读到的是推子和静音之后的电平，触发总线排在被压总线之后时侧链也一样。玩家调小语音，压缩器跟着少压，静音后不压，一般正合适。`threshold` 按默认音量调，不用为此另建总线
- 网页导出默认按 sample 方式播放，AudioEffect、多普勒、3D 混响总线、程序生成音频都不生效，空间音频也可能不正常。需要这些的播放器把 `playback_type` 设为 `AudioServer.PLAYBACK_TYPE_STREAM`，或改 `audio/general/default_playback_type.web`。代价是延迟更高，没开线程支持的导出更明显，可能爆音

## 参考

- [音频总线](https://docs.godotengine.org/en/stable/tutorials/audio/audio_buses.html)
- `references/dynamic-music.md`
- `references/mixing.md`：分类总线布局、响度测量与目标表、并发规则、固定量压低的写法、混音自查清单
