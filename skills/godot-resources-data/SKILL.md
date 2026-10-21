---
name: godot-resources-data
description: Godot 4 数据与资源管理，用于游戏数据表、配置、存档、资源加载与缓存。Use when defining game data as custom Resource (class_name + @export, .tres, C# [GlobalClass]), deciding JSON vs Resource, converting JSON/CSV to Resource at import time, Resource sharing / duplicate / duplicate_deep / local_to_scene, ResourceLoader cache and CacheMode, load vs preload, load_threaded_request with progress bar, ResourceSaver, save games in user:// (JSON, ConfigFile, store_var), untrusted .tres security, uid:// references, DirAccess on res:// after export, ResourceLoader.list_directory, Curve / Gradient / CurveTexture / Animation instead of custom curve classes, texture cache Dictionary. 数据表 自定义资源 存档 异步加载 加载界面 资源缓存 导出后目录扫描。
---

# Godot 资源与数据

解决游戏数据怎么定义、怎么编辑、怎么加载、怎么存档。不管场景怎么拆（见 godot-scene-architecture），不管写编辑器插件和导入插件（见 godot-editor-tooling）。

默认做法：只在游戏里用的数据做成自定义 `Resource`，用 `.tres` 在 Inspector 里编辑。JSON 留给外部工具、mod 和网络。存档用 JSON 到 `user://`。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 武器 敌人 物品 技能数据表 | 自定义 `Resource` + `@export`，`.tres` | JSON 加手写解析，字符串键取字段 |
| 伤害成长 缓动 衰减曲线 | `Curve`，`sample(t)`；给 shader 用 `CurveTexture` | 自写关键帧曲线类 |
| 颜色渐变 | `Gradient`，`sample(t)`；给 shader 用 `GradientTexture1D` | 颜色数组加手写插值 |
| 路径 轨道 | `Curve2D` `Curve3D` | 点数组加手算切线 |
| 关键帧动画 | `Animation` + `AnimationPlayer` | 自写属性曲线播放器 |
| 缓存纹理 音频 场景 | `load()` 自带缓存 | `static var` 字典缓存 `Texture2D` |
| 大场景不卡顿加载 | `load_threaded_request` + 每帧 `load_threaded_get_status` | 请求后立刻循环 `load_threaded_get` |
| 枚举某类资源 | 显式清单（`Array[Resource]` 的数据库资源），或 `ResourceLoader.list_directory`（4.4+） | 运行时 `DirAccess` 扫 `res://` |
| 兼容外部工具的数据 | 导入期转成 `.tres` 或 `.res` | 运行时全量解析 JSON 再手建对象 |
| MB 级几何或查找表 | 导入期烘焙成 `.res` | 运行时解析 JSON 建 `ArrayMesh` |
| 存档 | JSON 到 `user://` | `ResourceSaver` 存自定义 `Resource`，再 `load` 回来 |
| 稳定的资源引用 | `@export` 拖拽，或 `uid://` | 手写 `res://` 字符串当主键 |

## 自定义 Resource 当数据

```gdscript
class_name ItemData
extends Resource

@export var id: StringName
@export var title: String
@export_multiline var description: String
@export var icon: Texture2D
@export var price: int = 10
@export var price_curve: Curve
@export var tags: Array[StringName] = []
```

- 文件系统面板右键 New Resource 选 `ItemData`，存成 `.tres`，字段在 Inspector 里编辑，撤销重做、拖拽引用、复制粘贴都是原生的
- 资源能互相引用：`@export var drops: Array[ItemData]`，Inspector 里可以拖入，也可以内嵌新建
- 整张表用一个数据库资源持有，运行时按 id 建索引：

```gdscript
class_name ItemDb
extends Resource

@export var items: Array[ItemData] = []

var _by_id: Dictionary[StringName, ItemData] = {}

func get_item(id: StringName) -> ItemData:
	if _by_id.is_empty():
		for item in items:
			_by_id[item.id] = item
	return _by_id.get(id)
```

- `_init` 的参数必须都有默认值。Inspector 新建和 `duplicate()` 都是无参构造，有必填参数时 `duplicate()` 报 `Error constructing a GDScriptInstance` 并返回空壳
- 资源是静态配置。会变的运行时状态（当前血量 冷却）放在节点或 `RefCounted` 里，不写回共享的 `Resource`，见下文共享一节
- 文本格式 `.tres` 适合手改和版本控制，二进制 `.res` 适合烘焙出的大数据
- 不需要 Inspector 编辑、只是内存里的数据包用 `RefCounted` 子类，不要继承 `Node`

C# 用 `[GlobalClass]`，类名与文件名一致，必须 `partial`，属性写 `{ get; set; }`，改完先构建，Inspector 才认得：

```csharp
[GlobalClass]
public partial class ItemData : Resource
{
    [Export] public StringName Id { get; set; }

    [Export] public string Title { get; set; } = "";

    [Export] public int Price { get; set; } = 10;

    [Export] public Curve PriceCurve { get; set; }

    [Export] public Godot.Collections.Array<ItemData> Drops { get; set; } = new();
}
```

读取：`GD.Load<ItemData>("res://data/items/sword.tres")`。

## JSON 何时仍合理

| 场景 | 选择 |
|---|---|
| 只在游戏侧用的数据 | `Resource` |
| 策划用表格工具维护，导出 JSON 或 CSV | 源文件保留，导入期转成 `Resource` |
| 玩家 mod 或可下载内容，不能带脚本 | JSON，加载时校验字段 |
| 网络协议 | JSON 或二进制，不是 `Resource` |
| 存档 | JSON，见 [references/saving-data.md](references/saving-data.md) |
| 与其他引擎共用的数据 | JSON |

导入期转换的两种做法：

- 数据很少改：`@tool` 的 `EditorScript` 一键把 `res://data/*.json` 转成 `.tres`，把转换结果提交进仓库
- 数据常改：`EditorImportPlugin`，源文件放进工程就自动导入，改源文件自动重导，做法见 godot-editor-tooling

表格工具和编辑器都想改同一份数据时，先定唯一源头：表格还在导出就以 JSON 为源，`.tres` 只生成不手改；改在 Inspector 里就以 `.tres` 为源，用 `@tool` 按钮或 `EditorPlugin` 导出 JSON 给外部服务。两边各改一份迟早不一致。

两种做法的 `ResourceSaver` 代码见 [references/baking-data.md](references/baking-data.md)。运行时不再有解析代码，类型错误在导入时暴露，不拖到玩家机器上。

## 共享 复制 local_to_scene

同一个 `.tres` 被 `load` 多次，拿到的是同一个对象。场景里的子资源（sub_resource）被同一场景实例化多次，这些实例也共用它。改一处，处处变。

| 做法 | 行为 |
|---|---|
| `load(path)` 两次 | 同一实例，改一个另一个跟着变 |
| `duplicate()` | 浅拷贝，嵌套的 `Array` `Dictionary` `Resource` 与原件共享 |
| `duplicate(true)` | 数组和字典也复制，只复制内嵌的子资源，带路径的外部资源仍共享 |
| `duplicate_deep(mode)`（4.5+） | 同上并可选：`DEEP_DUPLICATE_NONE` 不复制子资源，`DEEP_DUPLICATE_INTERNAL` 只复制内嵌的（默认），`DEEP_DUPLICATE_ALL` 连外部资源也复制 |
| `resource_local_to_scene = true` | 场景每次实例化，这个资源各得一份，外部 `.tres` 也适用 |
| `ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_IGNORE)` | 绕过缓存读一份新的 |

```gdscript
class_name StatBlock
extends Resource

@export var hp: int = 10
@export var speed: float = 120.0
```

```gdscript
extends CharacterBody2D

@export var base_stats: StatBlock

var stats: StatBlock

func _ready() -> void:
	stats = base_stats.duplicate()
```

- 每个敌人要自己的血量，就在 `_ready` 里 `duplicate()`，或者把资源勾上 `resource_local_to_scene`
- 数据表里的 `ItemData` 当只读用，不要 `item.price = 5` 这样改，改了所有引用方都变，而且改动会留到缓存释放为止
- 要在 local_to_scene 复制时做初始化，重写 `Resource._setup_local_to_scene`
- C# 里 `(StatBlock)BaseStats.Duplicate()`，深拷贝 `DuplicateDeep(Resource.DeepDuplicateMode.Internal)`（4.5+）

## 加载

| 做法 | 用于 |
|---|---|
| `preload("res://x.tscn")` | 路径是常量，脚本一加载就读入。小而必用的资源 |
| `load(path)` | 路径是变量，或用到才读。同步，大资源会卡一帧以上 |
| `@export var scene: PackedScene` | 路径交给 Inspector，移动文件时引用不断 |
| `ResourceLoader.load_threaded_request` | 大资源或加载界面 |
| `ResourceLoader.exists(path)` | 导出后判断资源在不在，比 `FileAccess.file_exists` 可靠 |

`load` 的缓存按路径，资源没有任何引用时才会释放。不需要自己存一份字典缓存。

`ResourceLoader.CacheMode`：

| 值 | 行为 |
|---|---|
| `CACHE_MODE_REUSE` | 默认。有缓存用缓存，没有就读并存入 |
| `CACHE_MODE_IGNORE` | 不读也不写缓存，得到独立副本。依赖仍走缓存 |
| `CACHE_MODE_REPLACE` | 重读并刷新已缓存的同一对象，热重载数据用 |
| `CACHE_MODE_IGNORE_DEEP` `CACHE_MODE_REPLACE_DEEP` | 同上，递归到依赖 |

### 带进度的异步加载

```gdscript
extends Control

signal finished(resource: Resource)

@export var bar: ProgressBar

var _path: String = ""
var _progress: Array = []

func _ready() -> void:
	set_process(false)

func start(path: String) -> void:
	_path = path
	ResourceLoader.load_threaded_request(path)
	set_process(true)

func _process(_delta: float) -> void:
	var status := ResourceLoader.load_threaded_get_status(_path, _progress)
	match status:
		ResourceLoader.THREAD_LOAD_IN_PROGRESS:
			bar.value = float(_progress[0]) * 100.0
		ResourceLoader.THREAD_LOAD_LOADED:
			set_process(false)
			finished.emit(ResourceLoader.load_threaded_get(_path))
		_:
			set_process(false)
			push_error("加载失败 " + _path)
```

- 状态在不同帧里查，不要在一个 `while` 里空转
- `load_threaded_get` 在没加载完时会阻塞，只在状态为 `THREAD_LOAD_LOADED` 后调用
- 进度按已加载的依赖估算，单个大文件可能直接从 0 跳到 1
- `use_sub_threads = true` 更快，但可能拖慢主线程，加载界面上可以开
- 加载完的场景直接交给 `SceneTree.change_scene_to_packed`

## 枚举资源与 res:// 路径

导出后图片音频等导入资源的原文件不在包里，只剩 `.import`，转换结果放在 `.godot/imported`。`.tres` `.tscn` 默认转成二进制（`editor/export/convert_text_resources_to_binary`），原路径只剩 `.remap`。`DirAccess` 看到的目录和编辑器里不一样，直接扫目录会漏项或多出这些后缀。

- 清单是首选：一个数据库资源里 `@export var items: Array[ItemData]`，增删在 Inspector 里做
- 必须枚举目录时用 `ResourceLoader.list_directory("res://data/items")`（4.4+），返回编辑器里看到的原文件名，子目录带 `/` 后缀，顺序不固定，需要稳定顺序时自己排序
- 导出前 `list_directory("res://")` 会列出 `.godot/`，过滤掉
- 加载时用 `ResourceLoader.load`，不要 `FileAccess.open("res://...")` 读导出后的资源
- `user://` 是可写目录，位置因平台而异，`OS.get_user_data_dir()` 取绝对路径用于展示，代码里一律写 `user://`

## uid 引用

- 编辑器给每个资源分配 `uid://...`，场景和 `.tres` 里同时存 uid 和路径，在编辑器内移动重命名文件时引用自动跟着走
- 代码里写 `preload("uid://...")` 或 `load("uid://...")` 可以，路径移动后仍有效。uid 与路径互转：`ResourceLoader.get_resource_uid` 返回 `int`，没有 uid 时为 -1，`ResourceUID.id_to_text` 转成 `uid://` 字符串。4.5+ 可直接用 `ResourceUID.path_to_uid` 与 `ResourceUID.uid_to_path`
- `@export_file` 存的是 uid，文件移动后仍有效。`@export_file_path`（4.5+）存裸路径，移动后失效
- 脚本的 `.gd.uid` 文件（4.4+）要一起提交版本库，丢了 uid 会变，引用方只能走路径回退
- 在编辑器之外移动文件后，让编辑器重新扫描并保存引用方，场景里记的回退路径才会更新

## 存档

存档文件在玩家手里，视为不可信输入。

| 格式 | 适合 | 注意 |
|---|---|---|
| JSON（`JSON.stringify` `JSON.parse_string`） | 存档 跨版本 可读 | 数字读回是 `float`；`Vector2` `Color` 要转换或用 `JSON.from_native` `JSON.to_native`（4.4+） |
| `ConfigFile` | 设置 简单键值 | 文本里的 `Object(...)` 会被实例化，只读自己写的文件 |
| `FileAccess.store_var` `get_var` | 紧凑二进制 | `get_var(true)` 会解码对象并可能执行脚本，`allow_objects` 保持默认 `false` |
| `ResourceSaver.save` | 编辑器工具 开发期烘焙 | 不用于玩家存档 |

不要 `load()` 玩家可写位置的 `.tres` `.res` `.tscn`。这些文件可以内嵌脚本，加载就会执行。实测一个内嵌 `GDScript` 子资源的 `.tres`，`load` 时 `_init` 里的代码直接运行。

格式版本号、原子写入、加密和 C# 写法见 [references/saving-data.md](references/saving-data.md)。

## 陷阱

- 改共享资源的属性会污染缓存，后面所有 `load` 都拿到改后的值。典型的是 `stream.loop = true` 直接改 `AudioStream`。循环属性应在导入设置里改，或者 `duplicate()` 之后再改
- 场景里一个 sub_resource 被多个实例共享，其中一个实例改了 `material.albedo_color`，所有实例都变。需要独立就勾 `resource_local_to_scene`，或在 `_ready` 里 `duplicate()`
- `duplicate()` 是浅拷贝，`Array[Resource]` 里的元素仍与原件共享
- 自己用字典缓存 `Texture2D` `Material`：字典持有强引用，资源不再随引用归零释放，而且 `load` 已经缓存了
- `load_threaded_request` 后立刻 `load_threaded_get`，等于同步 `load`，卡住主线程
- 自定义 `Resource` 改了类名或移动了脚本，旧 `.tres` 里的 `script_class` 和脚本路径失效。在编辑器里改名，并保留 `.uid`
- `@export` 的 `Array[ItemData]` 里元素为 `null` 时 Inspector 不报错，运行时才崩。用到时判空
- `ConfigFile` 与 `str_to_var` 会实例化文本里写的 `Object(...)`。来源不可信的文本用 `JSON`
- 运行时 `DirAccess` 扫 `res://`，编辑器里正常，导出后行为不同
- 为了存几个字段手写 70 行 JSON 解析。字段固定的数据用 `Resource`，解析交给引擎

## 参考

- [references/builtin-data-resources.md](references/builtin-data-resources.md)：`Curve` `Gradient` `CurveTexture` `Curve2D` `Animation` 的取值与替换对照
- [references/saving-data.md](references/saving-data.md)：存档格式比较，版本迁移，原子写入，加密，C# 写法
- [references/baking-data.md](references/baking-data.md)：JSON 转 `.tres`，大数据烘焙成 `.res`
- 官方文档：https://docs.godotengine.org/en/stable/tutorials/scripting/resources.html
- 官方文档：https://docs.godotengine.org/en/stable/tutorials/io/background_loading.html
