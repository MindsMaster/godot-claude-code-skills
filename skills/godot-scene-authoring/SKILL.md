---
name: godot-scene-authoring
description: 在 Godot 4 里新做关卡、房间、HUD、菜单、NPC、道具、背景时用，决定内容摆进 .tscn 还是代码运行时搭。新建项目第一个场景，往已有项目加场景，打开场景一片空看不到东西，美术策划要在编辑器里直接看和调，自定义显示节点在编辑器里不显示，@tool 节点把材质 z_index 写进 tscn，确定性模拟 联机 服务器要读场景里摆的位置。先自查项目是摆在场景里还是运行时生成，再按结果新做或迁移。脚本生成 tscn、@tool 自绘节点、预制场景、_validate_property、internal 子节点、NOTIFICATION_EDITOR_PRE_SAVE、C# 重载。level authoring, WYSIWYG, prefab, data-driven, bake on save, empty scene, audit.
---

# Godot 场景摆放

解决内容在哪里定义：有位置、有外观的东西摆进 `.tscn`，打开场景看到的就是游戏里的样子，选得中、拖得动、改了存盘就生效；代码只管规则和运行时才出现的东西。场景怎么拆、节点怎么通信见 godot-scene-architecture，插件和 Inspector 怎么写见 godot-editor-tooling，数据资源和配表见 godot-resources-data。

判断标准：不运行游戏，美术能不能在编辑器里把一盏灯拖到另一处、把 NPC 换个朝向、把 HUD 的血条挪个位置，存盘后进游戏就是改过的样子。

## 先自查

动手做场景前先看项目现在是哪种做法，别假设。三步，细节和脚本见 [references/audit.md](references/audit.md)：

1. 打开或读几个现有 `.tscn`：节点数和游戏里看到的东西对得上，还是只有根节点和脚本
2. 搜脚本里的 `.new()` 加 `add_child`、给 `Control` 设 `position` `size`、`load("res://…png")`，搜配表里的坐标、贴图路径、颜色字段
3. 无头跑审计脚本，数每个场景 `_ready` 之后多出来的、owner 为空的节点

| 结果 | 怎么做 |
|---|---|
| 新项目，或还没有内容场景 | 按下面的做法新做 |
| 内容摆在场景里，脚本只管逻辑 | 照现有结构加内容 |
| 场景空壳，内容运行时按配表或代码建 | 告诉用户自查结果和迁移范围，同意后按 [references/migration.md](references/migration.md) 迁。没同意时，新系统照样摆进场景，往已有的代码搭系统里加东西时跟着现状写 |
| 两种都有 | 按系统分开判断，HUD、菜单、关卡、NPC 各算一项 |

程序生成的地图、按数据数量建的列表行属于运行时内容，不算问题。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 背景 道具 灯 HUD 菜单布局 | 节点直接摆进 `.tscn`，UI 用 Container 和 `Theme` | 代码 `new` 整棵树，场景只剩空壳 |
| 运行时才出现的敌人 子弹 列表行 | 预制 `.tscn` + `PackedScene.instantiate()` | 代码里逐个 `new` 子节点再设颜色尺寸 |
| 不开编辑器生成场景文件 | `extends SceneTree` 脚本建节点、设 owner、`PackedScene.pack` 后 `ResourceSaver.save` | 手拼大段 tscn 文本 |
| 自定义显示节点在编辑器里能看见 | `@tool` + 按导出属性 `_draw` 或建内部子节点 | 只在运行时按配表建，编辑器里空白 |
| 代码派生的属性不进 tscn | `_validate_property` 去掉 `PROPERTY_USAGE_STORAGE` | 存盘前清掉、存完再设回 |
| 节点自己生成的辅助子节点 | `add_child(n, false, Node.INTERNAL_MODE_BACK)` 不设 owner | 设 owner 存进场景 |
| 模拟 服务器 回放要读摆好的位置 | 存盘时导出：`Node.NOTIFICATION_EDITOR_PRE_SAVE` 或 `EditorPlugin.scene_saved` | JSON 里手写坐标，对着截图调 |
| 同一类物件不同外观 | 预制场景实例后覆盖属性，或继承场景 | 配表里写贴图路径 颜色 尺寸 |
| Tiled LDtk 这类外部关卡 | `EditorImportPlugin` 导入成场景，见 godot-editor-tooling | 运行时解析，编辑器里看不见 |

默认直接导出 `Texture2D`，拖进 Inspector 即可。项目有资源表或 MOD 覆盖时导出 ID 字符串，`@tool` 里按 ID 解析成贴图。

## 哪些进场景 哪些进数据

| 内容 | 放哪 |
|---|---|
| 有位置有外观：背景层、灯、NPC 站位和朝向、道具、机关外观、HUD 和菜单布局 | `.tscn` |
| 运行时才出现：敌人、投射物、掉落、列表行、弹窗 | 预制 `.tscn`，代码只 `instantiate()` 和设数据 |
| 规则和数值：出现条件、对话、商店、波次、伤害 | `Resource` 或配表 |
| 模拟 服务器要的位置和尺寸 | 场景里摆，存盘导出成数据 |
| 程序生成的地图 | 代码生成，同一段代码在 `@tool` 里按同样的种子生成给编辑器看 |

同一项只有一个来源，别在场景和配表里各写一份外观。

## 新做一个场景

关卡的树长这样，每一项都是存盘的节点，重复出现的东西是预制场景的实例：

```
Level            Node2D  level.gd
├ Background     Parallax2D / Sprite2D
├ Ground         TileMapLayer
├ Props          Node2D / crate.tscn 实例若干
├ Npcs           Node2D / npc.tscn 实例 覆盖朝向和对话 ID
├ SpawnPoints    Node2D / Marker2D 若干
└ Hud            hud.tscn 实例
```

不开编辑器时用一次性脚本生成，`godot --headless -s make_level.gd`，跑完删掉脚本，之后在编辑器里调：

```gdscript
extends SceneTree

func _initialize() -> void:
	var level := Node2D.new()
	level.name = "Level"
	var points := Node2D.new()
	points.name = "SpawnPoints"
	level.add_child(points)
	points.owner = level
	for i in 3:
		var marker := Marker2D.new()
		marker.name = "Spawn%d" % i
		marker.position = Vector2(200.0 * i, 0.0)
		points.add_child(marker)
		marker.owner = level
	var packed := PackedScene.new()
	packed.pack(level)
	ResourceSaver.save(packed, "res://level.tscn")
	level.free()
	quit()
```

- 每个后代都要设 `owner` 为场景根，只设直接子节点不够
- 实例化的子场景只给它的根设 owner，它里面的节点归子场景
- 几个节点的小场景可以直接写 tscn 文本，注意事项见 godot-scene-architecture 的 references/lifecycle.md

脚本只拿场景里摆好的节点，运行时才出现的东西从预制场景实例化：

```gdscript
extends Node2D

@export var enemy_scene: PackedScene
@onready var spawn_points: Node2D = $SpawnPoints

func spawn_wave() -> void:
	for point: Node in spawn_points.get_children():
		var enemy := enemy_scene.instantiate() as Node2D
		enemy.position = (point as Node2D).position
		add_child(enemy)
```

## 自己画的节点

`Sprite2D` 能表达的就用 `Sprite2D`。按米算高度、读自定义动画格式这类需要自己语义的节点，同样要在编辑器里按自己的属性画出来：

```gdscript
@tool
class_name GroundProp
extends Node2D

@export var texture: Texture2D:
	set(value):
		texture = value
		queue_redraw()
@export var height: float = 64.0:
	set(value):
		height = value
		queue_redraw()

func _draw() -> void:
	if texture == null:
		return
	var size := texture.get_size() * (height / texture.get_height())
	draw_texture_rect(texture, Rect2(Vector2(-size.x / 2.0, -size.y), size), false)
```

- 存盘的是节点和它的导出属性，画法跟着脚本走，和 `TileMapLayer` 按图块数据画出来是一回事
- setter 里只 `queue_redraw()` 或改自己的状态。用到树的操作先判断 `is_inside_tree()`，场景加载时 setter 在进树前就会调用

## 派生的东西不存盘

节点在 `_ready` 或 setter 里按环境算出来的属性，存盘时照样写进 tscn。常见的是按所在视口选的 `material`、按深度算的 `z_index`，材质里带贴图时路径也一起写进去。用 `_validate_property` 去掉存盘位：

```gdscript
@tool
extends Node2D

@export var depth: float = 0.0:
	set(value):
		depth = value
		z_index = -10 if depth > 0.0 else 10

func _validate_property(property: Dictionary) -> void:
	if property.name == "z_index":
		property.usage &= ~PROPERTY_USAGE_STORAGE
```

- 对继承来的引擎属性也生效，脚本要是 `@tool`。去掉后场景里设的值也不存，这类属性只能由代码决定

地面条、阴影这类节点自己生成、不属于内容的子节点，用 internal 子节点加进来，不设 owner：

```gdscript
@tool
extends Node2D

var _shadow: Sprite2D

func _ready() -> void:
	_shadow = Sprite2D.new()
	_shadow.modulate = Color(0.0, 0.0, 0.0, 0.4)
	add_child(_shadow, false, Node.INTERNAL_MODE_BACK)
```

| | 不设 owner | 不设 owner 且 internal |
|---|---|---|
| 视口里画出来 | 是 | 是 |
| 场景面板里看得到、点得中 | 否 | 否 |
| 存进 tscn | 否 | 否 |
| `get_children()` 拿得到 | 是 | 否，要 `get_children(true)` |
| `duplicate()` 和 Ctrl+D 带上 | 是 | 否 |

只不设 owner 不够：复制节点时生成的子节点被一起复制，新节点的 `_ready` 又建一份。设了 owner 的 internal 子节点照样存盘，读回来变成普通子节点。

## 存盘时导出给模拟

确定性模拟、回滚联机、服务器不能依赖场景树时，位置照样在场景里摆，存盘时导出成数据文件，跟场景一起提交：

```gdscript
@tool
extends Node2D

@export_file("*.json") var export_path: String = "res://room_points.json"

func _notification(what: int) -> void:
	if what == NOTIFICATION_EDITOR_PRE_SAVE:
		export_points()

func export_points() -> void:
	var points: Array[Dictionary] = []
	for child: Node in get_children():
		var marker := child as Marker2D
		if marker != null:
			points.append({"name": String(marker.name), "x": marker.position.x, "y": marker.position.y})
	var file := FileAccess.open(export_path, FileAccess.WRITE)
	file.store_string(JSON.stringify({"points": points}, "\t"))
```

- 只在编辑器里、打包场景之前发给被存场景的每个节点。这时节点被锁着，`add_child` `remove_child` 报错，只能读写属性和文件
- 统一导出放在插件里时连 `EditorPlugin.scene_saved`，文件写盘之后调
- 再做一个无头检查：读所有场景重新导出，和提交的文件不一致就失败

## 编辑器视口和游戏不一样

- 场景里的 `Camera2D` 在编辑器里不生效。跟镜头走的视差层、跟随节点在编辑器里停在原点
- `CanvasLayer` 的内容跟着编辑器平移缩放。`SubViewport` 的内容按单位变换贴出来，只显示子视口尺寸以内的部分
- 游戏里单独给某个 `SubViewport` 开了 `Viewport.use_hdr_2d`，编辑器视口只按项目设置 `rendering/viewport/hdr_2d`。材质按 `get_viewport()` 在进树之后选
- 编辑器默认低处理器模式，`@tool` 的 `_process` 只在重绘时推进。`_process` 里每帧 `queue_redraw()` 会让编辑器一直刷新，动画在编辑器里挡住
- 切换场景标签页时，旧场景的根先出树、再进树，`_ready` 只跑一次。`_exit_tree` 里释放的东西在 `_enter_tree` 里补回
- 改了全局着色器参数、静态缓存这类全局状态的节点，在 `_exit_tree` 里还原。换场景时旧的 `queue_free()` 要到帧末才出树，把新设的值还原掉，先 `remove_child()` 再 `queue_free()`

只在当前编辑的场景里做的事，判断 `is_part_of_edited_scene()`。编辑器先设好 `SceneTree.edited_scene_root` 再把场景加进树，`_ready` 里判断得到。

## C#

- 类加 `[Tool]`，改完点 Build 才生效。内部子节点是 `AddChild(node, false, InternalMode.Back)`
- 程序集重载时 `_Ready` 不重跑，只恢复能转成 Variant 的字段和属性。实现 `ISerializationListener`，在 `OnAfterDeserialize()` 里重新加载，自己建的 RID 在 `OnBeforeSerialize()` 里释放
- tool 代码 `new` 出来的非 `[Tool]` C# 节点，在编辑器里 `_Ready` `_Draw` 照常调用

完整示例见 [references/csharp.md](references/csharp.md)。

## 陷阱

- `@tool` 节点在 `_ready` 里给自己赋 `material` `z_index`，存盘时写进 tscn。用 `_validate_property` 去掉存盘位
- 不设 owner 的节点在视口里照样画，但场景面板看不到、点不中、不存盘。要成为内容就设 owner 为场景根，编辑器里是 `EditorInterface.get_edited_scene_root()`
- 生成节点挂在实例化的子场景下面、owner 设成子场景根时，打开子场景编辑会把它存进子场景文件。生成节点一律不设 owner
- 预制场景里的 ColorRect Label 要统一换材质时，子节点勾 `CanvasItem.use_parent_material`，代码只给根设一次，能隔多层传下去
- 编辑器存盘会给旧 tscn 补 `uid`，新版还会给节点补 `unique_id`。只打开存盘也会出 diff，和逻辑改动分开提交
- 导出数据只在编辑器存盘时写，没开编辑器改了场景会提交过期的数据。加无头检查
- 只给编辑器画一份不存盘的假画面去模仿运行时会建的东西，美术看得见但改不了，改了也不生效。内容要真的在场景里
- 没自查就照自己的习惯写，在代码搭的项目里新做一套场景，或在摆场景的项目里用代码建，两种做法混在同一个系统里

## 参考

- [references/audit.md](references/audit.md)：自查清单、搜索命令、无头审计脚本、怎么向用户报告
- [references/migration.md](references/migration.md)：迁移顺序、坐标换算、无头编辑器验证插件、常见报错
- [references/csharp.md](references/csharp.md)：C# 自绘节点完整示例
- 官方文档：https://docs.godotengine.org/en/stable/tutorials/best_practices/scenes_versus_scripts.html
- 官方文档：https://docs.godotengine.org/en/stable/tutorials/best_practices/scene_organization.html
- 官方文档：https://docs.godotengine.org/en/stable/tutorials/plugins/running_code_in_the_editor.html
