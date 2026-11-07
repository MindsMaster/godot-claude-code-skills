# 自查

判断项目内容摆在场景里还是运行时生成：场景文件、代码搜索、无头审计、报告格式。结论按系统给，HUD、菜单、关卡、NPC、背景各算一项。

## 场景文件

数每个场景的节点数，节点少、根脚本长的是嫌疑：

```
find . -name "*.tscn" -not -path "./addons/*" -not -path "./.godot/*" | while read -r f; do
	printf "%4d %s\n" "$(grep -c '^\[node ' "$f")" "$f"
done | sort -n | head -40
```

| 现象 | 结论 |
|---|---|
| 关卡、HUD、菜单只有 1 到 3 个节点，脚本几百行 | 内容运行时建 |
| 节点数和游戏画面对得上 | 已摆在场景里 |

- 最直接的办法：打开编辑器看场景面板和视口

## 代码搜索

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

| 命中位置 | 结论 |
|---|---|
| `_ready`、`build()`、`setup()`、`enter_room()` 里建背景、面板、标签、装饰 | 内容运行时建 |
| 生成敌人、子弹、列表行的函数里 `new` 节点再设外观 | 应做成预制场景，小问题 |
| 配表同时有坐标和贴图路径 | 外观在数据里 |
| 自绘 `_draw` 的脚本没有 `@tool` | 编辑器里看不见 |
| 按种子生成地图、按数据数量建列表行 | 正常的运行时内容 |

## 无头审计

逐个实例化场景、等两帧，数 owner 为空的节点。摆的节点 owner 是场景根，运行时 `add_child` 的 owner 为空。C# 项目同样用这个 GDScript 脚本：

<!-- check: gdonly -->
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

| 输出 | 结论 |
|---|---|
| `added` 远大于 `saved` | 运行时搭的 |
| `added` 为 0 或只有几个预制实例 | 摆好的 |
| 场景报错 | 依赖 autoload 或传参，不能单独打开，编辑器里多半也是空的 |

- `DIRS` 只放关卡和 UI 目录
- 实例化会跑游戏代码，可能联网、写存档、切场景，在干净的工作副本上跑
- 跑完删掉脚本

## 报告

迁移是大改动，先报告再动手：

| 系统 | 现状 | 证据 | 建议 |
|---|---|---|---|
| 关卡 | 运行时按 `rooms.json` 建 | `level.tscn` 2 个节点，`added` 140 | 迁进场景 |
| HUD | 摆在场景里 | `hud.tscn` 38 个节点，`added` 0 | 不动 |
| 敌人 | 代码 `new Sprite2D` | `spawner.gd:40` | 做成预制场景 |

- 用户同意后按 [migration.md](migration.md) 一个系统一个系统迁
- 未同意时，新系统摆进场景，已有的代码搭系统跟着现状写
