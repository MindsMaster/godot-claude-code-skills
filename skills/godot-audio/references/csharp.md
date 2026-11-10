# C# 对照

SKILL.md 各节示例的 C# 写法和 C# 独有的要点。`.tres` `.tscn` 文本两种语言通用。

## 音量设置

```csharp
public partial class VolumeSlider : HSlider
{
    [Export] public StringName BusName { get; set; } = "Music";

    public override void _Ready()
    {
        Value = AudioServer.GetBusVolumeLinear(AudioServer.GetBusIndex(BusName));
        ValueChanged += OnValueChanged;
    }

    private void OnValueChanged(double linear)
    {
        AudioServer.SetBusVolumeLinear(AudioServer.GetBusIndex(BusName), (float)linear);
    }
}
```

- `Range.ValueChanged` 的参数是 `double`，传给 `AudioServer` 前转 `float`

## 动态音乐

```csharp
public partial class LayeredMusic : AudioStreamPlayer
{
    private const int CombatLayer = 1;
    private const float SilentDb = -60.0f;

    private Tween _fade;

    public void EnterCombat()
    {
        FadeCombat(0.0f);
    }

    public void ExitCombat()
    {
        FadeCombat(SilentDb);
    }

    private void FadeCombat(float targetDb)
    {
        var layers = (AudioStreamSynchronized)Stream;
        _fade?.Kill();
        _fade = CreateTween();
        _fade.TweenMethod(Callable.From<float>(SetCombatDb), layers.GetSyncStreamVolume(CombatLayer), targetDb, 1.0);
    }

    private void SetCombatDb(float db)
    {
        ((AudioStreamSynchronized)Stream).SetSyncStreamVolume(CombatLayer, db);
    }
}
```
