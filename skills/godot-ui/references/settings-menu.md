# 设置界面

设置的生效与保存时机、底栏约定、窗口模式与尺寸的确认和还原、窗口陷阱、启动参数恢复入口、失焦暂停。音量换算见 godot-audio，键位重绑见 godot-input，`ConfigFile` 读写见 godot-resources-data。

## 生效与保存

改值当下生效，写盘时机二选一，整个设置界面保持一致：

| 做法 | 写盘 | 离开设置 | 取舍 |
|---|---|---|---|
| 离开即保存 | 离开设置界面时 | 直接离开 | 操作最少，改错只能手动改回或恢复默认 |
| 按应用保存 | 点应用时 | 有未保存改动时问应用、放弃、取消 | 可整体放弃，多一个按钮和一个弹框 |

| 规则 | 说明 |
|---|---|
| 窗口模式和尺寸 | 点应用才切换并倒计时确认，见下文 |
| 保存或放弃的时机 | 界面隐藏和退出场景树时，不每拖一格写一次 |
| 键位与窗口重设 | 与上次应用的值比对，变了才重设 |
| 恢复默认 | 只重置当前分页，先弹确认框，默认焦点在取消 |

- 返回键、Esc、宿主隐藏父节点走隐藏
- `queue_free`、切场景、退出程序只走退出场景树，不发 `NOTIFICATION_VISIBILITY_CHANGED`
- 不比对就重设时，拖音量滑块也重建 InputMap，并把玩家拖过的窗口拉回去

按应用保存的面板：

```gdscript
extends Control

signal leave_blocked

const SETTINGS_PATH := "user://settings.cfg"

var draft: Dictionary = {}
var _saved: Dictionary = {}
var _editing := false


func open(current: Dictionary) -> void:
	_saved = current.duplicate(true)
	draft = current.duplicate(true)
	_editing = true
	show()


func set_value(key: String, value: Variant) -> void:
	draft[key] = value
	_apply(draft)


func has_unsaved() -> bool:
	return draft != _saved


func apply() -> void:
	_save(draft)
	_saved = draft.duplicate(true)


func discard() -> void:
	draft = _saved.duplicate(true)
	_apply(draft)


func back() -> void:
	if has_unsaved():
		leave_blocked.emit()
		return
	hide()


func _notification(what: int) -> void:
	var closing := what == NOTIFICATION_VISIBILITY_CHANGED and not is_visible_in_tree()
	if (closing or what == NOTIFICATION_EXIT_TREE) and _editing:
		_editing = false
		if has_unsaved():
			discard()


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

```csharp
public partial class SettingsPanel : Control
{
    [Signal] public delegate void LeaveBlockedEventHandler();

    private const string SettingsPath = "user://settings.cfg";

    public Godot.Collections.Dictionary Draft { get; private set; } = new();
    private Godot.Collections.Dictionary _saved = new();
    private bool _editing;

    public void Open(Godot.Collections.Dictionary current)
    {
        _saved = current.Duplicate(true);
        Draft = current.Duplicate(true);
        _editing = true;
        Show();
    }

    public void SetValue(string key, Variant value)
    {
        Draft[key] = value;
        ApplyValues(Draft);
    }

    public bool HasUnsaved()
    {
        return !Draft.RecursiveEqual(_saved);
    }

    public void Apply()
    {
        Save(Draft);
        _saved = Draft.Duplicate(true);
    }

    public void Discard()
    {
        Draft = _saved.Duplicate(true);
        ApplyValues(Draft);
    }

    public void Back()
    {
        if (HasUnsaved())
        {
            EmitSignal(SignalName.LeaveBlocked);
            return;
        }
        Hide();
    }

    public override void _Notification(int what)
    {
        bool closing = what == NotificationVisibilityChanged && !IsVisibleInTree();
        if ((closing || what == NotificationExitTree) && _editing)
        {
            _editing = false;
            if (HasUnsaved())
            {
                Discard();
            }
        }
    }

    private void ApplyValues(Godot.Collections.Dictionary values)
    {
        int bus = AudioServer.GetBusIndex("Master");
        float volume = values.ContainsKey("master_volume") ? values["master_volume"].AsSingle() : 1.0f;
        AudioServer.SetBusVolumeLinear(bus, volume);
        AudioServer.SetBusMute(bus, volume <= 0.0f);
    }

    private void Save(Godot.Collections.Dictionary values)
    {
        var config = new ConfigFile();
        foreach (KeyValuePair<Variant, Variant> pair in values)
        {
            config.SetValue("settings", pair.Key.AsString(), pair.Value);
        }
        config.Save(SettingsPath);
    }
}
```

- `back()` 遇到未保存改动发 `leave_blocked`，由宿主弹框
- 宿主：应用选 `apply()` 再 `hide()`，放弃选 `discard()` 再 `hide()`
- 改成离开即保存：`_notification` 里 `discard()` 换成 `_save(draft)`，`back()` 直接 `hide()`
- GDScript 的 `Dictionary` 用 `==` `!=` 逐项比较，嵌套也比到底
- C# 的 `==` 比引用，内容比较用 RecursiveEqual
- 宿主强制关闭设置时按放弃处理

## 底栏与状态显示

常见约定，项目有自己的界面规范时以项目为准。

| 元素 | 约定 |
|---|---|
| 底栏按钮 | 常驻，不可用时置灰，不出现消失，免得相邻按钮移位 |
| 主按钮 | 同一时刻一个，按应用保存时是应用，无改动时置灰 |
| 恢复默认 | 放在离主按钮最远的一侧 |
| 已改动选项 | 改文字颜色，所在分类标签同样变色 |
| 选中状态 | 用底色或边框，与已改动各用一个通道 |
| 底栏手柄键位 | 写在按钮上，焦点在任一行都能直接触发 |
| 暂停键 | 不占用，设置界面里等同返回 |
| 返回键 | 在选项列表里也直接离开设置 |
| 分类切换 | 交给肩键或扳机 |
| 键位提示条 | 不重复底栏已标出的操作 |
| 说明栏 | 只放当前焦点选项的说明，没有就留空 |

- 已改动标记不插图标或文字，行高不变
- 返回先退回分类栏要按两次，第一次像没生效

## 窗口模式确认与还原

同操作系统的显示设置：改值只记下，点应用才切换并弹确认框，倒计时内不点保留就还原。

| 规则 | 原因或做法 |
|---|---|
| 改值不立即切窗口 | 翻选项时窗口来回切，每次弹一个确认框 |
| 只有窗口选项等应用 | 垂直同步、帧率上限、渲染倍率改值当下生效 |
| 只写已确认的值 | 倒计时中崩溃，下次启动仍是能用的设置 |
| 有未应用改动时离开 | 弹框问应用、放弃、取消 |
| 设置界面被强制关闭 | 丢掉未应用的窗口值，倒计时中的按还原 |
| 失焦时 | 继续倒计时，看不见画面只能靠超时还原 |

- 倒计时 `create_timer(15.0, true, false, true)`，暂停时照走
- 第 4 个参数让它不受 `Engine.time_scale` 影响
- 方向键导航在最近的根 Control 下找下一个焦点
- 父节点不是 Control、或设了 `top_level` 的 Control 自成一个根
- 确认框作为设置面板的子节点时，焦点会跳到框外

| 版本或位置 | 把焦点留在确认框里 |
|---|---|
| 4.5+ | 背后面板设 `focus_behavior_recursive` 与 `mouse_behavior_recursive` 为 DISABLED，关框改回 INHERITED |
| 4.4 | 框内按钮的 `focus_neighbor_*` 指向框内 |
| 加到 `get_tree().root` 下 | 自成一个根，没有这个问题 |
| 设置界面在 CanvasLayer 里 | 确认框加到同一个或更高的 CanvasLayer，否则画在下面 |

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

```csharp
public partial class DisplayConfirmDialog : Control
{
    [Signal] public delegate void ResolvedEventHandler(bool keep);

    private const double Seconds = 15.0;

    private Label _countdown;
    private Button _keep;
    private SceneTreeTimer _timer;

    public override void _Ready()
    {
        _countdown = GetNode<Label>("%Countdown");
        _keep = GetNode<Button>("%KeepButton");
        ProcessMode = ProcessModeEnum.Always;
        _timer = GetTree().CreateTimer(Seconds, true, false, true);
        _timer.Timeout += () => Resolve(false);
        _keep.Pressed += () => Resolve(true);
        _keep.GrabFocus();
    }

    public override void _Process(double delta)
    {
        _countdown.Text = Tr("Reverting in %d s").Replace("%d", Mathf.CeilToInt(_timer.TimeLeft).ToString());
    }

    public override void _Input(InputEvent @event)
    {
        if (@event.IsActionPressed("ui_cancel"))
        {
            GetViewport().SetInputAsHandled();
            Resolve(false);
        }
    }

    private void Resolve(bool keep)
    {
        if (IsQueuedForDeletion())
        {
            return;
        }
        QueueFree();
        EmitSignal(SignalName.Resolved, keep);
    }
}
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

```csharp
public partial class DisplaySettings : Node
{
    private static readonly Vector2I[] Sizes = { new(1280, 720), new(1600, 900), new(1920, 1080), new(2560, 1440) };

    [Export] public PackedScene ConfirmScene { get; set; }

    public DisplayServer.WindowMode ConfirmedMode { get; set; } = DisplayServer.WindowMode.Windowed;
    public Vector2I ConfirmedSize { get; set; } = new(1280, 720);
    public DisplayServer.WindowMode PendingMode { get; set; } = DisplayServer.WindowMode.Windowed;
    public Vector2I PendingSize { get; set; } = new(1280, 720);

    public bool HasPending()
    {
        return PendingMode != ConfirmedMode || PendingSize != ConfirmedSize;
    }

    public void DiscardPending()
    {
        PendingMode = ConfirmedMode;
        PendingSize = ConfirmedSize;
    }

    public void ApplyPending()
    {
        DisplayServer.WindowMode mode = PendingMode;
        Vector2I windowSize = PendingSize;
        ApplyWindow(mode, windowSize);
        var dialog = ConfirmScene.Instantiate<DisplayConfirmDialog>();
        dialog.Resolved += keep =>
        {
            if (keep)
            {
                ConfirmedMode = mode;
                ConfirmedSize = windowSize;
            }
            else
            {
                ApplyWindow(ConfirmedMode, ConfirmedSize);
            }
            DiscardPending();
        };
        GetTree().Root.AddChild(dialog);
    }

    public void ApplyWindow(DisplayServer.WindowMode mode, Vector2I windowSize)
    {
        if (DisplayServer.WindowGetMode() != mode)
        {
            DisplayServer.WindowSetMode(mode);
        }
        if (mode != DisplayServer.WindowMode.Windowed)
        {
            return;
        }
        List<Vector2I> sizes = WindowedSizes();
        Vector2I target = sizes.Contains(windowSize) ? windowSize : sizes[^1];
        Window window = GetWindow();
        window.Size = target;
        window.MoveToCenter();
    }

    public List<Vector2I> WindowedSizes()
    {
        int screen = DisplayServer.WindowGetCurrentScreen();
        Vector2I workArea = DisplayServer.ScreenGetUsableRect(screen).Size;
        var fitting = new List<Vector2I>();
        foreach (Vector2I candidate in Sizes)
        {
            if (candidate.X < workArea.X && candidate.Y < workArea.Y)
            {
                fitting.Add(candidate);
            }
        }
        if (fitting.Count == 0)
        {
            fitting.Add(Sizes[0]);
        }
        return fitting;
    }
}
```

## 窗口陷阱

| 现象 | 做法 |
|---|---|
| 全屏或最大化时设尺寸无效 | 先切 `DisplayServer.WINDOW_MODE_WINDOWED` 再设尺寸 |
| macOS 窗口铺满可用区时尺寸被忽略 | 同上，尺寸取严格小于可用区的档位 |
| Windows 退出全屏恢复成旧尺寸 | 切回窗口后再设一次尺寸并 `move_to_center()` |
| 全屏时改尺寸列表无效果 | 两种全屏都不改显示模式，全屏时把尺寸选项灰掉 |
| `WINDOW_MODE_EXCLUSIVE_FULLSCREEN` 切换黑屏片刻 | Windows 上切到别的程序也会触发一次 |
| 窗口超出屏幕 | 存档尺寸不在当前屏幕列表里时退到最大一档 |
| 无头模式尺寸列表只剩一档 | 无屏幕，usable rect 为零，属正常 |

- `DisplayServer.screen_get_usable_rect()` 已扣掉任务栏
- `Window.size` 是客户区，标题栏另占高度
- 降 3D 渲染分辨率用 `Viewport.scaling_3d_scale`，2D 和 UI 照常按窗口分辨率画
- `Window.content_scale_factor` 只在 `Window.CONTENT_SCALE_MODE_VIEWPORT` 下降渲染分辨率
- 其他 `Window.content_scale_mode` 下它是界面缩放

## 启动参数恢复入口

- `--windowed` `--fullscreen` `--resolution` 由引擎消费，`OS.get_cmdline_args()` 里没有
- 启动时套用存档会覆盖它们，玩家没法靠这些参数救回黑屏
- 恢复入口用 `--` 之后的自定义参数，从 `OS.get_cmdline_user_args()` 读

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

```csharp
public partial class DisplayReset : Node
{
    private const string SettingsPath = "user://settings.cfg";

    public override void _Ready()
    {
        var config = new ConfigFile();
        if (config.Load(SettingsPath) != Error.Ok)
        {
            return;
        }
        bool requested = System.Array.IndexOf(OS.GetCmdlineUserArgs(), "--reset-display") >= 0;
        if (requested && config.HasSection("display"))
        {
            config.EraseSection("display");
            config.Save(SettingsPath);
        }
    }
}
```

## 失焦暂停

窗口模式下点到窗口外：单机打开暂停菜单并暂停，联机只打开菜单。

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

```csharp
public partial class FocusPauseMenu : Control
{
    private bool _pausedByMenu;

    public override void _Ready()
    {
        ProcessMode = ProcessModeEnum.Always;
        Hide();
    }

    public override void _Notification(int what)
    {
        if (what == NotificationApplicationFocusOut)
        {
            Open();
        }
    }

    public void Open()
    {
        if (Visible)
        {
            return;
        }
        Show();
        if (Multiplayer.GetPeers().Length == 0 && !GetTree().Paused)
        {
            GetTree().Paused = true;
            _pausedByMenu = true;
        }
    }

    public void Close()
    {
        Hide();
        if (_pausedByMenu)
        {
            GetTree().Paused = false;
            _pausedByMenu = false;
        }
    }
}
```

| 通知 | 何时发 |
|---|---|
| `NOTIFICATION_APPLICATION_FOCUS_OUT` | 整个程序失去焦点，SceneTree 转发给所有节点 |
| `NOTIFICATION_WM_WINDOW_FOCUS_OUT` | 同一程序的窗口间切换也发，弹原生子窗口会误暂停 |

- 回到前台不自动继续，玩家自己按继续
- 失焦时引擎释放按住的键和非手柄输入按下的动作
- 鼠标按键状态不清
- 手柄事件照常到达，后台手柄仍能操作游戏
- 4.7+ 可开 `input_devices/joypads/ignore_joypad_on_unfocused_application`
- 模态界面挡住暂停菜单时单机仍要暂停，回前台只恢复自己设的暂停
- 带窗口跑的自动化测试留一个关闭失焦暂停的开关

无头模式收不到该通知，测试里手动发：

| 版本 | `get_tree().notification(MainLoop.NOTIFICATION_APPLICATION_FOCUS_OUT)` 的效果 |
|---|---|
| 4.7+ | 节点收到相同通知，并释放按键、记为失焦，测完发 `NOTIFICATION_APPLICATION_FOCUS_IN` |
| 4.6 及更早 | 节点收到通知，不释放按键 |
