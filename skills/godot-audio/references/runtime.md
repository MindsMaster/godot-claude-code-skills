# 运行时构造

一次性音效播放器，以及用代码建压缩器、随机器和 3D 播放器参数。关卡或总线由程序生成、在测试里搭场景时用，能写进 `.tres` `.tscn` 的照 SKILL.md 写进文件。

## 压缩器侧链

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

<!-- check: extends Node -->
```csharp
public override void _Ready()
{
    var duck = new AudioEffectCompressor();
    duck.Sidechain = "Voice";
    duck.Threshold = -18.0f;
    duck.Ratio = 1.5f;
    duck.ReleaseMs = 400.0f;
    AudioServer.AddBusEffect(AudioServer.GetBusIndex("Music"), duck);
}
```

- -12 dBFS 的语音按公式压低约 4.2 dB，实测约 4 dB

| 4.7.2 实测，触发峰值 -6 dBFS | 压低 |
|---|---|
| `threshold` -12，`ratio` 2 | 5 dB |
| `threshold` -20，`ratio` 1.2 | 4 dB |
| `threshold` -30，`ratio` 4 | 37 dB |

## 随机器

```gdscript
extends AudioStreamPlayer

@export var hits: Array[AudioStream] = []

func _ready() -> void:
	var random := AudioStreamRandomizer.new()
	random.random_pitch = 1.1
	random.random_volume_offset_db = 2.0
	for hit in hits:
		random.add_stream(-1, hit)
	stream = random
```

```csharp
public partial class HitPlayer : AudioStreamPlayer
{
    [Export] public Godot.Collections.Array<AudioStream> Hits { get; set; } = new();

    public override void _Ready()
    {
        var random = new AudioStreamRandomizer();
        random.RandomPitch = 1.1f;
        random.RandomVolumeOffsetDb = 2.0f;
        foreach (AudioStream hit in Hits)
        {
            random.AddStream(-1, hit);
        }
        Stream = random;
    }
}
```

- `add_stream` 第一参数小于 0 追加到末尾，第三参数是权重，默认 1.0

## 3D 距离滤波

<!-- check: extends Node3D -->
```gdscript
@onready var _gun: AudioStreamPlayer3D = $Gun

func _ready() -> void:
	_gun.unit_size = 15.0
	_gun.volume_db = -8.0
	_gun.attenuation_filter_cutoff_hz = 20500.0
```

<!-- check: extends Node3D -->
```csharp
private AudioStreamPlayer3D _gun;

public override void _Ready()
{
    _gun = GetNode<AudioStreamPlayer3D>("Gun");
    _gun.UnitSize = 15.0f;
    _gun.VolumeDb = -8.0f;
    _gun.AttenuationFilterCutoffHz = 20500.0f;
}
```

- 实测镜头 14 m、`unit_size` 15、`volume_db` -8 时默认滤波把 8 kHz 以上压约 24 dB
- `volume_db` 回到 0 后同一距离基本不滤波

## 一次性音效播放器

场景里给播放器 `stream` 填 AudioStreamPolyphonic，`polyphony` 默认 32：

```gdscript
extends AudioStreamPlayer

var _poly: AudioStreamPlaybackPolyphonic

func _ready() -> void:
	play()
	_poly = get_stream_playback()

func play_sfx(sound: AudioStream, gain_db: float = 0.0) -> int:
	return _poly.play_stream(sound, 0.0, gain_db)
```

```csharp
public partial class SfxPlayer : AudioStreamPlayer
{
    private AudioStreamPlaybackPolyphonic _poly;

    public override void _Ready()
    {
        Play();
        _poly = (AudioStreamPlaybackPolyphonic)GetStreamPlayback();
    }

    public long PlaySfx(AudioStream sound, float gainDb = 0.0f)
    {
        return _poly.PlayStream(sound, 0.0f, gainDb);
    }
}
```

- 声音走播放器的 `bus`，4.7.2 实测 `play_stream` 的 `bus` 参数无效
- 返回播放 ID，给 `stop_stream` `set_stream_volume` 用，C# 里是 `long`
- 并发满了返回 `AudioStreamPlaybackPolyphonic.INVALID_ID`
