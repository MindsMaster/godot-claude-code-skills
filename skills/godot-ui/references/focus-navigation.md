# 焦点导航与按键提示

手柄和键盘操作菜单的焦点设置、按键提示文本的取法、无障碍。

## 焦点导航

- 场景启动后须有控件拿焦点，否则方向键和手柄无反应
- 写法：`$StartButton.grab_focus.call_deferred()`
- 面板显示时对第一个按钮 `grab_focus()`
- 控件隐藏会丢焦点，面板重新显示要再抓
- `ui_up` `ui_down` `ui_left` `ui_right` `ui_accept` `ui_cancel` `ui_focus_next` 驱动焦点
- 引擎猜的邻居不准时，在 Focus 分类显式设 `focus_neighbor_left` 等
- Tab 顺序设 `focus_next` `focus_previous`

| `focus_mode` | 含义 |
|---|---|
| `FOCUS_ALL` | 可点击可导航，Button 默认 |
| `FOCUS_CLICK` | 只能点击 |
| `FOCUS_NONE` | 不可聚焦，Label 默认 |

- 子树禁止聚焦：`focus_behavior_recursive = Control.FOCUS_BEHAVIOR_DISABLED` 4.5+
- 悬停也聚焦：`mouse_entered.connect(grab_focus)`
- 弹窗打开前存 `get_viewport().gui_get_focus_owner()`，关闭后还焦点
- ScrollContainer 设 `follow_focus = true`，聚焦项自动滚入视野

## 按键提示

提示文本从 InputMap 取，玩家改键后自动跟随：

```gdscript
extends Label

@export var action: StringName = &"interact"

func _ready() -> void:
	text = tr("PROMPT_INTERACT").format({key = _key_text(action)})

func _key_text(action_name: StringName) -> String:
	for event: InputEvent in InputMap.action_get_events(action_name):
		if event is InputEventKey:
			return (event as InputEventKey).as_text_physical_keycode()
	return ""
```

```csharp
public partial class KeyPrompt : Label
{
    [Export] public StringName Action { get; set; } = "interact";

    public override void _Ready()
    {
        Text = Tr("PROMPT_INTERACT").Replace("{key}", KeyText(Action));
    }

    private static string KeyText(StringName actionName)
    {
        foreach (InputEvent ev in InputMap.ActionGetEvents(actionName))
        {
            if (ev is InputEventKey key)
            {
                return key.AsTextPhysicalKeycode();
            }
        }
        return "";
    }
}
```

| 绑定 | 显示文本 |
|---|---|
| `physical_keycode` | `as_text_physical_keycode()` |
| `keycode` | `as_text_keycode()` |
| 手柄按钮 | 按 `InputEventJoypadButton.button_index` 映射到自己的图标 |

- `InputEvent.as_text()` 对物理键带 Physical 后缀，手柄是长描述
- `as_text_physical_keycode()` 给 US QWERTY 位置的名字
- 键帽字母：`OS.get_keycode_string(DisplayServer.keyboard_get_label_from_physical(key.physical_keycode))`
- 上式只有 Linux Windows macOS 实现，其他平台和无头报错并原样返回
- 设备切换：`_input` 里记最近事件是 `InputEventJoypadButton` 还是 `InputEventKey`

## 无障碍

- 4.7+ AccessibilityServer 为每个节点自动生成无障碍元素
- 不用手动调 `create_element`
- `accessibility/general/accessibility_support` 默认 0，检测到读屏软件才处理
- 纯图标按钮和自绘控件设 `accessibility_name` `accessibility_description` 4.5+
