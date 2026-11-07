# Theme 细节

StyleBox 种类与代码构造、theme type variation、LabelSettings。

## StyleBox

| 类 | 用途 |
|---|---|
| StyleBoxFlat | 纯色、圆角、描边、阴影 |
| StyleBoxTexture | 九宫格贴图 |
| StyleBoxEmpty | 去掉默认样式，如按钮焦点框 |
| StyleBoxLine | 分隔线 |

```gdscript
extends PanelContainer

func _ready() -> void:
	var box := StyleBoxFlat.new()
	box.bg_color = Color(0.1, 0.1, 0.12, 0.9)
	box.set_corner_radius_all(8)
	box.set_border_width_all(2)
	box.set_content_margin_all(12.0)
	add_theme_stylebox_override(&"panel", box)
```

```csharp
public partial class StyledPanel : PanelContainer
{
    public override void _Ready()
    {
        var box = new StyleBoxFlat();
        box.BgColor = new Color(0.1f, 0.1f, 0.12f, 0.9f);
        box.SetCornerRadiusAll(8);
        box.SetBorderWidthAll(2);
        box.SetContentMarginAll(12.0f);
        AddThemeStyleboxOverride("panel", box);
    }
}
```

- 复用的样式放进 Theme
- 代码构造只用于运行时才知道参数的样式

## theme type variation

同类控件多种样式：

1. Theme 里新建类型如 `DangerButton`，Base Type 选 `Button`
2. 节点上设 `theme_type_variation`

- 只有项目级 Theme 里的变体出现在 Inspector 下拉里

## LabelSettings

- 单个 Label 的字号颜色描边阴影用 `label_settings`
- LabelSettings 可多个 Label 共用，优先于 Theme
