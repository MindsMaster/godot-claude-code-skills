# 动态音乐

AudioStreamInteractive 转场、Synchronized 分层、Playlist，4.3+。三种资源都挂在普通 AudioStreamPlayer 上，`bus` 照常指向 Music。

| 资源 | 用途 |
|---|---|
| AudioStreamInteractive | 多个片段加转场表，按状态切片段，在拍点或小节处淡入淡出 |
| AudioStreamPlaylist | 按顺序或乱序播放子流，可淡入淡出与循环 |
| AudioStreamSynchronized | 多条子流同时开始，分层配器，用音量加减层 |

AudioStreamInteractive 在 Inspector 填 `clip_count`，每个片段设名字与流，再配转场表。片段音频在导入设置里填 `bpm` 与 `beat_count`，转场才能按拍对齐。这些选项只有 Ogg Vorbis 与 MP3 有，WAV 没有，音乐用这两种格式导入。切换片段：

```gdscript
extends AudioStreamPlayer

func enter_combat() -> void:
	set(&"parameters/switch_to_clip", &"Combat")

func enter_explore() -> void:
	var playback := get_stream_playback() as AudioStreamPlaybackInteractive
	playback.switch_to_clip_by_name(&"Explore")
```

```csharp
public partial class MusicPlayer : AudioStreamPlayer
{
    private static readonly StringName SwitchToClip = "parameters/switch_to_clip";
    private static readonly StringName Combat = "Combat";
    private static readonly StringName Explore = "Explore";

    public void EnterCombat()
    {
        Set(SwitchToClip, Combat);
    }

    public void EnterExplore()
    {
        var playback = (AudioStreamPlaybackInteractive)GetStreamPlayback();
        playback.SwitchToClipByName(Explore);
    }
}
```

- 转场用 `add_transition()`，`AudioStreamInteractive.CLIP_ANY` 表示任意片段，`FADE_AUTOMATIC` 选常用淡入淡出
- AudioStreamSynchronized 最多 32 层，层音量用 `set_sync_stream_volume(index, db)`，改的是资源本身，多个播放器共用时一起变，需要时 `duplicate()`
- 只要两首曲子交叉淡入淡出，对 `volume_db` 用 Tween 即可

## 代码构造 Interactive

常规在 Inspector 里配。程序生成或测试时：

```gdscript
extends AudioStreamPlayer

@export var explore: AudioStream
@export var combat: AudioStream

func _ready() -> void:
	var music := AudioStreamInteractive.new()
	music.clip_count = 2
	music.set_clip_name(0, &"Explore")
	music.set_clip_stream(0, explore)
	music.set_clip_name(1, &"Combat")
	music.set_clip_stream(1, combat)
	music.add_transition(
		AudioStreamInteractive.CLIP_ANY,
		AudioStreamInteractive.CLIP_ANY,
		AudioStreamInteractive.TRANSITION_FROM_TIME_NEXT_BEAT,
		AudioStreamInteractive.TRANSITION_TO_TIME_START,
		AudioStreamInteractive.FADE_AUTOMATIC,
		1.0
	)
	stream = music
	play()
```

```csharp
public partial class InteractiveMusic : AudioStreamPlayer
{
    [Export] public AudioStream Explore { get; set; }
    [Export] public AudioStream Combat { get; set; }

    public override void _Ready()
    {
        var music = new AudioStreamInteractive();
        music.ClipCount = 2;
        music.SetClipName(0, "Explore");
        music.SetClipStream(0, Explore);
        music.SetClipName(1, "Combat");
        music.SetClipStream(1, Combat);
        music.AddTransition(
            (int)AudioStreamInteractive.ClipAny,
            (int)AudioStreamInteractive.ClipAny,
            AudioStreamInteractive.TransitionFromTime.NextBeat,
            AudioStreamInteractive.TransitionToTime.Start,
            AudioStreamInteractive.FadeMode.Automatic,
            1.0f);
        Stream = music;
        Play();
    }
}
```

- C# 里 `AudioStreamInteractive.ClipAny` 是 `long` 常量，传参转 `int`
- 转场的 `from_time` 有 `TRANSITION_FROM_TIME_IMMEDIATE` `NEXT_BEAT` `NEXT_BAR` `END`，`to_time` 有 `SAME_POSITION` `START` `PREVIOUS_POSITION`
- `fade_beats` 以拍计，片段音频需要在导入设置里填 `bpm`，`NEXT_BAR` 还要 `bar_beats`
- 一次性过场乐句：`set_clip_auto_advance()` 设 `AUTO_ADVANCE_ENABLED`，`set_clip_auto_advance_next_clip()` 指定下一片段
- 片段自身循环时自动跳转被忽略
- 要回到转场前的片段，转场 `hold_previous` 设 true，过场片段用 `AUTO_ADVANCE_RETURN_TO_HOLD`

## Synchronized 分层

多条子流同一时刻开始，到最后一条结束才结束，任何一条循环则整体继续。用层音量表达强度：

```gdscript
extends AudioStreamPlayer

@export var base_layer: AudioStream
@export var drums_layer: AudioStream

func _ready() -> void:
	var layers := AudioStreamSynchronized.new()
	layers.stream_count = 2
	layers.set_sync_stream(0, base_layer)
	layers.set_sync_stream(1, drums_layer)
	layers.set_sync_stream_volume(1, -60.0)
	stream = layers
	play()

func set_intensity(high: bool) -> void:
	var synced := stream as AudioStreamSynchronized
	synced.set_sync_stream_volume(1, 0.0 if high else -60.0)
```

```csharp
public partial class LayeredMusic : AudioStreamPlayer
{
    [Export] public AudioStream BaseLayer { get; set; }
    [Export] public AudioStream DrumsLayer { get; set; }

    public override void _Ready()
    {
        var layers = new AudioStreamSynchronized();
        layers.StreamCount = 2;
        layers.SetSyncStream(0, BaseLayer);
        layers.SetSyncStream(1, DrumsLayer);
        layers.SetSyncStreamVolume(1, -60.0f);
        Stream = layers;
        Play();
    }

    public void SetIntensity(bool high)
    {
        var synced = (AudioStreamSynchronized)Stream;
        synced.SetSyncStreamVolume(1, high ? 0.0f : -60.0f);
    }
}
```

`set_sync_stream_volume` 直接设值。要渐变，用 `tween_method` 驱动一个回调，回调里调它。

## Playlist

`stream_count` 设曲目数，最多 64，`set_list_stream(index, stream)` 填曲目，`shuffle` 默认 false，开启后每次开始与每次循环重新洗牌，`loop` 默认 true，`fade_time` 默认 0.3 秒。淡出需要曲目末尾留一小段尾音。Playlist 是流资源，同样挂在播放器上，不用监听 `finished` 自己换曲。
