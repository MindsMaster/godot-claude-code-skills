# godot-input

## SKILL.md `Input.get_vector(&"move_left"`

```gdscript
Input.action_press(&"move_right")
Input.action_press(&"move_down")
await frames(2)
expect(is_equal_approx(node.velocity.length(), 220.0), "斜向长度限制为 1，速度 220")
Input.action_release(&"move_right")
Input.action_release(&"move_down")
Input.action_press(&"move_left", 0.1)
await frames(2)
expect(node.velocity == Vector2.ZERO, "强度 0.1 低于平均死区 0.2")
expect(is_equal_approx(Input.get_vector(&"move_left", &"move_right", &"move_up", &"move_down", 0.0).length(), 0.1), "第五个参数覆盖死区")
Input.action_release(&"move_left")
await frames(2)
expect(node.velocity == Vector2.ZERO, "松开后停下")
var stick := VirtualJoystick.new()
expect(stick.action_left == &"ui_left" and stick.action_up == &"ui_up", "VirtualJoystick 的 action_* 默认是 ui_*")
expect(is_zero_approx(stick.deadzone_ratio), "deadzone_ratio 默认 0")
stick.free()
expect(Input.use_accumulated_input, "use_accumulated_input 默认 true")
expect(ProjectSettings.get_setting("input_devices/pointing/emulate_mouse_from_touch") == true, "触摸合成鼠标默认开")
```

## SKILL.md `BUFFER_TICKS`

<!-- check: setup -->
```gdscript
var body_shape := CollisionShape2D.new()
var circle := CircleShape2D.new()
circle.radius = 10.0
body_shape.shape = circle
node.add_child(body_shape)
```

```gdscript
var floor_body := StaticBody2D.new()
var floor_shape := CollisionShape2D.new()
var floor_rect := RectangleShape2D.new()
floor_rect.size = Vector2(1000.0, 20.0)
floor_shape.shape = floor_rect
floor_body.add_child(floor_shape)
floor_body.position = Vector2(0.0, 100.0)
root.add_child(floor_body)
var press_jump := func() -> void:
	var ev := InputEventAction.new()
	ev.action = &"jump"
	ev.pressed = true
	Input.parse_input_event(ev)
	await frames(1)
	var release := InputEventAction.new()
	release.action = &"jump"
	release.pressed = false
	Input.parse_input_event(release)

var landed := false
var jumped := false
press_jump.call()
for i in 80:
	await frames(1)
	if node.is_on_floor():
		landed = true
	if node.velocity.y < -400.0:
		jumped = true
expect(landed and not jumped, "落地前 6 个 tick 之外的按键已过期，落地不起跳")

node.position = Vector2.ZERO
node.velocity = Vector2.ZERO
await frames(2)
var late_jump_seen := false
for i in 80:
	await frames(1)
	if node.position.y > 60.0 and not late_jump_seen:
		late_jump_seen = true
		press_jump.call()
		await frames(1)
	if node.velocity.y < -400.0:
		jumped = true
		break
expect(jumped, "落地前 6 个 tick 内的按键在落地时起跳")
await frames(1)
expect(node._jump_pressed_tick == -1000, "起跳后缓冲清零")
floor_body.free()
```

## SKILL.md `keybinds.cfg`

<!-- check: setup -->
```gdscript
var space := InputEventKey.new()
space.physical_keycode = KEY_SPACE
var pad := InputEventJoypadButton.new()
pad.button_index = JOY_BUTTON_A
ProjectSettings.set_setting("input/jump", {"deadzone": 0.2, "events": [space, pad]})
InputMap.load_from_project_settings()
```

```gdscript
var actions: Array[StringName] = [&"jump"]
var key_j := InputEventKey.new()
key_j.physical_keycode = KEY_J
node.rebind(&"jump", key_j)
var has_pad := false
var physical := KEY_NONE
for e: InputEvent in InputMap.action_get_events(&"jump"):
	if e is InputEventJoypadButton:
		has_pad = true
	elif e is InputEventKey:
		physical = (e as InputEventKey).physical_keycode
expect(has_pad, "改键盘键保留手柄绑定")
expect(physical == KEY_J, "键盘键换成 J")
var conflict := InputEventKey.new()
conflict.physical_keycode = KEY_J
expect(InputMap.action_has_event(&"jump", conflict), "action_has_event 能查到冲突")
var saved := ConfigFile.new()
expect(saved.load("user://keybinds.cfg") == OK and saved.get_value("keys", "jump") == KEY_J, "存档存键码整数")

InputMap.load_from_project_settings()
var restored := KEY_NONE
for e: InputEvent in InputMap.action_get_events(&"jump"):
	if e is InputEventKey:
		restored = (e as InputEventKey).physical_keycode
expect(restored == KEY_SPACE, "load_from_project_settings 恢复默认键")
node.load_saved(actions)
physical = KEY_NONE
for e: InputEvent in InputMap.action_get_events(&"jump"):
	if e is InputEventKey:
		physical = (e as InputEventKey).physical_keycode
expect(physical == KEY_J, "load_saved 读回存档")
expect(InputMap.action_get_events(&"jump").size() == 2, "读回后仍是一个键加一个手柄")
DirAccess.remove_absolute("user://keybinds.cfg")
```
