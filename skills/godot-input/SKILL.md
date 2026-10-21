---
name: godot-input
description: Godot 4 输入处理，InputMap 动作代替硬编码按键，Input.get_axis get_vector 死区，键盘手柄双绑定，_input _unhandled_input _process 轮询的选择，is_action_just_pressed 与 _physics_process 帧对齐，运行时改键 action_erase_events action_add_event 存档，鼠标捕获 MOUSE_MODE_CAPTURED，输入缓冲，触屏 VirtualJoystick。在写移动 跳跃 攻击 视角控制 改键菜单 手柄支持 时用。input map keybinding gamepad remap deadzone.
---

# Godot 输入

玩法输入一律走 InputMap 动作，同一个动作绑键盘与手柄，用 `Input` 的轴和向量接口读值。不管 UI 控件的焦点与点击，也不管按键提示文本，见 `godot-ui`。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 判断按键 | InputMap 动作加 `Input.is_action_pressed` | `event.keycode == KEY_W` |
| 一维轴 二维移动 | `Input.get_axis` `Input.get_vector` | 分别读两个方向再相减拼向量 |
| 摇杆死区 | 动作的 `deadzone`，`get_vector` 自动做圆形死区 | `if abs(x) < 0.2` |
| 手柄支持 | 同一动作加 `InputEventJoypadButton` `InputEventJoypadMotion` | 另写一套手柄分支 |
| 改键 | `InputMap.action_erase_event` 加 `action_add_event` | 自己维护按键表 |
| 触屏摇杆 | VirtualJoystick 4.7+，TouchScreenButton | 自己解析 `InputEventScreenTouch` |
| 模拟输入 | `Input.action_press`，`Input.parse_input_event` | 直接改自己的状态 |

## 定义动作

在项目设置 Input Map 页添加，键盘与手柄放进同一个动作：

```ini
[input]

jump={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
, Object(InputEventJoypadButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"button_index":0,"pressure":0.0,"pressed":false,"script":null)
]
}
```

- 移动键绑 `physical_keycode`，编辑器里选 Physical Keycode，AZERTY 布局上 WASD 位置不变。要字符含义的快捷键才用 `keycode`
- 摇杆每个方向一个 `InputEventJoypadMotion`：`axis_value` -1.0 绑 `move_left`，+1.0 绑 `move_right`。扳机轴只有 +1.0
- `device` 为 -1 表示所有设备。本地多人给每位玩家单独的动作如 `p1_jump`，指定各自设备编号
- 动作名用玩法语义，不复用 `ui_accept` `ui_up` 这类内置动作，它们驱动 UI 焦点

```gdscript
extends CharacterBody2D

const SPEED := 220.0

func _physics_process(_delta: float) -> void:
	velocity = Input.get_vector(&"move_left", &"move_right", &"move_up", &"move_down") * SPEED
	move_and_slide()
```

`get_vector` 的长度已限制为 1，不用再 `normalized()`。只有横向的平台游戏用 `Input.get_axis(&"move_left", &"move_right")`。模拟量用 `Input.get_action_strength`。

## 选回调

| 方式 | 适用 |
|---|---|
| `_physics_process` 里轮询 `Input.*` | 持续状态：移动，蓄力，按住 |
| `_unhandled_input(event)` | 一次性动作：跳，攻击，交互。UI 已处理的事件到不了这里 |
| `_input(event)` | 必须先于 UI 看到的：全局热键，改键捕获 |

事件顺序：`_input`，GUI，`_shortcut_input`，`_unhandled_key_input`，`_unhandled_input`。处理完调 `get_viewport().set_input_as_handled()`。

- 事件回调里用 `event.is_action_pressed(&"jump")`，文档要求不在输入处理中用 `Input.is_action_just_pressed`。默认不含按住重复，要重复传 `allow_echo = true`
- `Input.is_action_just_pressed` 在 `_process` 与 `_physics_process` 里各按帧和按物理 tick 计算，同一次按下两边各读到一次，按下又迅速松开也不丢
- 在哪个回调里消费就在哪个回调里读。别在 `_process` 里置标志让物理消费，一帧里物理可能跑 0 次或 2 次，标志会丢或重复

## 输入缓冲

`_unhandled_input` 记录，物理里消费，时间用 `Engine.get_physics_frames()`，不用毫秒，回放时结果一致：

```gdscript
extends CharacterBody2D

const BUFFER_TICKS := 6
const JUMP_SPEED := -420.0

var _jump_pressed_tick: int = -1000

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"jump"):
		_jump_pressed_tick = Engine.get_physics_frames()

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity += get_gravity() * delta
	elif Engine.get_physics_frames() - _jump_pressed_tick <= BUFFER_TICKS:
		velocity.y = JUMP_SPEED
		_jump_pressed_tick = -1000
	move_and_slide()
```

## 改键

```gdscript
extends Node

const SAVE_PATH := "user://keybinds.cfg"

func rebind(action: StringName, event: InputEventKey) -> void:
	_apply(action, event)
	var cfg := ConfigFile.new()
	cfg.load(SAVE_PATH)
	cfg.set_value("keys", action, event.physical_keycode)
	cfg.save(SAVE_PATH)

func load_saved(actions: Array[StringName]) -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return
	for action in actions:
		if cfg.has_section_key("keys", action):
			var event := InputEventKey.new()
			event.physical_keycode = cfg.get_value("keys", action) as Key
			_apply(action, event)

func _apply(action: StringName, event: InputEventKey) -> void:
	for old: InputEvent in InputMap.action_get_events(action):
		if old is InputEventKey:
			InputMap.action_erase_event(action, old)
	InputMap.action_add_event(action, event)
```

- 只清同一类设备的事件，改键盘键不要清掉手柄绑定
- 存档存键码整数，启动时调一次 `load_saved`
- 恢复默认：`InputMap.load_from_project_settings()` 再删存档文件。冲突检测用 `InputMap.action_has_event()`
- 捕获新按键：进入监听状态后，在 `_input` 里接第一个 `pressed` 的 `InputEventKey`，调 `set_input_as_handled()`，Esc 取消。手柄接 `InputEventJoypadButton`

## 鼠标与触屏

- 视角控制：`Input.mouse_mode = Input.MOUSE_MODE_CAPTURED`，在 `_unhandled_input` 里读 `InputEventMouseMotion.relative`。打开菜单时切回 `Input.MOUSE_MODE_VISIBLE`
- 2D 世界坐标用 `get_global_mouse_position()`，`get_viewport().get_mouse_position()` 是视口坐标
- `Input.use_accumulated_input` 默认 true，同一帧鼠标移动合并成一个事件。自由画线需要逐点轨迹时关掉
- VirtualJoystick 4.7+ 是 Control，`action_left` `action_right` `action_up` `action_down` 指到 InputMap 动作后，`Input.get_vector` 照常读，玩法代码不用改。它的 `deadzone_ratio` 先于动作死区生效
- 按钮用 TouchScreenButton 的 `action` 属性。`input_devices/pointing/emulate_mouse_from_touch` 默认开，触摸合成鼠标事件

## 陷阱

- 手写 `Axis(neg, pos)` 分别读两个轴拼向量，没有圆形死区，斜向速度超过 1
- InputMap 只有键盘事件，插手柄毫无反应。每个动作都检查手柄绑定
- 用 `Input.is_key_pressed(KEY_W)` 或 `event.keycode` 判断玩法键，改键和键盘布局都失效
- `_input` 里处理游戏内点击会穿透按钮，改 `_unhandled_input`
- 把 `ui_accept` `ui_cancel` 当玩法键，菜单打开时同时触发
- 键盘幽灵键让某些组合键的 `is_action_just_pressed` 为 false，组合键别设计得太多

## 参考

- [InputEvent](https://docs.godotengine.org/en/stable/tutorials/inputs/inputevent.html)
- [输入示例](https://docs.godotengine.org/en/stable/tutorials/inputs/input_examples.html)
- [手柄](https://docs.godotengine.org/en/stable/tutorials/inputs/controllers_gamepads_joysticks.html)
