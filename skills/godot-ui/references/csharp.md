# C# 对照

SKILL.md 各节示例的 C# 写法。通用的 C# 规则见 godot-csharp。

## 布局

```csharp
public partial class BottomPrompt : Control
{
    public override void _Ready()
    {
        SetAnchorsAndOffsetsPreset(LayoutPreset.CenterBottom, LayoutPresetMode.Minsize, 32);
    }
}
```

- 枚举在 Control 内：`Control.LayoutPreset`、`Control.LayoutPresetMode`

## Theme

```csharp
public partial class TeamBar : ProgressBar
{
    public void SetTeamColor(Color color)
    {
        var fill = (StyleBoxFlat)GetThemeStylebox("fill").Duplicate();
        fill.BgColor = color;
        AddThemeStyleboxOverride("fill", fill);
    }
}
```

- `Duplicate()` 返回 Resource，强转回 StyleBoxFlat
- 主题项名是 `StringName`，每帧调用时缓存成 `static readonly StringName`

## 血条

```csharp
public partial class HealthBar : Control
{
    private ProgressBar _front;
    private ProgressBar _chip;
    private Tween _tween;

    public override void _Ready()
    {
        _front = GetNode<ProgressBar>("%Front");
        _chip = GetNode<ProgressBar>("%Chip");
    }

    public void SetHealth(float value)
    {
        _front.Value = value;
        _tween?.Kill();
        _tween = CreateTween();
        _tween.TweenInterval(0.4);
        _tween.TweenProperty(_chip, "value", value, 0.3).SetTrans(Tween.TransitionType.Cubic).SetEase(Tween.EaseType.Out);
    }
}
```

- `Range.Value` 是 double，float 赋值自动转换

## 本地化

```csharp
public partial class ItemCount : Label
{
    private int _count;

    public override void _Notification(int what)
    {
        if (what == NotificationTranslationChanged)
        {
            Text = TrN("%d item", "%d items", _count).Replace("%d", _count.ToString());
        }
    }
}
```

- C# 字符串没有 Godot 的 `%` 格式化，`%d` 用 Replace 替换
- 命名占位符同样 Replace，见 [localization.md](localization.md)
