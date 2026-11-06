# godot-scene-authoring

## SKILL.md `class_name GroundProp`

<!-- check: setup -->
```gdscript
node.texture = make_texture(16, 32)
node.height = 128.0
```

```gdscript
var packed := PackedScene.new()
packed.pack(node)
var state := packed.get_state()
var saved := PackedStringArray()
for i in state.get_node_property_count(0):
	saved.append(String(state.get_node_property_name(0, i)))
expect(saved.has("texture") and saved.has("height"), "存盘的是导出属性")
var copy := packed.instantiate() as GroundProp
expect(is_equal_approx(copy.height, 128.0) and copy.texture != null, "读回来属性还在")
copy.free()
```

## SKILL.md `@export var depth: float`

<!-- check: setup -->
```gdscript
node.depth = 5.0
```

```gdscript
expect(node.z_index == -10, "setter 按深度算 z_index")
var packed := PackedScene.new()
packed.pack(node)
var state := packed.get_state()
var saved := PackedStringArray()
for i in state.get_node_property_count(0):
	saved.append(String(state.get_node_property_name(0, i)))
expect(saved.has("depth"), "depth 存盘")
expect(not saved.has("z_index"), "z_index 去掉存盘位后不存")
var copy := packed.instantiate() as Node2D
expect(copy.z_index == -10, "读回来由 setter 重新算出")
copy.free()
```

## SKILL.md `var _shadow: Sprite2D`

```gdscript
expect(node.get_child_count() == 0, "internal 子节点不在 get_children 里")
expect(node.get_child_count(true) == 1, "get_children(true) 拿得到")
var loose := Node2D.new()
node.add_child(loose)
var copy := node.duplicate() as Node2D
expect(copy.get_child_count(true) == 1, "duplicate 不带 internal 子节点")
expect(copy.get_child(0).get_class() == "Node2D", "不设 owner 的普通子节点照样复制")
copy.free()
loose.free()

var packed := PackedScene.new()
packed.pack(node)
expect(packed.get_state().get_node_count() == 1, "不设 owner 的 internal 子节点不存盘")

var shadow := node.get_child(0, true)
shadow.owner = node
packed.pack(node)
expect(packed.get_state().get_node_count() == 2, "设了 owner 的 internal 子节点照样存盘")
var loaded := packed.instantiate()
expect(loaded.get_child_count() == 1, "读回来变成普通子节点")
loaded.free()
```

## SKILL.md `NOTIFICATION_EDITOR_PRE_SAVE`

<!-- check: setup -->
```gdscript
node.export_path = "user://room_points.json"
var spawn := Marker2D.new()
spawn.name = "Spawn"
spawn.position = Vector2(12.0, -4.0)
node.add_child(spawn)
node.add_child(Node2D.new())
```

```gdscript
node.notification(Node.NOTIFICATION_EDITOR_PRE_SAVE)
var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("user://room_points.json"))
var points: Array = data["points"]
expect(points.size() == 1, "只导出 Marker2D")
expect(points[0]["name"] == "Spawn" and is_equal_approx(float(points[0]["x"]), 12.0), "导出名字和位置")
DirAccess.remove_absolute("user://room_points.json")
```

## references/migration.md `func enter_room`

<!-- check: setup -->
```gdscript
var room := Node2D.new()
for marker_name: String in ["Open", "Locked"]:
	var marker := Marker2D.new()
	marker.name = marker_name
	var npc := Sprite2D.new()
	npc.name = "Npc"
	marker.add_child(npc)
	room.add_child(marker)
node.room_scene = make_scene(room)
```

```gdscript
node.enter_room()
var room := node.get_child(0)
expect((room.get_node("Open/Npc") as CanvasItem).visible, "取到场景里摆的节点")
expect(not (room.get_node("Locked/Npc") as CanvasItem).visible, "按条件设 visible")
```

## references/migration.md `extends EditorPlugin`

<!-- run: norun 打开场景存盘后退出编辑器 -->

## SKILL.md `ResourceSaver.save(packed`

<!-- run: mode script -->

## SKILL.md `func spawn_wave`

<!-- check: setup -->
```gdscript
var enemy := Node2D.new()
enemy.name = "Enemy"
node.enemy_scene = make_scene(enemy)
var points := node.get_node("SpawnPoints") as Node2D
for i in 2:
	var marker := Marker2D.new()
	marker.position = Vector2(50.0 * i, 0.0)
	points.add_child(marker)
```

```gdscript
var before := node.get_child_count()
node.spawn_wave()
expect(node.get_child_count() == before + 2, "每个标记点出一个")
expect(is_equal_approx((node.get_child(node.get_child_count() - 1) as Node2D).position.x, 50.0), "位置取自场景里摆的标记点")
```

## references/audit.md `func count_unowned`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://levels")
var authored := Node2D.new()
for i in 3:
	var sprite := Sprite2D.new()
	sprite.name = "Sprite%d" % i
	authored.add_child(sprite)
	sprite.owner = authored
var packed := PackedScene.new()
packed.pack(authored)
ResourceSaver.save(packed, "res://levels/authored.tscn")
authored.free()
var script := FileAccess.open("res://levels/shell.gd", FileAccess.WRITE)
script.store_string("extends Node2D\n\nfunc _ready() -> void:\n\tfor i in 5:\n\t\tadd_child(Sprite2D.new())\n")
script.close()
var shell := Node2D.new()
shell.set_script(load("res://levels/shell.gd"))
packed = PackedScene.new()
packed.pack(shell)
ResourceSaver.save(packed, "res://levels/shell.tscn")
shell.free()
```
