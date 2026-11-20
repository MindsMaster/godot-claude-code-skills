# Theme 细节

StyleBox 种类与代码构造、theme type variation、LabelSettings、界面音效。

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

## 界面音效

4.8+ Theme 有 sound 项，控件按交互自动播放，不用给每个按钮挂播放器。

```ini
[gd_resource type="Theme" load_steps=3 format=3]

[ext_resource type="AudioStream" path="res://ui/sfx/click.wav" id="1"]
[ext_resource type="AudioStream" path="res://ui/sfx/hover.wav" id="2"]

[resource]
Button/sounds/pressed_sound = ExtResource("1")
Button/sounds/hover_sound = ExtResource("2")
Button/sounds/focus_sound = ExtResource("2")
```

```ini
[audio]

buses/gui_theme_bus=&"UI"
```

| 控件类型 | sound 项 |
|---|---|
| `Button` | `pressed_sound` `hover_sound` `focus_sound` `pressed_disabled_sound` |
| `Slider` | `value_changed_sound` `drag_started_sound` `drag_ended_sound` `focus_sound` |
| `TabBar` `TabContainer` | `pressed_sound` `hover_sound` `focus_sound` |
| `LineEdit` | `text_changed_sound` `text_submitted_sound` `caret_moved_sound` `focus_sound` |
| `PopupMenu` | `item_activated_sound` `item_hovered_sound` |
| `ItemList` `Tree` | `item_selected_sound` `item_hovered_sound` `focus_sound` |

- 写在 `Button` 下，`CheckBox` `OptionButton` 等子类继承
- 写在 `BaseButton` 下不生效，`TextureButton` `LinkButton` 要按各自类型名另写
- `focus_sound` 只在键盘或手柄移动焦点时响，鼠标点击不响
- 播放器临时挂在 `root` 下，`PROCESS_MODE_ALWAYS`，暂停菜单里照样响
- 走 `audio/buses/gui_theme_bus` 指定的总线，默认 Master，总线不存在也回到 Master
- 单个控件静音：用 override 设一个长度为 0 的 AudioStream
- 每次音高略不同：sound 项填 AudioStreamRandomizer
- 代码里播放同一套音效：`play_theme_sound(get_theme_sound(&"pressed_sound"))`
