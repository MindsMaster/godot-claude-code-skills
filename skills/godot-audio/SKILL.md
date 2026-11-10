---
name: godot-audio
description: Godot 4 中所有发出声音的功能：播放、音量、混音、音乐、音效变化、空间音频、区域效果与音频导入。在 Godot 项目里新写或修改任何与声音有关的代码、场景或资源之前先加载，用户没提 bus 或 AudioStreamPlayer 也要加载，比如调音量、换背景音乐、让音效更自然、声音听不清或发闷、按音乐节拍计时、导出后声音异常。这类配置错了多半不报错只是没效果，如总线顺序、侧链阈值、area_mask、循环导入值，所以先读再动手。Use for any Godot audio task: AudioStreamPlayer, audio bus, volume, music, SFX, ducking, reverb, spatial audio, import.
---

# Godot 音频

播放器、总线、效果器、随机与分层的流资源写进 `default_bus_layout.tres`、`.tscn`、`.tres`，脚本只写运行时会变的部分，如滑条和切换音乐层。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 音乐 音效 语音分开调音量 | 总线布局加 `AudioServer.set_bus_volume_linear` | 每个播放器调 `volume_db` |
| 说话时压低音乐 | Music 总线上 AudioEffectCompressor，`sidechain` 设 Voice | 管理器在播语音时 Tween 音乐 |
| 同一音效每次不一样 | AudioStreamRandomizer 资源 | 手写随机下标和 `randf_range` |
| 连发时尾音叠起来 | 播放器 `max_polyphony` | 每发新建一个播放器 |
| 大量不同的一次性音效 | AudioStreamPolyphonic | 自建播放器池 |
| 多轨同拍 加减层 | AudioStreamSynchronized | 多个播放器同一帧 `play()` |
| 战斗探索切曲 曲目列表 | AudioStreamInteractive AudioStreamPlaylist | 多个播放器手动淡入淡出 |
| 区域内混响 | Area3D 的 `reverb_bus_enabled` | 每帧查位置改 `bus` |
| 区域内整体换声音 | Area2D Area3D 的 `audio_bus_override` | 进出区域信号里改 `bus` |
| 节奏游戏的歌曲时间 | `get_playback_position()` 加混音时间减延迟，见 [references/dynamic-music.md](references/dynamic-music.md) | `_process` 的 delta 累加 |
| 多类音效同时响 分开调比例 | SFX 下按类别建子总线 | 所有音效挤在一条 SFX |
| 慢动作时所有声音跟着变慢 | `AudioServer.playback_speed_scale`，新播的也生效 | 遍历播放器改 `pitch_scale` |
| 循环 | 导入设置 `edit/loop_mode`，见 [references/import.md](references/import.md) | 运行时改 `loop_mode` |
| 3D 音效近处发闷 | 查 `attenuation_filter_cutoff_hz` 和 `volume_db` | 把 WAV 转 Ogg 或改导入设置 |

## 陷阱

下列配置错了不报错，只是没效果：

| 现象 | 做法 |
|---|---|
| 侧链压缩器一点不压 | `threshold` 默认 0 dB，按[压低量公式](#说话时压低音乐)算 |
| 子总线滑块不起作用 | 子总线排在父总线前，`send` 被静默改发 Master |
| 区域对播放器无效 | 播放器 `area_mask` 默认 0，要包含区域的 `collision_layer` |
| 区域混响听不到 | `reverb_bus_amount` 默认 0，设 0.3 到 1 |
| WAV 不循环 | 导入 `edit/loop_mode=1` 是关闭，正向循环填 2 |
| 某些声音不受滑条控制 | `.tscn` 里 `bus` 留空走 Master，每个播放器都写 `bus` |
| 总线名拼错 | 播放器 `bus` 不存在时回退 Master |
| 3D 播放器 `volume_db` 为负后近处也发闷 | 滤波按 `volume_db` 加距离衰减算，音量挪到总线 |
| 3D 播放器调低几 dB 听不出 | 贴近时衰减有十几 dB 正值，`max_db` 截断在后 |
| 调小或静音语音后音乐不再压低 | Voice 排在 Music 后时侧链读推子后电平，排到前面 |
| 网页导出效果器 多普勒不生效 | 默认 sample 播放，`playback_type` 设 `AudioServer.PLAYBACK_TYPE_STREAM` |

## 做法

### 全局播放器

UI 音这类到处都要播的声音，播放器写进一个场景，注册成 autoload：

```ini
[gd_scene format=3]

[ext_resource type="AudioStream" path="res://click.wav" id="1_click"]

[node name="Audio" type="Node"]

[node name="Click" type="AudioStreamPlayer" parent="."]
stream = ExtResource("1_click")
bus = &"UI"
```

- 存为 `res://audio.tscn`，`project.godot` 的 `[autoload]` 写 `Audio="*res://audio.tscn"`
- 调用处 `Audio.get_node(^"Click").play()`
- 不要在 `_ready` 里用代码新建播放器再设 `stream` `bus`

### 总线布局

存为 `res://default_bus_layout.tres`，项目设置 `audio/buses/default_bus_layout` 默认读这个路径，不用改 `project.godot`：

```ini
[gd_resource type="AudioBusLayout" format=3]

[sub_resource type="AudioEffectCompressor" id="AudioEffectCompressor_duck"]
threshold = -20.0
ratio = 2.0
release_ms = 400.0
sidechain = &"Voice"

[resource]
bus/1/name = &"Voice"
bus/1/send = &"Master"
bus/2/name = &"Music"
bus/2/send = &"Master"
bus/2/effect/0/effect = SubResource("AudioEffectCompressor_duck")
bus/2/effect/0/enabled = true
bus/3/name = &"SFX"
bus/3/send = &"Master"
```

- 序号即顺序，`send` 只能指向序号更小的总线
- 要防爆音时 Master 上加 AudioEffectHardLimiter，AudioEffectLimiter 已弃用

### 音量设置

滑条的 `max_value = 1.0` 与 `step = 0.01` 写在 `.tscn` 里，脚本只接总线：

```gdscript
extends HSlider

@export var bus_name: StringName = &"Music"

func _ready() -> void:
	value = AudioServer.get_bus_volume_linear(AudioServer.get_bus_index(bus_name))
	value_changed.connect(_on_value_changed)

func _on_value_changed(linear: float) -> void:
	AudioServer.set_bus_volume_linear(AudioServer.get_bus_index(bus_name), linear)
```

- 线性 0 到 1 直接当 `volume_db` 听感不均匀
- `AudioServer.set_bus_volume_linear` 4.4+，0 即负无穷 dB，已经无声
- 总音量就是 Master 总线，同一个脚本 `bus_name` 填 Master

### 说话时压低音乐

[总线布局](#总线布局)里 Music 的压缩器就是压低，不用脚本，语音播放器 `bus` 走 Voice 即可。

| 公式 | 4.7.2 实测 |
|---|---|
| 压低量 | 2.08 ×（触发峰值 − `threshold`）×（1 − 1/`ratio`） |
| 反推 `threshold` | 触发峰值 − 目标压低量 ÷（2.08 ×（1 − 1/`ratio`）） |

| 触发峰值 | 目标 | `ratio` | `threshold` |
|---|---|---|---|
| -12 dBFS | 4 dB | 2 | -15.8 |
| -12 dBFS | 3 dB | 2 | -14.9 |
| -6 dBFS | 6 dB | 4 | -9.8 |

- 实测比公式小 0 到 1 dB
- `release_ms` 控制说完后恢复的快慢
- 压低量随语音响度变化是正常的，对白压音乐就用压缩器
- 说完后按 `release_ms` 自动恢复，不用监听语音结束
- 压缩器与 Music 滑条各自独立，滑条调的是总线音量
- 策划写明精确 dB，或一个触发压多条总线，才用 [references/mixing.md](references/mixing.md) 的固定量做法

### 随机音效

AudioStreamRandomizer 作为子资源写进播放器所在的 `.tscn`，或存成 `.tres` 共用：

```ini
[gd_scene format=3]

[ext_resource type="AudioStream" path="res://footstep_1.wav" id="1_step"]
[ext_resource type="AudioStream" path="res://footstep_2.wav" id="2_step"]

[sub_resource type="AudioStreamRandomizer" id="AudioStreamRandomizer_steps"]
random_pitch = 1.1
random_volume_offset_db = 2.0
streams_count = 2
stream_0/stream = ExtResource("1_step")
stream_1/stream = ExtResource("2_step")

[node name="Player" type="Node2D"]

[node name="Step" type="AudioStreamPlayer2D" parent="."]
stream = SubResource("AudioStreamRandomizer_steps")
bus = &"SFX"
```

- `playback_mode` 默认 `PLAYBACK_RANDOM_NO_REPEATS`，不连续重复，不用写
- `random_pitch` 是倍率，1.1 表示在 1/1.1 到 1.1 之间
- 按半音设用 `random_pitch_semitones` 4.6+
- `random_volume_offset_db` 2.0 表示正负 2 dB
- 每格权重 `stream_N/weight`，默认 1.0

### 同时多声

| 情况 | 做法 |
|---|---|
| 同一音效连续触发，如机枪 | `max_polyphony` 4 到 8，超出时切掉最老的，默认 1 |
| 很多不同的一次性音效 | 一个播放器挂 AudioStreamPolyphonic，用 `play_stream()` |
| 每个实体自己的位置声 | 每个实体一个 AudioStreamPlayer2D 或 3D |

- 一次性音效播放器的脚本见 [references/runtime.md](references/runtime.md)
- 声音走播放器的 `bus`，`play_stream` 的 `bus` 参数实测无效

### 动态音乐

4.3+。同一首曲子的分轨用 AudioStreamSynchronized，存成 `.tres` 挂到播放器 `stream`：

```ini
[gd_resource type="AudioStreamSynchronized" format=3]

[ext_resource type="AudioStream" path="res://explore.ogg" id="1_explore"]
[ext_resource type="AudioStream" path="res://combat.ogg" id="2_combat"]

[resource]
stream_count = 2
stream_0/stream = ExtResource("1_explore")
stream_0/volume = 0.0
stream_1/stream = ExtResource("2_combat")
stream_1/volume = -60.0
```

脚本只做淡入淡出：

```gdscript
extends AudioStreamPlayer

const COMBAT_LAYER := 1
const SILENT_DB := -60.0

var _fade: Tween

func enter_combat() -> void:
	_fade_combat(0.0)

func exit_combat() -> void:
	_fade_combat(SILENT_DB)

func _fade_combat(target_db: float) -> void:
	var layers := stream as AudioStreamSynchronized
	if _fade:
		_fade.kill()
	_fade = create_tween()
	_fade.tween_method(_set_combat_db, layers.get_sync_stream_volume(COMBAT_LAYER), target_db, 1.0)

func _set_combat_db(db: float) -> void:
	(stream as AudioStreamSynchronized).set_sync_stream_volume(COMBAT_LAYER, db)
```

| 资源 | 用途 |
|---|---|
| AudioStreamSynchronized | 多条子流同时开始，用层音量加减层，最多 32 层 |
| AudioStreamInteractive | 多片段加转场表，在拍点或小节处切换 |
| AudioStreamPlaylist | 顺序或乱序播放子流，可淡入淡出与循环 |

- 层音量改的是资源本身，多个播放器共用时一起变
- 子流各自在导入设置里开循环，见 [references/import.md](references/import.md)
- 切 Interactive 片段：`set(&"parameters/switch_to_clip", &"Combat")`

### 空间音频

| 项 | 2D | 3D |
|---|---|---|
| 衰减 | `attenuation` 指数，默认 1.0 | `attenuation_model` 加 `unit_size` |
| 听者 | 无 AudioListener2D 时为视口中心 | 当前 Camera3D |
| 距离高频滤波 | 无 | 默认开，`attenuation_filter_cutoff_hz` 5000，`attenuation_filter_db` -24 |

- 3D 滤波强度按衰减后的音量算，`volume_db` 也计入，负得越多压得越狠
- 不要空气吸收的音效，`attenuation_filter_cutoff_hz` 设 20500 关掉
- 要保留远处发闷又要调小，把音量挪到单独总线或素材增益

```ini
[gd_scene format=3]

[ext_resource type="AudioStream" path="res://gun.wav" id="1_gun"]

[node name="Gun" type="AudioStreamPlayer3D"]
stream = ExtResource("1_gun")
unit_size = 15.0
max_polyphony = 4
bus = &"Weapon"
```

### 区域混响

山洞、浴室这类区域，Area3D 把范围内发声的 3D 播放器送一份到混响总线：

```ini
[gd_scene format=3]

[sub_resource type="BoxShape3D" id="BoxShape3D_cave"]
size = Vector3(30, 10, 30)

[node name="Cave" type="Node3D"]

[node name="CaveZone" type="Area3D" parent="."]
reverb_bus_enabled = true
reverb_bus_name = &"CaveReverb"
reverb_bus_amount = 0.6

[node name="CollisionShape3D" type="CollisionShape3D" parent="CaveZone"]
shape = SubResource("BoxShape3D_cave")
```

- 布局里建 CaveReverb 总线，挂 AudioEffectReverb，`dry` 设 0
- 每个 3D 播放器 `area_mask` 包含区域的层，默认层是 1
- `reverb_bus_uniformity` 0 时混响从声源方向来，1 时四周均匀
- 2D 没有混响送出，用 `audio_bus_override` 加 `audio_bus_name` 整体换到带混响的总线

## 范围

| 不含 | 去哪 |
|---|---|
| 动画里的音频轨道 | godot-animation |
| 设置界面的生效与保存 | godot-ui |
| autoload 与普通节点的取舍 | godot-scene-architecture |

## 参考

- [references/csharp.md](references/csharp.md)：C# 项目先读，本文各节示例的 C# 写法
- [references/mixing.md](references/mixing.md)：分类总线布局、响度测量与目标、并发规则、固定量压低、混音自查
- [references/dynamic-music.md](references/dynamic-music.md)：Interactive 转场、Playlist、节奏游戏的歌曲时间
- [references/import.md](references/import.md)：选 WAV Ogg MP3、压缩、单声道、循环点
- [references/runtime.md](references/runtime.md)：一次性音效播放器，或程序生成总线、随机器时读
- https://docs.godotengine.org/en/stable/tutorials/audio/audio_buses.html
