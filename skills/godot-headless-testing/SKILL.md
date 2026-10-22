---
name: godot-headless-testing
description: 在终端里验证 Godot 4 改动，看不到编辑器时自己跑通。无头运行 headless、命令行参数 command line、--headless --import --check-only --quit-after --script、SceneTree 脚本、冒烟测试 smoke test、退出码 exit code、从输出判失败 SCRIPT ERROR Parse Error、模拟输入 Input.parse_input_event action_press、截图 screenshot xvfb、--write-movie 录帧、GUT gdUnit4、CI 下载 Godot 二进制、导出 --export-pack、查 API ClassDB doctool、C# dotnet build 后再跑。修完脚本报错要确认整个项目没有脚本错误、没有 GDScript 警告 warning、改完 GDScript、场景、C# 后想自己验证、写自动化测试、配 CI 时用
---

# Godot 无头测试与命令行验证

给在终端里工作的 AI 用：改完代码后用 Godot 命令行自己验证，不依赖编辑器。管命令行参数、判失败的规则、冒烟脚本、输入模拟、截图、CI。不管单个节点或 API 怎么用，那些去对应的领域 skill。

示例都在 4.7.2 编辑器版上实测过，`$GODOT_BIN` 指 Godot 可执行文件，`--no-header` 去掉版本头。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 查单个脚本语法 | `--headless --check-only -s x.gd`，退出码 0 或 1 | 正则或自写解析器 |
| 新增 class_name 或资源后 | `--headless --import` | 手改 `.godot/global_script_class_cache.cfg` |
| 跑主场景 N 帧后退出 | `--quit-after N`，配 `--fixed-fps 60` 可复现 | `sleep` 加 kill |
| 加载场景、断言、按结果退出 | SceneTree 脚本加 `quit(code)` | 自己拼 main 循环 |
| 引擎报错也算失败 | `OS.add_logger` 的 Logger 子类计数（4.5+） | 只靠 grep 或只靠退出码 |
| 传参给脚本 | `--` 之后的参数，`OS.get_cmdline_user_args()` 读 | 环境变量或写临时文件 |
| 按键、动作输入 | `Input.action_press`、`Input.parse_input_event` | 直接改节点状态冒充输入 |
| 看画面 | `xvfb-run`，Forward+ 用 `--rendering-driver vulkan`，Compatibility 用 `opengl3` | headless 下截图 |
| 录一段画面 | `--write-movie out/f.png` 或 `.avi`，同样要 xvfb | 循环截图 |
| 查类和方法是否存在 | `ClassDB.class_has_method`、类参考 XML | 凭记忆写 |
| 导出验证 | `--export-pack`，不需要模板 | 手动打 zip |
| 日志留档 | `--log-file 目录须已存在的路径` | `tee` 之外再造日志类 |
| 单元测试库 | GUT 或 gdUnit4，见 references/ci-and-frameworks.md | 自写断言框架 |

## 验证顺序

改完代码按这个顺序跑，前一步不过不进下一步：

1. 新增或改了 class_name、资源、自动加载、输入映射：`--import`
2. 每个改动的脚本 `--check-only`
3. 加载全部场景与脚本，看输出里的 ERROR。要求没有警告时先做下面的警告转错误
4. 冒烟脚本，覆盖改到的系统
5. 工程里有 GUT 或 gdUnit4 测试时跑它们

所有命令包进下面的函数。它做了四件事：外层 `timeout -s KILL` 防卡死，`</dev/null` 防调试器提示符等输入，去 ANSI 颜色，输出里有失败特征行时把退出码改成 1。

```bash
gdrun() {
	local log rc
	log=$(mktemp)
	timeout -s KILL "${GD_TIMEOUT:-60}" "${GODOT_BIN:-godot}" --headless --no-header --path "${GD_PROJECT:-.}" "$@" </dev/null >"$log" 2>&1
	rc=$?
	sed -i 's/\x1b\[[0-9;]*m//g' "$log"
	cat "$log"
	if [ "$rc" -eq 0 ] && grep -E 'SCRIPT ERROR|Parse Error|^ERROR:|Error importing|Debugger Break|handle_crash|^FAIL:|^LOAD_FAIL|^ENGINE_ERRORS' "$log" | grep -vqE 'resources still in use|RID allocations|singleton'; then
		rc=1
	fi
	rm -f "$log"
	return "$rc"
}

gdrun --import
gdrun --check-only -s scripts/player.gd
gdrun -s tests/load_all.gd
GD_TIMEOUT=120 gdrun -s tests/smoke_level.gd
```

实测每种情况的结果：

| 情况 | gdrun 退出码 | 特征输出 |
|---|---|---|
| 正常 | 0 | 脚本自己的 print |
| 解析错误 | 1 | `SCRIPT ERROR: Parse Error: ...` 加 `ERROR: Failed to load script` |
| 运行时错误后脚本没有走到 quit | 137 | `SCRIPT ERROR: Cannot call method ...`，随后被 KILL |
| `push_error` | 1 | `ERROR: ...` |
| 导入失败 | 1 | `ERROR: Error importing 'res://bad.png'.` |

排除 `resources still in use` 和 `RID allocations ... leaked at exit` 是因为脚本里 new 或 instantiate 出来的节点没释放时退出会打这两条 ERROR，同时有 `WARNING: ... ObjectDB instances were leaked`。测试脚本自己 `free()` 创建的节点就不会出现。

退出码规则详表和每个参数的实测见 references/cli-flags.md。

## 查 GDScript 警告

命令行运行默认不打印警告，输出干净不等于没有警告。加 `--debug` 虽然会打印，但解析错误时崩溃（134），运行时错误时停在 `debug>`，不用它。`tests/warn_as_error.gd` 在工程根生成 `override.cfg`，把等级为 Warn 的项都设成 Error，再运行就会让有警告的脚本报 `Warning treated as error`：

```gdscript
extends SceneTree

func _initialize() -> void:
	var cfg := ConfigFile.new()
	for p: Dictionary in ProjectSettings.get_property_list():
		var key: String = p["name"]
		if not key.begins_with("debug/gdscript/warnings/"):
			continue
		if typeof(ProjectSettings.get_setting(key)) == TYPE_INT and ProjectSettings.get_setting(key) == 1:
			cfg.set_value("debug", key.trim_prefix("debug/"), 2)
	cfg.save("res://override.cfg")
	quit()
```

```bash
gdrun -s tests/warn_as_error.gd
gdrun --quit-after 5
gdrun --check-only -s enemies/slime.gd
rm override.cfg
```

- 只有被加载的脚本才报，没挂进场景的脚本逐个 `--check-only`
- 默认关闭的项如 `untyped_declaration`、`return_value_discarded` 不在其中，要查就在 `override.cfg` 的 `[debug]` 下手写 `gdscript/warnings/名字=2`
- 项目目录只读时在副本里生成和运行，用完删掉 `override.cfg`，它对所有运行生效

## 冒烟脚本的写法

完整脚本在 references/smoke-scripts.md，包含 Logger 计数、看门狗、物理帧等待、输入。骨架：

```gdscript
extends SceneTree

var _failures: int = 0

func _check(ok: bool, msg: String) -> void:
	if not ok:
		_failures += 1
		printerr("FAIL: ", msg)

func _initialize() -> void:
	create_timer(30.0).timeout.connect(quit.bind(2))
	_run()

func _run() -> void:
	var level := (load("res://level.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await physics_frame
	for i: int in 10:
		await physics_frame
	_check(level.is_inside_tree(), "level in tree")
	level.queue_free()
	await process_frame
	quit(1 if _failures > 0 else 0)
```

要点：

- 继承 SceneTree，放 `_initialize` 里开始。自动加载节点在 `_initialize` 里已经是 `root` 的子节点，在 `_init` 里还没有
- `_initialize` 返回前 `root` 不在树内：自动加载节点和刚 `root.add_child` 的节点 `is_inside_tree()` 都是 false，`_ready` 没跑，`global_position`、`look_at` 这类依赖全局变换的调用报 `!is_inside_tree()`。遇到第一个 `await` 后才进树，要用就先 `await process_frame`
- 场景用 `root.add_child` 挂上去，进树后 `_ready` 才会跑
- 等帧用 `await physics_frame` 和 `await process_frame`，物理相关的断言等够物理帧再查
- 失败自己计数，最后 `quit(1)`。不用 `assert`
- 必须有看门狗：`create_timer(30.0).timeout.connect(quit.bind(2))`。协程里一行报错后面全不执行，没有它进程永远不退出
- 结尾 `queue_free` 创建的场景再等一帧，退出时才没有泄漏警告

## 模拟输入

```gdscript
extends SceneTree

func _initialize() -> void:
	Input.action_press("jump")
	print(Input.is_action_pressed("jump"))
	Input.action_release("jump")
	var ev := InputEventAction.new()
	ev.action = "ui_accept"
	ev.pressed = true
	Input.parse_input_event(ev)
	await process_frame
	quit()
```

- `Input.action_press` 当场生效，`parse_input_event` 要过一帧。两者读到的状态不同，写断言前先 `await`
- 动作名不在 InputMap 里时输出 `ERROR: The InputMap action "x" doesn't exist.`，状态恒为 false，工程里要先配好输入映射
- 无头下根窗口第一帧之后只有 64x64，坐标落在窗口外的鼠标点击点不到控件，`Button` 收不到 `pressed`。`await process_frame` 之后设 `root.size = Vector2i(1152, 648)` 就能点，`DisplayServer.window_set_size` 无效。点 UI 也可以用焦点加 `ui_accept`，或直接 `pressed.emit()`
- 按下之后记得发松开

## 看画面

headless 不渲染。要看画面用 xvfb 起一个真窗口：

```bash
xvfb-run -a -s "-screen 0 1280x720x24" "$GODOT_BIN" --path . --audio-driver Dummy --rendering-driver vulkan -s tests/shot.gd
```

脚本里 `await RenderingServer.frame_post_draw` 后 `root.get_texture().get_image().save_png(path)`，再用 Read 工具看图。装了 `mesa-vulkan-drivers`（lavapipe）时 `vulkan` 跑工程的 Forward+，`opengl3` 跑 Compatibility，都是 Mesa llvmpipe 软件渲染。没有 Vulkan 驱动时 `vulkan` 先打印 `ERROR: Required Vulkan instance extension VK_KHR_surface not found.` 再回退 OpenGL 3，按 ERROR 判失败的包装会判失败，CI 上要么装驱动要么改 `opengl3`。脚本见 references/smoke-scripts.md。

## 查 API

先看类参考 XML 和 `docs.godotengine.org/en/stable/classes/class_<小写类名>.html`。想在运行时确认成员存在：

```gdscript
extends SceneTree

func _initialize() -> void:
	print(ClassDB.class_has_method("Node", "queue_free"))
	print(ClassDB.class_get_signal_list("Timer", true).size())
	quit()
```

`godot --headless --doctool out/doc` 导出的 XML 说明文字是空的，只能确认签名。`--gdscript-docs` 能从自己脚本的 `##` 注释生成 XML。

## 陷阱

- 运行时 SCRIPT ERROR 不会让进程退出，也不改退出码。`-s` 脚本在报错的函数里中断，没走到 `quit()` 就一直卡着。每个命令都套 `timeout -s KILL`，脚本里放看门狗
- `--quit-after N` 到点退出码是 0，即使前面报过错。判失败要靠 grep 或 Logger 计数
- `assert` 失败和运行时错误一样，只打 `SCRIPT ERROR: Assertion failed` 并中断所在函数，退出码不变。`-s` 脚本在 `_initialize` 里断言失败，走不到 `quit()` 就卡住，只能 KILL。release 导出里 `assert` 整条被忽略。测试里不用 `assert`
- `-d` 在脚本报错时停在 `debug>` 提示符。stdin 是 `/dev/null` 时读到 EOF：运行时错误直接退出，退出码 0，解析错误崩溃（134）。命令行不要带 `-d`，输入重定向到 `/dev/null`，`gdrun` 靠 `Debugger Break` 兜底
- `load()` 一个缺 `ext_resource` 的 `.tscn` 仍返回非 null 的 PackedScene，只在输出里报 ERROR。别只检查 null
- `--import` 打开工程后退出码恒为 0，导入错误和脚本语法错误都一样。路径无效或没有 `project.godot` 时才是 1。导入错误只在第一次打印，之后 `.import` 里记 `valid=false` 不再报
- class_name 要先 `--import` 才进全局缓存。`--quit` 不导入也不建 `.godot`。没 import 就跑会报 `Identifier "X" not declared in the current scope`，类型标注处报 `Could not find type "X" in the current scope`。这是缓存缺失，不要删类型标注或改 preload
- `--check-only` 不认自动加载：引用 autoload 名的脚本会报 `Identifier not found`，是误报。SceneTree 脚本本身也不能用 autoload 名，要 `root.get_node("名字")`，在 `_initialize` 里它的 `_ready` 还没跑，调用方法放到 `await process_frame` 之后
- `--quit-after` 数的是 process 帧，不是物理帧。要两者对齐加 `--fixed-fps 60`
- `parse_input_event` 的按键过一帧才生效，`Input.action_press` 立即生效
- headless 下 `get_texture().get_image()` 返回 null，`await RenderingServer.frame_post_draw` 永远不触发，`--write-movie` 段错误。截图和录像必须 xvfb
- `--write-movie`、`--log-file` 的输出目录必须已存在
- 标准版 Godot 不加载 `.cs`。C# 要 mono 版加 `dotnet build`，没构建就跑会卡住。见 references/ci-and-frameworks.md
- 命令行运行 GDScript 警告默认不打印，无头和 xvfb 都一样，`--check-only` 也不报，只有 `--debug` 会打印。想让警告变失败，按上一节生成 `override.cfg`，用完删除
- grep `ERROR:` 会命中几种无害行：退出时 `resources still in use` 与 `RID allocations ... leaked at exit`，xvfb 不加 `--audio-driver Dummy` 时的 ALSA 报错，mono 版 `--import` 的 `Parameter "singleton" is null`。grep `WARNING:` 还会命中 xvfb 下 `opengl3` 的 `Could not set V-Sync mode`。要排除就具体排除，不要整类忽略
- 退出时的 `WARNING: N ObjectDB instances were leaked` 说明测试脚本创建的节点没 `free`，不是引擎问题，加 `--verbose` 看 `Leaked instance`
- `--log-file` 不会让终端静默，两边都有输出

## 参考

- references/cli-flags.md：每个参数的作用与实测输出、退出码表、渲染驱动实测
- references/smoke-scripts.md：冒烟脚本全文、加载全部场景、check-only 循环、点按钮、截图、运行时查 API
- references/ci-and-frameworks.md：下载 Godot 的 URL、导出、C# 流程、GUT 与 gdUnit4 命令行
- https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html
- https://docs.godotengine.org/en/stable/classes/class_scenetree.html
