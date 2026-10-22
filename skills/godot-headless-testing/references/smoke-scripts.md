# 可直接用的脚本

代码块都在 4.7.2 上跑通过。放在工程的 `tests/` 目录，与游戏脚本分开。

## 冒烟脚本

加载场景，跑若干物理帧，断言，按失败数退出。Logger 子类把引擎报错也计入失败，所以 SCRIPT ERROR 不会被漏掉。Logger 与 ScriptBacktrace 是 4.5+，4.4 上去掉计数类改用 grep。

```gdscript
extends SceneTree

class ErrorCounter extends Logger:
	var count: int = 0
	var _mutex := Mutex.new()

	func _log_error(_function: String, _file: String, _line: int, _code: String, _rationale: String, _editor_notify: bool, error_type: int, _script_backtraces: Array[ScriptBacktrace]) -> void:
		if error_type != Logger.ERROR_TYPE_WARNING:
			_mutex.lock()
			count += 1
			_mutex.unlock()

var _errors := ErrorCounter.new()
var _failures: int = 0
var _done: bool = false

func _check(ok: bool, msg: String) -> void:
	if not ok:
		_failures += 1
		printerr("FAIL: ", msg)

func _initialize() -> void:
	OS.add_logger(_errors)
	create_timer(30.0).timeout.connect(_finish.bind(2))
	_run()

func _run() -> void:
	var level := (load("res://level.tscn") as PackedScene).instantiate()
	root.add_child(level)
	var player := level.get_node("Player") as CharacterBody2D
	await physics_frame
	Input.action_press("right")
	for i: int in 10:
		await physics_frame
	Input.action_release("right")
	_check(player.position.x > 10.0, "player moved, x=%s" % player.position.x)
	level.queue_free()
	await process_frame
	_finish(0)

func _finish(code: int) -> void:
	if _done:
		return
	_done = true
	if _errors.count > 0:
		printerr("ENGINE_ERRORS ", _errors.count)
		code = 1
	if _failures > 0:
		code = 1
	if code == 2:
		printerr("TIMEOUT")
	quit(code)
```

- 30 秒的 `create_timer` 是看门狗。`_run` 里任何一行报错，整个协程会被中断而 `_finish(0)` 永远不执行，没有看门狗进程就卡住
- `_run` 在 `_initialize` 里不 await 地调用，协程在第一个 await 处交还控制权
- 用 `_initialize` 不用 `_init`：自动加载节点在 `_initialize` 里已经是 `root` 的子节点，`_init` 里还没有
- `_initialize` 返回前 `root` 不在树内，自动加载节点和 `root.add_child` 的节点 `is_inside_tree()` 为 false，`_ready` 没跑。第一个 `await` 之后才进树，`global_position`、`look_at` 这类依赖全局变换的调用放在它之后
- 不用 `assert`：失败只打 `SCRIPT ERROR: Assertion failed` 并中断所在函数，退出码不变，release 导出里整条被忽略
- `_log_error` 可能在其他线程调用，所以计数加了 `Mutex`
- 运行 `bash` 命令见 SKILL.md 的 `gdrun`

## 加载全部场景与脚本

遍历工程，逐个 `load`。缺失 `ext_resource` 的场景仍然返回非 null，所以检查输出里的 ERROR 才是判据，null 检查只能抓到文件不存在这类情况。

```gdscript
extends SceneTree

func _initialize() -> void:
	var failed: int = 0
	var paths := _collect("res://")
	for path: String in paths:
		if path == get_script().resource_path:
			continue
		var res := load(path)
		if res == null:
			printerr("LOAD_FAIL ", path)
			failed += 1
	print("loaded ", paths.size(), " files")
	quit(1 if failed > 0 else 0)

func _collect(dir_path: String) -> PackedStringArray:
	var out := PackedStringArray()
	for f: String in DirAccess.get_files_at(dir_path):
		if f.get_extension() in ["tscn", "scn", "gd", "tres"]:
			out.append(dir_path.path_join(f))
	for d: String in DirAccess.get_directories_at(dir_path):
		if not d.begins_with(".") and d != "addons":
			out.append_array(_collect(dir_path.path_join(d)))
	return out
```

- 跳过自己：用 `CACHE_MODE_IGNORE` 加载正在运行的这个脚本会段错误，其余文件传这个模式没问题
- 导出后 `res://` 下的 `.tscn` 变成 `.tscn.remap`，这个脚本只在源工程里用
- 报错行是 `ERROR: res://broken.tscn:6 - Parse Error: [ext_resource] referenced non-existent resource at: res://missing.gd.`

## 逐个脚本 check-only

`--check-only` 每次只解析一个脚本，每个 0.3 到 0.5 秒。

```bash
export GODOT_BIN=godot
fail=0
for f in $(find . -name '*.gd' -not -path './addons/*' -not -path './.godot/*'); do
	out=$($GODOT_BIN --headless --no-header --path . --check-only -s "$f" 2>&1 </dev/null)
	if [ $? -ne 0 ]; then
		echo "$out"
		fail=1
	fi
done
exit $fail
```

引用了自动加载名的脚本会误报 `Compile Error: Identifier not found: G`，真实场景里它是合法的。这类脚本改用「加载全部场景」那个脚本验证，因为场景实例化走的是运行时环境。

新加了 class_name 的脚本被其他脚本引用时，先 `--import`，否则报 `Identifier "Unit" not declared in the current scope`。

## 点按钮与按键

```gdscript
extends SceneTree

var hits: int = 0

func _initialize() -> void:
	var b := Button.new()
	b.size = Vector2(80, 30)
	b.pressed.connect(func() -> void: hits += 1)
	root.add_child(b)
	await process_frame
	b.grab_focus()
	var press := InputEventAction.new()
	press.action = "ui_accept"
	press.pressed = true
	Input.parse_input_event(press)
	await process_frame
	var release := InputEventAction.new()
	release.action = "ui_accept"
	release.pressed = false
	Input.parse_input_event(release)
	await process_frame
	b.pressed.emit()
	print("hits=", hits)
	b.queue_free()
	quit(0 if hits == 2 else 1)
```

| 做法 | headless | xvfb 窗口 |
|---|---|---|
| 焦点加 `ui_accept` 的 InputEventAction | 可用 | 可用 |
| 直接 emit 按钮信号 | 可用 | 可用 |
| `Input.parse_input_event` 发鼠标按下与松开 | 坐标在根窗口内可用，窗口外 0 次 | 可用 |
| `root.push_input` 发鼠标事件 | 同上 | 可用 |

headless 的根窗口第一帧之后只有 64x64，窗口外的坐标进不了 hover，那里的 Button 不响应。第一帧之后设 `root.size = Vector2i(1152, 648)` 即可，在 `_initialize` 里设会被第一帧改回。发鼠标事件时先发一个 `InputEventMouseMotion` 再发按下和松开，各等一帧。

动作输入的时机：

- `Input.action_press("jump")` 立即生效，同一帧里 `Input.is_action_pressed` 就是 true
- `Input.parse_input_event` 发 `InputEventKey` 要等下一帧才被 `Input.is_action_pressed` 看到，实测一个物理帧之后速度才变
- `InputEventAction` 经 `Input.parse_input_event` 发出后，等 2 个物理帧，`_physics_process` 里的 `Input.is_action_just_pressed` 读到 true
- 动作名不在 InputMap 里会打 `ERROR: The InputMap action "x" doesn't exist.`，状态为 false
- 发完按下记得再发松开，或调用 `Input.action_release`，否则状态残留到后面的断言

## 截图

只能在非 headless 下。

```gdscript
extends SceneTree

func _initialize() -> void:
	var level := (load("res://level.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	var err := img.save_png("res://shot.png")
	print("size=", img.get_size(), " save=", err, " adapter=", RenderingServer.get_video_adapter_name())
	quit(0 if err == OK else 1)
```

```bash
xvfb-run -a -s "-screen 0 1280x720x24" godot --path . --audio-driver Dummy --rendering-driver vulkan -s tests/shot.gd
```

`vulkan` 需要 `mesa-vulkan-drivers`，实测输出里有 `Vulkan 1.4.318 - Forward+ - Using Device #0: Unknown - llvmpipe`、`size=(1152, 648)`、`save=0`。换成 `opengl3` 是 Compatibility，输出 `OpenGL API 4.5 (Core Profile) Mesa ... Compatibility - Using Device: Mesa - llvmpipe`。图用 Read 工具直接看。

多帧录像：

```bash
xvfb-run -a -s "-screen 0 1280x720x24" godot --path . --audio-driver Dummy --rendering-driver opengl3 res://level.tscn --write-movie out/f.png --fixed-fps 30 --quit-after 60
```

`out/` 目录须已存在。得到 `f00000000.png` 起的序列帧和 `f.wav`。

## 运行时查 API

```gdscript
extends SceneTree

func _initialize() -> void:
	print(ClassDB.class_exists("Tween"))
	print(ClassDB.class_has_method("CharacterBody2D", "move_and_slide", true))
	print(ClassDB.class_get_signal_list("Timer", true).map(func(d: Dictionary) -> String: return d.name))
	print(ClassDB.class_get_property_list("Camera2D", true).map(func(d: Dictionary) -> String: return d.name))
	print(ClassDB.class_get_enum_constants("Node", "ProcessMode"))
	print(ProjectSettings.has_setting("rendering/textures/canvas_textures/default_texture_filter"))
	quit()
```

实测输出：`true`、`true`、`["timeout"]`、`["offset", "anchor_mode", "ignore_rotation", ...]`（属性列表里夹着属性分组名）、`["PROCESS_MODE_INHERIT", "PROCESS_MODE_PAUSABLE", ...]`、`true`。第三个参数 `true` 表示不含继承来的成员。

- `ClassDB` 只认原生类。脚本里定义的方法用 `Object.has_method` 或 `Script.get_script_method_list`
- 一次查几十个名字时，先把名字列表写进脚本，输出 `MISSING 名字`，比逐个跑命令快
- `godot --doctool` 导出的 XML 没有说明文字，只能确认成员存在和签名，说明文字去 `docs.godotengine.org/en/stable/classes/class_<小写类名>.html`
