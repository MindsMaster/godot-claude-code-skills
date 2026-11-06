# 自查 内容摆在场景里还是运行时生成

在已有项目里新做或改场景之前读这一篇。结论按系统给，HUD、菜单、关卡、NPC、背景各算一项，一个项目里常常两种都有。

## 看场景文件

数每个场景的节点数，节点很少、根脚本很长的是嫌疑：

```
find . -name "*.tscn" -not -path "./addons/*" -not -path "./.godot/*" | while read -r f; do
	printf "%4d %s\n" "$(grep -c '^\[node ' "$f")" "$f"
done | sort -n | head -40
```

- 关卡、HUD、菜单只有 1 到 3 个节点，挂的脚本几百行：内容在运行时建
- 节点数和游戏画面里的东西对得上：已经摆在场景里
- 打开编辑器看一眼最直接：场景面板里有没有对应的节点，视口里有没有画面

## 搜代码

GDScript：

```
grep -rnE "(Sprite2D|Label|ColorRect|TextureRect|Panel|Button|Polygon2D|Line2D|[HV]BoxContainer)\.new\(\)" --include=*.gd .
grep -rnE "\.(position|size|custom_minimum_size) = " --include=*.gd .
grep -rnE "load\(\"res://[^\"]+\.(png|jpg|webp|svg)\"\)" --include=*.gd .
grep -rlE "func _draw" --include=*.gd . | xargs grep -L "^@tool"
```

C#：

```
grep -rnE "new (Sprite2D|Label|ColorRect|TextureRect|Panel|Button|Polygon2D|Line2D|[HV]BoxContainer)\b" --include=*.cs .
grep -rnE "\.(Position|Size|CustomMinimumSize) = new Vector2" --include=*.cs .
grep -rnE "GD\.Load<Texture2D>\(\"res://" --include=*.cs .
grep -rlE "override void _Draw" --include=*.cs . | xargs grep -L "\[Tool"
```

配表：

```
grep -rlE "\"(x|y|pos|position|texture|sprite|image|color|tint|width|height|scale)\"" --include=*.json .
```

怎么读结果：

- 命中在 `_ready`、`build()`、`setup()`、`enter_room()` 这类函数里，建的是背景、面板、标签、装饰：内容在运行时建
- 命中在生成敌人、子弹、列表行的函数里，每次 `new` 一个节点再设外观：应该做成预制场景，属于小问题
- 配表里同时有坐标和贴图路径：外观在数据里
- 自绘 `_draw` 的脚本没有 `@tool`：编辑器里看不见
- 按种子生成地图、按数据数量建列表行：正常的运行时内容

## 无头审计

把场景逐个实例化、等两帧，数 owner 为空的节点。场景里摆的节点 owner 是场景根，运行时 `add_child` 的 owner 为空，运行时实例化的预制场景只记它的根：

```gdscript
extends SceneTree

const DIRS: PackedStringArray = ["res://levels", "res://ui"]

func _initialize() -> void:
	audit.call_deferred()

func audit() -> void:
	var lines := PackedStringArray(["saved\tadded\tscene"])
	for dir: String in DIRS:
		for path: String in find_scenes(dir):
			var packed := load(path) as PackedScene
			var scene := packed.instantiate()
			root.add_child(scene)
			await process_frame
			await process_frame
			lines.append("%d\t%d\t%s" % [packed.get_state().get_node_count(), count_unowned(scene), path])
			scene.free()
	print("\n".join(lines))
	quit()

func find_scenes(dir: String) -> PackedStringArray:
	var found := PackedStringArray()
	if not DirAccess.dir_exists_absolute(dir):
		return found
	for file: String in DirAccess.get_files_at(dir):
		if file.ends_with(".tscn"):
			found.append(dir.path_join(file))
	for sub: String in DirAccess.get_directories_at(dir):
		found.append_array(find_scenes(dir.path_join(sub)))
	return found

func count_unowned(node: Node) -> int:
	var total := 0
	for child: Node in node.get_children():
		if child.owner == null:
			total += 1
		total += count_unowned(child)
	return total
```

```
godot --headless --path . -s audit.gd
```

- `DIRS` 只放关卡和 UI 目录。实例化会跑游戏代码，可能连网络、写存档、切场景，在干净的工作副本上跑
- `added` 远大于 `saved` 的场景是运行时搭的。`added` 为 0 或只有几个预制实例的是摆好的
- 依赖 autoload 或上一个场景传参的场景可能报错，报错本身说明它不能单独打开，编辑器里多半也是空的
- 跑完删掉脚本

## 向用户报告

迁移是大改动，先给结论再动手：

| 系统 | 现状 | 证据 | 建议 |
|---|---|---|---|
| 关卡 | 运行时按 `rooms.json` 建 | `level.tscn` 2 个节点，`added` 140 | 迁进场景 |
| HUD | 摆在场景里 | `hud.tscn` 38 个节点，`added` 0 | 不动 |
| 敌人 | 代码 `new Sprite2D` | `spawner.gd:40` | 做成预制场景 |

用户同意后按 [migration.md](migration.md) 一个系统一个系统迁。没同意时，新系统照样摆进场景；往已有的代码搭系统里加东西时跟着现状写，别在同一个系统里混两种做法。
