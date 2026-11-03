# 设置界面

SKILL.md 讲界面怎么搭。本文讲设置什么时候生效、什么时候写盘，窗口模式与尺寸怎么确认和还原，以及失焦时自动暂停。音量换算见 godot-audio，键位重绑见 godot-input，`ConfigFile` 读写见 godot-resources-data。

## 生效与写盘的时机

| 类别 | 生效 | 写盘 |
|---|---|---|
| 音量 亮度 对比度 语言 键位 帧率上限 垂直同步 抗锯齿 渲染倍率 | 改值当下 | 离开设置界面时一次 |
| 窗口模式 窗口尺寸 | 点应用后，同时弹确认框倒计时 | 只写已确认的值 |

- 改值当下生效，玩家才能边听边调音量、边看边调亮度。改完要点保存才生效的界面没法预览
- 写盘放在界面隐藏和退出场景树时。返回键、Esc、宿主隐藏父节点走隐藏，`queue_free`、切场景、退出程序只走退出场景树，不发 `NOTIFICATION_VISIBILITY_CHANGED`。不要每拖一格滑块写一次文件
- 打开时留一份原值给撤销更改用，恢复默认只重置当前分页
- 每次改值都调同一个 apply 时，键位和窗口按上次应用的值比对，变了才重设。否则拖音量滑块也会重建 InputMap，还会把玩家手动拖过的窗口尺寸拉回去

```gdscript
extends Control

const SETTINGS_PATH := "user://settings.cfg"

var draft: Dictionary = {}
var _opened: Dictionary = {}
var _editing := false


func open(current: Dictionary) -> void:
	_opened = current.duplicate(true)
	draft = current.duplicate(true)
	_editing = true
	show()


func set_value(key: String, value: Variant) -> void:
	draft[key] = value
	_apply(draft)


func revert() -> void:
	draft = _opened.duplicate(true)
	_apply(draft)


func _notification(what: int) -> void:
	var closing := what == NOTIFICATION_VISIBILITY_CHANGED and not is_visible_in_tree()
	if (closing or what == NOTIFICATION_EXIT_TREE) and _editing:
		_editing = false
		_save(draft)


func _apply(values: Dictionary) -> void:
	var bus := AudioServer.get_bus_index("Master")
	var volume: float = values.get("master_volume", 1.0)
	AudioServer.set_bus_volume_linear(bus, volume)
	AudioServer.set_bus_mute(bus, volume <= 0.0)


func _save(values: Dictionary) -> void:
	var config := ConfigFile.new()
	for key: String in values:
		config.set_value("settings", key, values[key])
	config.save(SETTINGS_PATH)
```

## 窗口模式确认与还原

做法同操作系统的显示设置：窗口模式和尺寸改值时只记下，不动窗口。玩家点应用后才切换并弹确认框，倒计时内不点保留就回到上次确认的值。

- 改值当下切窗口的话，玩家左右翻选项时窗口跟着来回切，每切一次弹一个确认框，看不清自己选到了哪个
- 有未应用的改动时离开设置，弹框问应用、放弃、取消。应用走上面的确认流程，放弃把选项退回已确认的值再离开，取消留在设置里
- 只有窗口相关的选项要等应用。垂直同步、帧率上限、渲染倍率这些切错了画面照样可见，改值当下生效
- 确认前的值只在内存里，写盘只写已确认的值。倒计时期间崩溃或被结束进程，下次启动用的仍是能用的设置
- 倒计时用 `create_timer(15.0, true, false, true)`，暂停时照走，第 4 个参数让它不受 `Engine.time_scale` 影响
- 失焦时也要继续倒计时，玩家看不见画面时只能靠超时还原
- 设置界面被强制关闭时丢掉未应用的值，倒计时中的按还原处理，再写盘
- 方向键导航在最近的根 Control 下按距离找下一个焦点。父节点不是 Control 或设了 `top_level` 的 Control 自成一个根。确认框作为设置面板的子节点时，焦点会跳到框外的面板上。4.5+ 给背后的面板设 `focus_behavior_recursive = Control.FOCUS_BEHAVIOR_DISABLED` 与 `mouse_behavior_recursive = Control.MOUSE_BEHAVIOR_DISABLED`，关框时改回 `FOCUS_BEHAVIOR_INHERITED` 与 `MOUSE_BEHAVIOR_INHERITED`。4.4 给框内按钮写 `focus_neighbor_*` 指向框内。确认框加到 `get_tree().root` 下自成一个根，没有这个问题
- 设置界面放在 CanvasLayer 里时，加到 `get_tree().root` 下的确认框画在它下面，鼠标也先点到设置界面。把确认框加到同一个 CanvasLayer 或层级更高的 CanvasLayer

确认框：

```gdscript
class_name DisplayConfirmDialog
extends Control

signal resolved(keep: bool)

const SECONDS := 15.0

@onready var _countdown: Label = %Countdown
@onready var _keep: Button = %KeepButton
var _timer: SceneTreeTimer


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_timer = get_tree().create_timer(SECONDS, true, false, true)
	_timer.timeout.connect(_resolve.bind(false))
	_keep.pressed.connect(_resolve.bind(true))
	_keep.grab_focus()


func _process(_delta: float) -> void:
	_countdown.text = tr("Reverting in %d s") % ceili(_timer.time_left)


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		_resolve(false)


func _resolve(keep: bool) -> void:
	if is_queued_for_deletion():
		return
	queue_free()
	resolved.emit(keep)
```

应用与还原：

```gdscript
extends Node

const SIZES: Array[Vector2i] = [Vector2i(1280, 720), Vector2i(1600, 900), Vector2i(1920, 1080), Vector2i(2560, 1440)]

@export var confirm_scene: PackedScene

var confirmed_mode := DisplayServer.WINDOW_MODE_WINDOWED
var confirmed_size := Vector2i(1280, 720)
var pending_mode := DisplayServer.WINDOW_MODE_WINDOWED
var pending_size := Vector2i(1280, 720)


func has_pending() -> bool:
	return pending_mode != confirmed_mode or pending_size != confirmed_size


func discard_pending() -> void:
	pending_mode = confirmed_mode
	pending_size = confirmed_size


func apply_pending() -> void:
	var mode := pending_mode
	var window_size := pending_size
	apply_window(mode, window_size)
	var dialog := confirm_scene.instantiate() as DisplayConfirmDialog
	dialog.resolved.connect(func(keep: bool) -> void:
		if keep:
			confirmed_mode = mode
			confirmed_size = window_size
		else:
			apply_window(confirmed_mode, confirmed_size)
		discard_pending()
	)
	get_tree().root.add_child(dialog)


func apply_window(mode: DisplayServer.WindowMode, window_size: Vector2i) -> void:
	if DisplayServer.window_get_mode() != mode:
		DisplayServer.window_set_mode(mode)
	if mode != DisplayServer.WINDOW_MODE_WINDOWED:
		return
	var sizes := windowed_sizes()
	var target: Vector2i = window_size if sizes.has(window_size) else sizes[-1]
	var window := get_window()
	window.size = target
	window.move_to_center()


func windowed_sizes() -> Array[Vector2i]:
	var screen := DisplayServer.window_get_current_screen()
	var work_area := DisplayServer.screen_get_usable_rect(screen).size
	var fitting: Array[Vector2i] = []
	for candidate: Vector2i in SIZES:
		if candidate.x < work_area.x and candidate.y < work_area.y:
			fitting.append(candidate)
	if fitting.is_empty():
		fitting.append(SIZES[0])
	return fitting
```

## 窗口的陷阱

- 先 `DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)` 再设尺寸。Windows 在全屏或最大化时直接忽略尺寸设置，macOS 在窗口铺满屏幕可用区时也忽略
- Windows 退出全屏会恢复进入全屏前的窗口位置和尺寸，切回窗口后再设一次尺寸并 `move_to_center()`
- `WINDOW_MODE_FULLSCREEN` 与 `WINDOW_MODE_EXCLUSIVE_FULLSCREEN` 都不改显示器的显示模式，全屏时窗口尺寸列表不影响渲染分辨率。全屏时把尺寸选项灰掉。降 3D 渲染分辨率用 `Viewport.scaling_3d_scale`，2D 和 UI 照常按窗口分辨率画。`Window.content_scale_factor` 只在 `Window.content_scale_mode` 为 `Window.CONTENT_SCALE_MODE_VIEWPORT` 时降低渲染分辨率，其他模式下它是界面缩放
- `WINDOW_MODE_EXCLUSIVE_FULLSCREEN` 在 Windows 上切换时可能黑屏片刻，切到别的程序也会触发一次切换
- 窗口尺寸列表只留严格小于 `DisplayServer.screen_get_usable_rect()` 的档位。usable rect 已扣掉任务栏，`Window.size` 是客户区，标题栏另占高度
- 存档里的尺寸不在当前屏幕的列表里时退到最大一档，换到小屏幕时窗口不会超出屏幕
- 无头模式没有屏幕，usable rect 是零，列表只剩兜底的一档

## 启动参数救不回存档

`--windowed` `--fullscreen` `--resolution` 由引擎自己消费，`OS.get_cmdline_args()` 里看不到。启动时套用存档的代码会覆盖它们，玩家没法靠启动参数救回黑屏。用 `--` 之后的自定义参数做恢复入口，从 `OS.get_cmdline_user_args()` 读：

```gdscript
extends Node

const SETTINGS_PATH := "user://settings.cfg"


func _ready() -> void:
	var config := ConfigFile.new()
	if config.load(SETTINGS_PATH) != OK:
		return
	# game.exe -- --reset-display
	if "--reset-display" in OS.get_cmdline_user_args() and config.has_section("display"):
		config.erase_section("display")
		config.save(SETTINGS_PATH)
```

## 失焦暂停

窗口模式游玩时点到窗口外，游戏不该继续跑。单机打开暂停菜单并暂停，联机只打开菜单。

```gdscript
extends Control

var _paused_by_menu := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	hide()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		open()


func open() -> void:
	if visible:
		return
	show()
	# 联机时世界照常运行
	if multiplayer.get_peers().is_empty() and not get_tree().paused:
		get_tree().paused = true
		_paused_by_menu = true


func close() -> void:
	hide()
	if _paused_by_menu:
		get_tree().paused = false
		_paused_by_menu = false
```

- `NOTIFICATION_APPLICATION_FOCUS_OUT` 在整个程序失去焦点时发，SceneTree 转发给所有节点。`NOTIFICATION_WM_WINDOW_FOCUS_OUT` 在同一程序的两个窗口间切换也会发，用它的话弹出原生子窗口就会误暂停
- 回到前台不自动继续，让玩家自己按继续
- 失焦时引擎释放按住的键和由非手柄输入按下的动作，鼠标按键状态不清。手柄事件照常到达，后台的手柄仍能操作游戏。4.7+ 可开 `input_devices/joypads/ignore_joypad_on_unfocused_application`
- 奖励选择框之类的模态界面挡住暂停菜单时，单机仍要单独暂停，回到前台时只恢复自己设的暂停
- 无头模式不会收到这个通知。测试里调 `get_tree().notification(MainLoop.NOTIFICATION_APPLICATION_FOCUS_OUT)` 模拟，节点收到的通知相同。4.7+ 这样调也会释放按键并把输入记为失焦，测完再发一次 `NOTIFICATION_APPLICATION_FOCUS_IN`。4.6 及更早释放按键在各平台的窗口代码里，手动发通知不释放
- 带窗口跑的自动化测试被点到别处也会暂停，给测试留一个关闭失焦暂停的开关
