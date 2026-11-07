# C# 对照

C# 工程的构建、运行与失败输出。冒烟脚本仍用 GDScript，mono 版同时支持。

## C# 工程

`godot_mono` 指 mono 版可执行文件。标准版 Godot 不加载 `.cs`，必须用 mono 版并先构建。

```bash
dotnet build
godot_mono --headless --no-header --path . --import
godot_mono --headless --no-header --path . main.tscn --quit-after 30
```

| 情况 | 输出 | 退出码 |
|---|---|---|
| `dotnet build` 编译错误 | `Hello.cs(8,17): error CS0029: ...` | 1 |
| 构建后运行，`GetTree().Quit(4)` | `GD.Print` 正常输出 | 4 |
| 没构建就运行 | `Cannot instantiate C# script because the associated class could not be found`，之后卡住 | KILL |
| 找不到 dotnet | `Unable to load .NET runtime, specifically hostfxr` | 崩溃 134 |
| `--build-solutions --quit` 编译失败 | `ERROR: An EditorPlugin build callback failed.` | 1 |
| mono 版 `--import` | `ERROR: Parameter "singleton" is null.`，无害 | 0 |

- `dotnet build` 首次约 9 秒，之后约 2 秒
- 找不到 dotnet：设 `DOTNET_ROOT` 并把 dotnet 放进 `PATH`
- `--build-solutions --quit` 可代替 `dotnet build`
- grep `ERROR:` 时排除 `singleton` is null 这一行
- 断言写法同 GDScript：自己计数，`GetTree().Quit(code)`
