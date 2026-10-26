# 混音细节

SKILL.md 混音一节的展开：布局怎么写、响度怎么测、并发怎么限、固定量压低怎么做。

## 分类总线布局

```ini
[gd_resource type="AudioBusLayout" format=3]

[sub_resource type="AudioEffectHardLimiter" id="AudioEffectHardLimiter_1"]
ceiling_db = -1.0

[sub_resource type="AudioEffectAmplify" id="AudioEffectAmplify_music"]
resource_name = "Duck"

[sub_resource type="AudioEffectAmplify" id="AudioEffectAmplify_weapon"]
resource_name = "Duck"

[resource]
bus/0/effect/0/effect = SubResource("AudioEffectHardLimiter_1")
bus/0/effect/0/enabled = true
bus/1/name = &"SFX"
bus/1/send = &"Master"
bus/2/name = &"Music"
bus/2/send = &"Master"
bus/2/effect/0/effect = SubResource("AudioEffectAmplify_music")
bus/2/effect/0/enabled = true
bus/3/name = &"Ambience"
bus/3/send = &"Master"
bus/4/name = &"Weapon"
bus/4/send = &"SFX"
bus/4/effect/0/effect = SubResource("AudioEffectAmplify_weapon")
bus/4/effect/0/enabled = true
bus/5/name = &"MonsterAttack"
bus/5/send = &"SFX"
bus/6/name = &"UI"
bus/6/send = &"SFX"
```

- 引擎从最后一条总线往前处理，`send` 指向序号不小于自己的总线时改发 Master。子总线写在 SFX 后面
- 玩家滑块挂 Master Music SFX Ambience，子总线的音量只给策划调
- 要被压低的总线第一个效果器放一个 AudioEffectAmplify，压低只改它，不动总线音量
- 场景里每个播放器都写 `bus`。可以写一个测试遍历 `.tscn`，查出没写 `bus` 的 AudioStreamPlayer 节点

## 响度

| 素材 | 看什么 |
|---|---|
| 一次性短音效 | 最大瞬时响度 LUFS-M，400 ms 窗 |
| 音乐 环境循环 | 整体响度 LUFS-I |
| 全部 | 真峰值 dBTP |

ffmpeg 的 ebur128 测量。短于 0.4 s 的音效不出瞬时值，整体响度显示 -70，先用 apad 补静音：

```
ffmpeg -v verbose -nostats -i shot.wav -af apad=pad_dur=0.5,ebur128=framelog=verbose -f null - 2>&1 | grep -oE ' M: *-?[0-9.]+' | awk '{print $2}' | sort -g | tail -1
ffmpeg -nostats -i music.ogg -af ebur128=peak=true -f null - 2>&1 | tail -12
```

统一响度：增益等于目标减测得值，`ffmpeg -i in.wav -af volume=3.2dB -c:a pcm_s16le out.wav`，再测一次真峰值。超过 -1 dBTP 就降目标或先做轻度饱和，不要靠 Master 的限幅器兜底。有损格式的音乐和循环不重新编码，差值写在播放器音量里。

默认音量下各类别的起点，PC 和主机。手机整体高 6 dB 左右：

| 类别 | 目标 |
|---|---|
| 音乐 | -24 LUFS-I |
| 环境床 | -30 到 -37 LUFS-I |
| 武器开火 | -20 LUFS-M，单发重武器 -17，高射速 -22 |
| 武器技能 | -18 LUFS-M |
| 怪物出招 | -21 LUFS-M |
| 宝箱 拾取等互动 | -22 LUFS-M |
| 换弹 UI | -24 LUFS-M |
| 怪物常驻声 | -26 LUFS-M |
| 命中 暴击 击杀反馈 | -30 到 -27 LUFS-M |

整体依据 ASWG-R001 与 IESD 的混音参考：主机和 PC -24 LUFS 加减 2，手机 -18，真峰值 -1 dBTP。

## 并发

Unreal 的 Sound Concurrency 规则在 Godot 里的对应：

| Unreal | Godot |
|---|---|
| StopOldest | `max_polyphony`，满了切掉最老的 |
| PreventNew | AudioStreamPolyphonic，满了 `play_stream` 返回 `AudioStreamPlaybackPolyphonic.INVALID_ID` |
| StopLowestPriority StopQuietest StopFarthestThenOldest | 自己管一组播放器，满了按优先级、音量或距离挑一个 `stop()` 再播 |

| 类别 | 起点 |
|---|---|
| 每把枪开火 | 4 到 8 |
| 换弹 | 每把枪 1，换枪、打断时停 |
| 命中反馈 | 全局 4 左右，几十毫秒内同类只放优先级最高的一条 |
| 怪物出招 | 全局 4 到 6，出招优先于常驻声 |
| UI | 2 |

## 两种压低做法

| | 压缩器侧链 | 电平加 Amplify |
|---|---|---|
| 压低量 | 随触发声响度变 | 固定，写多少压多少 |
| 写法 | 布局里加效果器，不写脚本 | 一个常驻节点每帧读电平 |
| 一个触发压多条总线 | 每条目标总线各加一个压缩器 | 一张规则表 |
| 适合 | 语音压音乐 | 怪物出招压枪声和音乐，技能压枪声 |

固定量压低。压的是目标总线第一个效果器的 `volume_db`，玩家滑块和策划推子不受影响：

```gdscript
extends Node

const TRIGGER_DB := -45.0
const ATTACK_DB_PER_SEC := 120.0
const RELEASE_DB_PER_SEC := 10.0

@export var key_bus: StringName = &"MonsterAttack"
@export var target_bus: StringName = &"Music"
@export var depth_db: float = -3.0

var _duck: AudioEffectAmplify

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_duck = AudioEffectAmplify.new()
	AudioServer.add_bus_effect(AudioServer.get_bus_index(target_bus), _duck, 0)

func _process(delta: float) -> void:
	var key := AudioServer.get_bus_index(key_bus)
	var level := maxf(AudioServer.get_bus_peak_volume_left_db(key, 0), AudioServer.get_bus_peak_volume_right_db(key, 0))
	var target := depth_db if level > TRIGGER_DB else 0.0
	var rate := ATTACK_DB_PER_SEC if target < _duck.volume_db else RELEASE_DB_PER_SEC
	_duck.volume_db = move_toward(_duck.volume_db, target, rate * delta)
```

- 压得快放得慢，放回太快听起来像音量抖了一下。连续出招之间有空隙时，加 0.1 到 0.2 s 的保持再放
- 电平是触发总线推子之后的值。`TRIGGER_DB` 取得低，玩家把音效调小后仍会触发，压低量不变
- 布局里已经放了 Amplify 时，用 `AudioServer.get_bus_effect(bus, 0)` 取出来改，不要再加一个
- 压低量 2 到 4 dB 起步，进游戏听，比看数字准

## 自查清单

- 每个播放器都写了 `bus`，没有直接走 Master 的
- 子总线排在父总线之后
- 素材按类别统一响度，真峰值不超过 -1 dBTP
- 每类声音有并发上限
- 常播的音效 3 到 5 条变体，AudioStreamRandomizer 加轻微音高与音量随机
- 3D 声源单声道，按需关掉 `attenuation_filter_cutoff_hz` 的距离滤波
- 最激烈的战斗段落里 Master 限幅器不长时间压着
- 菜单暂停时要继续响的播放器和压低节点设 `Node.PROCESS_MODE_ALWAYS`
