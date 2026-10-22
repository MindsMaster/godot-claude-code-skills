# 测试

```
python3 tests/check.py [lint] [api] [gd] [run] [cs] [--only 路径子串] [--strict]
```

| 步骤 | 查什么 | 依赖 |
| --- | --- | --- |
| lint | frontmatter、SKILL.md 行数、断链、禁用措辞 | 无 |
| api | 行内代码的类名、`Class.member`、项目设置路径、代码块里的已弃用类、版本标注 | `tests/data/godot_api.json.gz` |
| gd | GDScript 代码块逐个无头加载 未标类型和引擎默认警告都按错误算 | `GODOT_BIN` |
| run | GDScript 代码块逐个真跑 有错误或警告输出、没跑完、超时都算失败 | `GODOT_BIN`，render 模式另需 `xvfb-run` 与 Vulkan 驱动 |
| cs | C# 代码块用 Godot.NET.Sdk 编译 开 IDE0011 | `DOTNET_BIN` .NET 8 SDK |

每个检查一个文件，从头读到尾就是这一项的全部逻辑：

| 文件 | 内容 |
| --- | --- |
| `check.py` | 入口 收集 skills 下的 md 依次跑各项 |
| `markdown.py` | 把 md 拆成正文行和代码块 读 frontmatter |
| `lint.py` | 格式与措辞 |
| `api.py` | 对照 `data/godot_api.json.gz` |
| `gdscript.py` | 生成临时工程 用 Godot 加载每个片段 |
| `run.py` | 按 `run/<skill>.md` 的夹具逐个运行片段 |
| `csharp.py` | 生成临时 csproj 编译所有片段 |
| `build_api_index.py` | 从引擎源码生成 API 索引 升级版本时跑 |

`data/allow_names.txt` 放引擎类参考里查不到但确实存在的名字：示例里自定义的类型、旧版本类名、未写进文档的项目设置。

代码块上一行的标记：

```
<!-- check: skip -->
<!-- check: extends CharacterBody2D -->
<!-- check: deprecated -->
```

`deprecated` 用于故意展示旧写法的代码块。

# run

每个代码块单独起一个 Godot 进程。同一文档的代码块放在同一个工程里，互相能用 `class_name`。

| 模式 | 怎么跑 | 默认用于 |
| --- | --- | --- |
| game | 无头 `--fixed-fps 60`，实例化脚本挂到 `root` 下，跑完夹具或 60 个物理帧后释放 | 其余代码块 |
| script | 代码块本身就是 `-s` 脚本，要自己 `quit()`，退出码非 0 算失败。写 `mode render` 则在 xvfb 下跑 | `extends SceneTree` |
| editor | 无头编辑器里由一个插件实例化并驱动 | 用到 `Editor*` 类的代码块 |
| render | `xvfb-run` 下开窗口渲染，默认 Vulkan Forward+ | 夹具里写 `mode render` |

自动补的上下文：

- `@onready var x: T = $Path` 与 `%Name` 建出对应类型的子节点
- `@export var x: T` 能实例化的类型先填一个空实例，节点类型挂成子节点
- `Input.*` 和 `is_action*` 调用里出现的动作名写进工程的 `[input]`

其余上下文写夹具。`run/<skill>.md` 里每节一个代码块：

````
## references/dynamic-music.md `func set_intensity`

<!-- run: frames 120 -->

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://addons/items")
```

<!-- check: setup -->
```gdscript
node.base_layer = make_tone(1.0)
```

```gdscript
node.set_intensity(true)
expect(is_zero_approx(node.volume_db), "说明")
```
````

- 标题是 skill 目录下的文档路径加一段反引号锚点，锚点要在该文档里恰好命中一个 GDScript 代码块
- `prepare` 在导入前作为 `-s` 脚本跑一次，用来写场景、脚本、图片等文件，写完会重新导入
- `setup` 在实例化之后、加进树之前跑，`node` 是代码块的实例，类型就是代码块本身
- 不带标记的是运行段，加进树、`_ready` 跑完后执行，不写就跑 60 个物理帧。script 模式只认 `prepare`
- `<!-- run: ... -->` 选项：`mode game|script|editor|render`，`driver opengl3` 改 render 的驱动，`frames N` 改默认帧数，`norun 原因` 不跑
- 夹具里可用：`frames(n)` 等物理帧，`wait_real(秒)` 等真实时间，`expect(条件, 说明)` 不成立就报错，`make_tone(秒)`、`make_texture(宽, 高, 颜色)`、`make_scene(根节点)`
- 代码块里不以下划线开头的函数，夹具和代码块自身都没调用的，报警告

`_initialize` 运行时 `root` 还不在树内，驱动先等一帧再开始。音频线程按真实时间走，等音频状态变化用 `wait_real`。

# 参考副本

```
mkdir -p ref && cd ref
git clone --depth 1 --filter=blob:none --branch 4.7.2-stable https://github.com/godotengine/godot.git
git clone --depth 1 https://github.com/godotengine/godot-docs.git
git clone --depth 1 https://github.com/godotengine/godot-cpp.git
```

# 升级 API 索引

```
python3 tests/build_api_index.py --godot-cpp ref/godot-cpp --godot ref/godot --target 4.7
```

`--godot` 要指向对应稳定版标签的引擎源码，弃用标记和项目设置取自它的 `doc/classes`。
