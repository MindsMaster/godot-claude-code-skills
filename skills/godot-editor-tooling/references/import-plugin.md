# 导入插件

外部文件放进工程就自动转成 `Resource`，改源文件自动重导。数据常改、策划直接维护 JSON 或表格导出文件时用它。数据很少改，一个 `EditorScript` 一次性转换更省事，见 [editor-recipes.md](editor-recipes.md)。

## 数据脚本

```gdscript
@tool
class_name ItemData
extends Resource

@export var id: StringName
@export var price: int
```

```gdscript
@tool
class_name ItemDb
extends Resource

@export var items: Array[ItemData] = []
```

导入器里用到的自定义资源脚本都要加 `@tool`，没加时编辑器里拿到的是占位实例，方法不可用。

## 导入器

```gdscript
@tool
extends EditorImportPlugin

func _get_importer_name() -> String:
	return "game.item_table"

func _get_visible_name() -> String:
	return "Item Table"

func _get_recognized_extensions() -> PackedStringArray:
	return ["itemtable"]

func _get_save_extension() -> String:
	return "res"

func _get_resource_type() -> String:
	return "Resource"

func _get_preset_count() -> int:
	return 1

func _get_preset_name(_preset_index: int) -> String:
	return "Default"

func _get_import_options(_path: String, _preset_index: int) -> Array[Dictionary]:
	return []

func _get_priority() -> float:
	return 1.0

func _get_import_order() -> int:
	return 0

func _import(source_file: String, save_path: String, _options: Dictionary, _platform_variants: Array[String], _gen_files: Array[String]) -> Error:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(source_file))
	if not parsed is Array:
		return ERR_PARSE_ERROR
	var db := ItemDb.new()
	for row: Dictionary in parsed:
		var item := ItemData.new()
		item.id = StringName(row.get("id", ""))
		item.price = int(row.get("price", 0))
		db.items.append(item)
	return ResourceSaver.save(db, "%s.%s" % [save_path, _get_save_extension()])
```

```gdscript
@tool
extends EditorPlugin

var _importer: EditorImportPlugin

func _enter_tree() -> void:
	_importer = load("res://addons/items/item_table_importer.gd").new()
	add_import_plugin(_importer)

func _exit_tree() -> void:
	remove_import_plugin(_importer)
	_importer = null
```

放一个 `data/items.itemtable`，内容 `[{"id":"sword","price":10}]`，编辑器扫描后生成 `.import` 文件和 `.godot/imported/` 下的 `.res`。游戏里 `load("res://data/items.itemtable")` 直接得到 `ItemDb`。

- 扩展名别用 `json` `txt` 这类常见后缀，会和内置导入器抢文件。用自己的后缀，如 `itemtable`
- `_get_save_extension` 对普通资源写 `res`，场景写 `scn`，材质写 `material`。`_get_resource_type` 决定拖放到哪种属性槽
- `_import` 的返回值是 `Error`，解析失败返回 `ERR_PARSE_ERROR`。源文件是系统边界，字段缺失和类型不对都要处理
- 保存路径是 `save_path` 加扩展名，不要写到别处。额外生成的文件放进 `_gen_files`，按平台不同的变体放进 `_platform_variants` 并用 `save_path.特性标签.扩展名` 保存
- 选项用 `_get_import_options` 返回 `[{"name": "scale", "default_value": 1.0}]` 这样的字典数组，在 Import 面板里显示，`_import` 的 `options` 参数拿到值
- 需要多线程导入时重写 `_can_import_threaded` 返回 `true`，`_import` 里不碰场景树和编辑器单例
- 导入结果引用的其他资源变了不会自动重导，需要时在 `_import` 里调用 `append_import_external_resource`
- 源文件放进工程后，导入结果不提交，`.import` 文件提交，`.godot/` 不提交

## 场景导入后处理

glTF 等 3D 场景导入后要统一改节点（关阴影 加碰撞 改名），用 `EditorScenePostImport`：

```gdscript
@tool
extends EditorScenePostImport

func _post_import(scene: Node) -> Object:
	for node: MeshInstance3D in scene.find_children("*", "MeshInstance3D"):
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return scene
```

- 单个文件用：Import 面板的 Custom Script 选这个脚本，然后 Reimport
- 全局规则用 `EditorScenePostImportPlugin`，在 `EditorPlugin` 里 `add_scene_post_import_plugin`
- `_post_import` 必须返回场景根，`get_source_file()` 取源文件路径
