# C# 对照

SKILL.md 各节示例的 C# 写法和 C# 独有的要点。

## 音量设置

```csharp
public partial class VolumeSlider : HSlider
{
    [Export] public StringName BusName { get; set; } = "Music";

    public override void _Ready()
    {
        MinValue = 0.0;
        MaxValue = 1.0;
        Step = 0.01;
        Value = AudioServer.GetBusVolumeLinear(AudioServer.GetBusIndex(BusName));
        ValueChanged += OnValueChanged;
    }

    private void OnValueChanged(double linear)
    {
        int bus = AudioServer.GetBusIndex(BusName);
        AudioServer.SetBusVolumeLinear(bus, (float)linear);
        AudioServer.SetBusMute(bus, linear <= 0.0);
    }
}
```

- `Range.ValueChanged` 的参数是 `double`，传给 `AudioServer` 前转 `float`

## 混音

```csharp
public partial class MusicDuck : Node
{
    public override void _Ready()
    {
        var duck = new AudioEffectCompressor();
        duck.Sidechain = "Voice";
        duck.Threshold = -18.0f;
        duck.Ratio = 1.5f;
        duck.ReleaseMs = 400.0f;
        AudioServer.AddBusEffect(AudioServer.GetBusIndex("Music"), duck);
    }
}
```

## 随机音效

```csharp
public partial class HitPlayer : AudioStreamPlayer
{
    [Export] public Godot.Collections.Array<AudioStream> Hits { get; set; } = new();

    public override void _Ready()
    {
        var random = new AudioStreamRandomizer();
        random.PlaybackMode = AudioStreamRandomizer.PlaybackModeEnum.RandomNoRepeats;
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

## 同时多声

```csharp
public partial class SfxPlayer : AudioStreamPlayer
{
    private AudioStreamPlaybackPolyphonic _poly;

    public override void _Ready()
    {
        var poly = new AudioStreamPolyphonic();
        poly.Polyphony = 16;
        Bus = "SFX";
        Stream = poly;
        Play();
        _poly = (AudioStreamPlaybackPolyphonic)GetStreamPlayback();
    }

    public long PlaySfx(AudioStream sound, float gainDb = 0.0f)
    {
        return _poly.PlayStream(sound, 0.0f, gainDb);
    }
}
```

- `AudioStreamPlaybackPolyphonic.PlayStream` 返回 `long` 播放 ID

## 歌曲时间

```csharp
public partial class Song : AudioStreamPlayer
{
    private readonly double _latency = AudioServer.GetOutputLatency();

    public double SongTime()
    {
        return GetPlaybackPosition() + AudioServer.GetTimeSinceLastMix() - _latency;
    }
}
```

## 空间音频

```csharp
public partial class GunSetup : Node3D
{
    private AudioStreamPlayer3D _gun;

    public override void _Ready()
    {
        _gun = GetNode<AudioStreamPlayer3D>("Gun");
        _gun.UnitSize = 15.0f;
        _gun.VolumeDb = -8.0f;
        _gun.AttenuationFilterCutoffHz = 20500.0f;
    }
}
```
