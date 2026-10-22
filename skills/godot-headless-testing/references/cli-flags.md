# 命令行参数与实测输出

版本 4.7.2 编辑器版实测。`godot --help` 为准，参数标注 R 的在导出模板里也有，E 只在编辑器版有，X 需要编辑器版或 `disable_path_overrides=false` 的模板。下文的 `$G` 指 Godot 可执行文件，`P` 指工程目录。

## 运行类

| 参数 | 作用 | 实测 |
|---|---|---|
| `--headless` | 等于 `--display-driver headless --audio-driver Dummy` | 没有渲染，见下文渲染一节 |
| `--path P` | 指定含 project.godot 的目录 | `-s` 的相对路径按 P 解析 |
| `--no-header` | 不打印版本头 | 无头下少一行，grep 更干净 |
| `--quit` | 第一次主循环迭代后退出 | 要有主场景或场景参数，否则报 `no main scene defined in the project` 退出码 1。有场景时退出码 0，不触发导入，`.godot` 不会被创建 |
| `--quit-after N` | N 次主循环迭代后退出，0 为不限 | 计的是 process 帧。N=30 时物理帧数随机器速度变，实测 12 到 20，与 process 帧不对齐。退出码 0，脚本出错也是 0 |
| `--fixed-fps F` | 固定步长，关闭实时同步 | `--fixed-fps 60 --quit-after 60` 得 60 个 process 帧和 60 个物理帧，可复现 |
| `--scene PATH` 或位置参数 | 运行指定场景 | `godot --path P res://main.tscn --quit-after 3` 可用。场景不存在时退出码 1 |
| `-s`, `--script F` | 运行脚本 | 须继承 SceneTree 或 MainLoop，否则输出 `Can't load the script ... as it doesn't inherit from SceneTree or MainLoop.` 退出码 1。路径可写 `res://x.gd` 或相对工程的 `x.gd` |
| `--check-only` | 与 `-s` 连用，只解析 | 通过时无输出退出码 0，失败时退出码 1 |
| `--main-loop NAME` | 运行指定全局类名的 MainLoop | 同时给 `-s` 时 `-s` 生效。单独用要有主场景或场景参数。工程设置 `application/run/main_loop_type` 等价 |
| `--` 或 `++` | 其后是用户参数 | `OS.get_cmdline_user_args()` 只返回分隔符之后的部分 |
| `--log-file F` | 日志写到文件 | 终端仍照常输出。F 的目录须已存在，否则报 `Failed to open log file for writing` |
| `-v`, `--verbose` | 详细输出 | 多出初始化细节与加载日志，退出时列出泄漏对象 `Leaked instance: Node:...` |
| `--print-fps` | 打印 fps | |
| `--audio-driver Dummy` | 不开声卡 | 非 headless 的 xvfb 下不加会出一堆 ALSA 报错，之后回退 Dummy |
| `-d`, `--debug` | 本地调试器 | 脚本报错时停在 `Debugger Break ... debug>` 提示符。stdin 是 `/dev/null` 时运行时错误退出码 0，解析错误崩溃，不要在无人值守的运行里用 |

`OS.get_cmdline_args()` 返回的只有引擎没消费的参数，例如 `["-s", "scripts/hello.gd"]`，用户参数用 `OS.get_cmdline_user_args()`。

## 工具类

| 参数 | 作用 | 实测 |
|---|---|---|
| `--import` | 启动编辑器核心，导入资源并重建 class_name 缓存后退出 | 空工程 8 到 14 秒，之后更快。打开工程后退出码恒为 0，导入错误和脚本语法错误都一样。路径无效或没有 `project.godot` 时为 1 |
| `--editor --quit` | 同样会导入 | 输出与 `--import` 相同，用 `--import` 即可 |
| `--export-release P F` | 按预设 P 导出到 F | 目录须已存在。缺导出模板或预设名不存在时退出码 1 |
| `--export-debug P F` | 同上，用 debug 模板 | |
| `--export-pack P F` | 只导出数据包，扩展名 pck 或 zip | 不需要导出模板，成功时退出码 0 |
| `--doctool [D]` | 把引擎 API 导出为 XML | 1 秒左右。只含签名，description 全是空的 |
| `--doctool D --gdscript-docs res://dir` | 从 GDScript 的 `##` 注释生成 XML | 输出 `Class.xml`，含 brief_description 与参数 |
| `--no-docbase` | 与 `--doctool` 连用，不导出基础类型 | |
| `--build-solutions` | 构建 C# 工程 | 用于 mono 版，标准版上无事可做，退出码 0。C# 编译失败时退出码 1，输出 `An EditorPlugin build callback failed` |
| `--dump-extension-api` | 导出 GDExtension 用的 extension_api.json | 当前目录 |
| `--validate-extension-api F` | 与旧版 API 比对 | 有不兼容时退出码非 0 |
| `--convert-3to4` | Godot 3 工程迁移 | |

`--import` 的标准输出是带 ANSI 颜色的进度行，`NO_COLOR` 不生效，用 `sed 's/\x1b\[[0-9;]*m//g'` 去掉。实际有信息的是不以 `[` 开头的行：

```
[ DONE ] first_scan_filesystem
WARNING: Not a PNG file
ERROR: Error importing 'res://bad.png'.
```

导入错误只在第一次打印。之后 `bad.png.import` 里记着 `valid=false`，再跑 `--import` 不再报，退出码仍是 0。排查导入问题时先删掉对应的 `.import` 文件和 `.godot`。

`--import` 会补写缺失的 `.uid` 文件，改完提交时带上。

## 退出码

| 情况 | 退出码 |
|---|---|
| `-s` 脚本解析失败 | 1 |
| `--check-only` 解析失败 | 1 |
| `quit(n)` 或 `get_tree().quit(n)` | n |
| 运行时 SCRIPT ERROR | 不变。进程继续跑，所在函数被中断 |
| `push_error`、`push_warning`、`printerr` | 0 |
| `assert` 失败 | 不变，同运行时 SCRIPT ERROR。`-s` 脚本走不到 `quit()` 时卡住，只能被 `timeout -s KILL` 杀掉 |
| `--quit-after` 到点 | 0 |
| 外层 `timeout N` 到点 | 124 |
| 外层 `timeout -s KILL N` 到点 | 137 |
| 引擎崩溃 | 139 或 134，输出含 `handle_crash: Program crashed` |
| `--import` | 0，路径无效或没有 `project.godot` 时 1 |
| 导出失败 | 1 |
| `--build-solutions` C# 编译失败 | 1 |

## 输出里要认的行

```
SCRIPT ERROR: Parse Error: Identifier "Unit" not declared in the current scope.
          at: GDScript::reload (res://scripts/use.gd:4)
ERROR: Failed to load script "res://scripts/use.gd" with error "Parse error".
SCRIPT ERROR: Cannot call method 'queue_free' on a null value.
          at: _init (res://scripts/rt_err.gd:5)
SCRIPT ERROR: Assertion failed: math broke
ERROR: res://broken.tscn:6 - Parse Error: [ext_resource] referenced non-existent resource at: res://missing.gd.
WARNING: 3 ObjectDB instances were leaked at exit (run with `--verbose` for details).
ERROR: 1 resources still in use at exit (run with --verbose for details).
Debugger Break, Reason: 'Cannot call method ...'
handle_crash: Program crashed with signal 11
```

- 所有这些都写到 stderr，解析错误也是。用 `2>&1` 合并后再 grep
- 报错的位置在下一行的 `at:` 里，格式 `at: 函数 (res://路径:行号)`
- 退出时的 `ObjectDB instances were leaked` 是 WARNING，`resources still in use` 和 `RID allocations ... leaked at exit` 是 ERROR。测试脚本里 new 或 instantiate 出节点之后 `free()`，这些都会消失
- 解析错误会成对出现，一条短描述加一条带变量名的长描述

## 警告当错误

命令行运行里 GDScript 警告（等级 1）不打印，无头和 xvfb 都一样，`--check-only` 也不报。要让警告变失败，把对应项设为 2（Error）。不改工程文件的办法是在工程根目录放 `override.cfg`：

```ini
[debug]

gdscript/warnings/untyped_declaration=2
gdscript/warnings/unused_variable=2
```

实测 `--check-only -s w.gd` 输出 `Parse Error: Function "f()" has no static return type. (Warning treated as error.)` 并退出码 1。用完删掉 `override.cfg`，它对所有运行生效。

## 渲染

| 场景 | 结果 |
|---|---|
| `--headless` 下 `root.get_texture().get_image()` | 返回 null，打印 `ERROR: Parameter "t" is null.`，位置在 `dummy/storage/texture_storage.h` |
| `--headless` 下 `await RenderingServer.frame_post_draw` | 永远不触发，脚本卡住 |
| `--headless --write-movie x.png` | 段错误，留下空的 wav |
| `xvfb-run -a -s "-screen 0 1280x720x24" $G --rendering-driver opengl3` | 可用。本机用 Mesa llvmpipe，输出 `OpenGL API 4.5 (Core Profile) Mesa ... Compatibility - Using Device: Mesa - llvmpipe`，渲染方法为 gl_compatibility |
| 同上用 `--rendering-driver vulkan` | 装了 `mesa-vulkan-drivers`（lavapipe）时输出 `Vulkan 1.4.318 - Forward+ - Using Device #0: Unknown - llvmpipe`，`get_current_rendering_method()` 为 `forward_plus`。没有 Vulkan 驱动时先打印 `ERROR: Required Vulkan instance extension VK_KHR_surface not found.`，再警告 `switching to OpenGL 3` 并回退 Compatibility，输出里的 ERROR 行会让按 ERROR 判失败的包装失败 |
| xvfb 下 `--write-movie out/f.png --fixed-fps 30 --quit-after 5` | 生成 `f00000000.png` 到 `f00000004.png` 和 `f.wav`，结尾打印 `5 frames at 30 FPS` |
| xvfb 下 `--write-movie out/m.avi` | 生成 avi。用 `ffmpeg -i m.avi -vf "select=eq(n\,10)" -vframes 1 f.png` 抽帧 |
| xvfb 下的 `RenderingServer.get_video_adapter_name()` | `llvmpipe (LLVM 20.1.2, 256 bits)` |

截图尺寸取工程的 `display/window/size/viewport_width` 与 `display/window/size/viewport_height`，默认 1152x648，与 xvfb 屏幕大小无关。`opengl3` 下 Forward+ 工程按 Compatibility 渲染，截图里没有 Forward+ 才有的效果，要看这些效果用 `vulkan`。

`--write-movie` 会强制 `--fixed-fps`，未指定时为 60。`--quit-after` 决定写多少帧。
