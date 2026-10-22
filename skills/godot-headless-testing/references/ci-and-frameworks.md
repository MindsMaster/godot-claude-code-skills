# CI、导出、C# 与测试框架

## 下载 Godot 二进制

GitHub releases 上的资源名规律，4.7.2 逐个用 curl 验证过（HTTP 302 跳到 release-assets，最终 200）：

| 用途 | 文件名 |
|---|---|
| 标准版 Linux | `Godot_v4.7.2-stable_linux.x86_64.zip` |
| mono 版 Linux | `Godot_v4.7.2-stable_mono_linux_x86_64.zip` |
| 标准版导出模板 | `Godot_v4.7.2-stable_export_templates.tpz` |
| mono 版导出模板 | `Godot_v4.7.2-stable_mono_export_templates.tpz` |

URL 前缀 `https://github.com/godotengine/godot/releases/download/4.7.2-stable/`。`godotengine/godot-builds` 仓库有同名资源。把版本号换成其他稳定版时目录名是 `<版本>-stable`，文件名里是 `v<版本>-stable`。

zip 内容不同：

- 标准版：一个文件 `Godot_v4.7.2-stable_linux.x86_64`
- mono 版：目录 `Godot_v4.7.2-stable_mono_linux_x86_64/`，里面可执行文件叫 `Godot_v4.7.2-stable_mono_linux.x86_64`（下划线变点），旁边有 `GodotSharp/` 目录。可执行文件必须与 `GodotSharp/` 同目录

```bash
V=4.7.2
curl -fsSL -o godot.zip "https://github.com/godotengine/godot/releases/download/${V}-stable/Godot_v${V}-stable_linux.x86_64.zip"
unzip -q godot.zip
chmod +x "Godot_v${V}-stable_linux.x86_64"
export GODOT_BIN="$PWD/Godot_v${V}-stable_linux.x86_64"
"$GODOT_BIN" --version
```

`--version` 输出 `4.7.2.stable.official.ed1daf0bf`，mono 版是 `4.7.2.stable.mono.official.ed1daf0bf`，脚本里可以用后缀判断是否 mono。

CI 里的顺序：下载，`--import`，`--check-only` 循环，冒烟脚本，失败时上传日志。下面的 YAML 外壳没有在 Actions 上实跑过，命令本身在本机验证过。

```yaml
steps:
  - uses: actions/checkout@v4
  - name: Fetch Godot
    run: |
      V=4.7.2
      curl -fsSL -o godot.zip "https://github.com/godotengine/godot/releases/download/${V}-stable/Godot_v${V}-stable_linux.x86_64.zip"
      unzip -q godot.zip
      chmod +x "Godot_v${V}-stable_linux.x86_64"
      echo "GODOT_BIN=$PWD/Godot_v${V}-stable_linux.x86_64" >> "$GITHUB_ENV"
  - run: $GODOT_BIN --headless --no-header --path . --import
  - run: timeout -s KILL 120 $GODOT_BIN --headless --no-header --path . -s tests/smoke_level.gd
```

## 导出

```bash
mkdir -p build
godot --headless --no-header --path . --export-pack "Linux" build/game.pck
godot --headless --no-header --path . --export-release "Linux" build/game.x86_64
```

- `export_presets.cfg` 必须在工程根目录，预设名与第一个参数完全一致。不存在时退出码 1
- `--export-pack` 不需要导出模板，实测退出码 0，输出 `[ DONE ] savepack` 和一串 `Storing File:`
- `--export-release` 和 `--export-debug` 需要模板。缺失时输出 `No export template found at the expected path:` 后面跟路径，退出码 1。本机标准版的路径是 `~/.local/share/godot/export_templates/4.7.2.stable/linux_release.x86_64`，以报错里打印的路径为准
- 输出目录须已存在
- 导出后 `res://` 里的场景变成 `.remap`，运行时靠资源加载器透明处理，用 `DirAccess` 扫目录的代码会在导出后失效，这类问题只有跑导出包才能发现

## C# 工程

下文 `godot_mono` 指 mono 版可执行文件。标准版 Godot 不加载 `.cs`：运行带 C# 脚本的场景输出 `ERROR: No loader found for resource: res://Hello.cs (expected type: Script)`。必须用 mono 版，且先构建：

```bash
dotnet build
godot_mono --headless --no-header --path . --import
godot_mono --headless --no-header --path . main.tscn --quit-after 30
```

实测：

- `dotnet build` 在 `Godot.NET.Sdk/4.7.2` 的工程上首次约 9 秒，之后约 2 秒。编译错误输出 `Hello.cs(8,17): error CS0029: ...`，退出码 1
- 先 `dotnet build` 再运行，`GD.Print` 的输出和 `GetTree().Quit(4)` 的退出码 4 都正常
- 没构建就运行：输出 `Cannot instantiate C# script because the associated class could not be found`，之后进程卡住，需要 `timeout -s KILL`
- 找不到 dotnet：输出 `Unable to load .NET runtime, specifically hostfxr` 后崩溃（134）。设 `DOTNET_ROOT` 并把 dotnet 放进 `PATH`
- 也可以 `godot_mono --headless --path . --build-solutions --quit` 代替 `dotnet build`，编译失败时退出码 1，输出 `ERROR: An EditorPlugin build callback failed.`
- mono 版 `--import` 的输出里有 `ERROR: Parameter "singleton" is null.`（`is_cmdline_mode`），无害，grep 时排除

C# 的断言写法与 GDScript 一样：自己计数，`GetTree().Quit(code)`。C# 通用规则见 godot-csharp。

## 测试框架

没有框架也能测，本 skill 的冒烟脚本够用。需要断言库、参数化、Mock 时再引入。

| | GUT | gdUnit4 |
|---|---|---|
| 用途 | 用 GDScript 写测试的单元测试框架 | 支持 GDScript 与 C# 的测试框架，带编辑器内检视面板 |
| 4.7 对应版本 | 9.7.1（README 里标 4.7.x，分支 godot_4_7） | 6.2.x 的 README 兼容表含 4.7 与 4.7.1 |
| 安装 | 把 `addons/gut` 放进工程并启用插件，重启编辑器 | 同样放进 `addons/` 并启用插件 |
| 命令行入口 | `addons/gut/gut_cmdln.gd` | `addons/gdUnit4/runtest.sh`，内部调 `res://addons/gdUnit4/bin/GdUnitCmdTool.gd` |

GUT 命令行，选项来自其文档的 `-gh` 帮助输出：

```bash
godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://test -gexit
```

- `-gdir` 测试目录，`-ginclude_subdirs` 含子目录，`-gtest` 指定脚本，`-gselect` 按文件名过滤，`-gunit_test_name` 按测试名过滤
- `-gexit` 跑完退出，不加会一直开着
- 退出码：全过为 0，有失败为 1，pending 不影响
- 选项也可以放 `res://.gutconfig.json`
- 官方文档示例用了 `-d`。`-d` 在脚本报错时会停在 `debug>` 提示符，无人值守时去掉它。这条命令行没有在本机跑过，因为本机没装 GUT

gdUnit4 命令行，选项来自其文档的 `-help` 输出：

```bash
export GODOT_BIN=/path/to/godot
./addons/gdUnit4/runtest.sh -a ./test
```

- `-a` 加测试目录或套件，可重复。`-i` 忽略某套件或用例，`-c` 失败后继续（默认第一个失败就中止），`-conf` 指定配置文件
- 退出码：全过为 0，有失败为 100，有警告为 101。`gdrun` 之类只认 0 的包装要把 101 单独处理
- `runtest.sh` 读 `GODOT_BIN` 或 `--godot_binary`，检测到 mono 版会先执行 `dotnet build --debug`
- 6.2.0 起它启动 Godot 时带 `-d --remote-debug tcp://127.0.0.1:0`，目的是避免脚本解析错误时本地调试器陷入无限的 `debug>` 循环。自己拼命令行时照抄这个做法
- 本机没装 gdUnit4，没有实跑

框架的断言失败有退出码，但引擎自己的运行时报错仍然不会让进程失败，所以 `gdrun` 里的 grep 照样要留。

## 导出 API 文档与签名

```bash
mkdir -p out/doc
godot --headless --no-header --path . --doctool out/doc
godot --headless --no-header --path . --doctool out/doc --gdscript-docs res://scripts
```

第一条把引擎所有类写到 `out/doc/doc/classes/*.xml` 和 `out/doc/modules/*/doc_classes/`，约 1000 个 XML，约 1 秒，只有签名没有说明。第二条为带 `##` 注释的脚本生成 XML，类名文件如 `Unit.xml`，无 class_name 的脚本为 `scripts--player.gd.xml`，含 `brief_description`、参数与默认值。

引擎源码里的 `doc/classes/<类名>.xml` 才带完整说明。
