# 导入期烘焙

外部数据（JSON CSV 表格导出）在编辑器里转成 `Resource` 一次，运行时只 `load`。

## JSON 转 .tres

```gdscript
class_name ItemData
extends Resource

@export var id: StringName
@export var title: String
@export var price: int
```

```gdscript
@tool
extends EditorScript

const SRC: String = "res://data/items.json"
const OUT: String = "res://data/items/"

func _run() -> void:
	var rows: Array = JSON.parse_string(FileAccess.get_file_as_string(SRC))
	DirAccess.make_dir_recursive_absolute(OUT)
	for row: Dictionary in rows:
		var path := OUT + str(row["id"]) + ".tres"
		var item: ItemData = load(path) if ResourceLoader.exists(path) else ItemData.new()
		item.id = StringName(row["id"])
		item.title = row["title"]
		item.price = int(row["price"])
		var err := ResourceSaver.save(item, path)
		if err != OK:
			push_error("保存失败 %s %s" % [path, error_string(err)])
	EditorInterface.get_resource_filesystem().scan()
```

- 脚本编辑器里打开它，`File > Run`（Ctrl+Shift+X）执行
- 已存在的 `.tres` 先 `load` 再原地改，Inspector 里手填的其他字段保留。同路径重存 uid 保留，别处引用不断，前提是在编辑器里执行，运行游戏时 `ResourceSaver` 不写 uid
- 转换结果提交进版本库，源 JSON 一起留着
- 解析 JSON 是系统边界：行缺字段、类型不对时报错并跳过，不要写出半成品资源

JSON 一直在变、需要源文件放进工程就自动导入时，改用 `EditorImportPlugin`，见 godot-editor-tooling 的导入插件一节。

## 大数据烘焙成 .res

运行时解析 MB 级 JSON 再手建 `ArrayMesh`，每次启动都付一遍代价。导入期建好，存成二进制 `.res`：

```gdscript
@tool
extends EditorScript

func _run() -> void:
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/terrain.json"))
	var flat := PackedFloat32Array(raw["vertices"])
	var verts := PackedVector3Array()
	verts.resize(roundi(flat.size() / 3.0))
	for i in verts.size():
		verts[i] = Vector3(flat[i * 3], flat[i * 3 + 1], flat[i * 3 + 2])
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_INDEX] = PackedInt32Array(raw["indices"])
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var err := ResourceSaver.save(mesh, "res://baked/terrain.res")
	if err != OK:
		push_error(error_string(err))
```

- 运行时 `load("res://baked/terrain.res")` 直接得到 `ArrayMesh`
- `.res` 是二进制，不能手改也不能 diff，源数据留在仓库里，烘焙结果也提交，或者在 CI 里重新烘焙
- 查找表、导航数据、预计算的噪声同理，存成自定义 `Resource` 的 `PackedFloat32Array` 字段
