# godot-resources-data

## SKILL.md `class_name ItemData`

```gdscript
DirAccess.make_dir_recursive_absolute("res://data")
var path := "res://data/sword.tres"
var item := ItemData.new()
item.id = &"sword"
item.title = "Sword"
item.description = "Sharp\nblade"
item.price_curve = Curve.new()
item.tags = [&"melee", &"iron"]
expect(ResourceSaver.save(item, path) == OK, "存成 .tres")
var text := FileAccess.get_file_as_string(path)
expect(text.begins_with("[gd_resource") and text.contains('script_class="ItemData"'), ".tres 是文本并记着 script_class")
expect(text.contains('title = "Sword"') and text.contains("price_curve = SubResource"), "字段与内嵌子资源写进文件")
item = null
expect(ResourceLoader.exists(path) and not ResourceLoader.exists("res://data/none.tres"), "ResourceLoader.exists")

var a := load(path) as ItemData
var b := load(path) as ItemData
expect(a == b, "load 两次拿到同一个对象")
expect(a.id == &"sword" and a.price == 10 and a.tags.size() == 2 and a.tags[1] == &"iron", "字段读回")
expect(a.price_curve != null, "内嵌 Curve 读回")
a.price = 5
expect(b.price == 5 and (load(path) as ItemData).price == 5, "改一处处处变，后面的 load 也拿到改后的值")
a = null
b = null
expect(not ResourceLoader.has_cached(path), "没有任何引用后缓存释放")
expect((load(path) as ItemData).price == 10, "缓存释放后重新读盘")

var x := load(path) as ItemData
var y := ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_IGNORE) as ItemData
expect(x != y, "CACHE_MODE_IGNORE 得到独立副本")
x.price = 99
expect(y.price == 10 and (load(path) as ItemData) == x, "IGNORE 不写缓存")
var changed := ItemData.new()
changed.price = 7
ResourceSaver.save(changed, path)
expect((load(path) as ItemData).price == 99, "CACHE_MODE_REUSE 磁盘变了也用缓存")
var z := ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_REPLACE) as ItemData
expect(z == x and x.price == 7, "CACHE_MODE_REPLACE 刷新已缓存的同一对象")

expect(ResourceLoader.get_resource_uid(path) == -1, "运行时 ResourceSaver 不写 uid")
var uid := ResourceLoader.get_resource_uid("res://s0.gd")
expect(uid != -1, "脚本有 uid")
var uid_text := ResourceUID.id_to_text(uid)
expect(uid_text.begins_with("uid://"), "id_to_text")
expect(ResourceUID.path_to_uid("res://s0.gd") == uid_text and ResourceUID.uid_to_path(uid_text) == "res://s0.gd", "uid 与路径互转")
expect(load(uid_text) is GDScript, "load 接受 uid://")

var evil := FileAccess.open("user://evil.tres", FileAccess.WRITE)
evil.store_string('[gd_resource type="Resource" format=3]\n\n[sub_resource type="GDScript" id="GDScript_1"]\nscript/source = "extends Resource\\n\\nfunc _init() -> void:\\n\\tEngine.set_meta(&\\"pwned\\", true)\\n"\n\n[resource]\nscript = SubResource("GDScript_1")\n')
evil.close()
expect(not Engine.has_meta(&"pwned"), "加载前没有执行")
load("user://evil.tres")
expect(Engine.has_meta(&"pwned"), "load 玩家可写位置的 .tres 会执行内嵌脚本")
Engine.remove_meta(&"pwned")
```

## SKILL.md `class_name ItemDb`

```gdscript
var sword := ItemData.new()
sword.id = &"sword"
sword.title = "Sword"
var potion := ItemData.new()
potion.id = &"potion"
potion.title = "Potion"
node.items = [sword, potion]
expect(node.get_item(&"potion") == potion, "按 id 取")
expect(node.get_item(&"sword").title == "Sword", "建索引后再取")
expect(node.get_item(&"missing") == null, "未知 id 返回 null")

DirAccess.make_dir_recursive_absolute("res://data")
expect(ResourceSaver.save(node, "res://data/db.tres") == OK, "数据库资源存成 .tres")
var loaded := load("res://data/db.tres") as ItemDb
expect(loaded.items.size() == 2 and loaded.get_item(&"potion").title == "Potion", "读回后索引照常建")
```

## SKILL.md `class_name StatBlock`

<!-- check: prepare -->
```gdscript
var f := FileAccess.open("res://resist.gd", FileAccess.WRITE)
f.store_string("class_name Resist\nextends Resource\n\n@export var ratio: float = 1.0\n")
f.close()
f = FileAccess.open("res://armor.gd", FileAccess.WRITE)
f.store_string("class_name Armor\nextends Resource\n\n@export var inner: Resist\n@export var resists: Array[Resist] = []\n")
f.close()
f = FileAccess.open("res://armor_holder.gd", FileAccess.WRITE)
f.store_string("class_name ArmorHolder\nextends Node2D\n\n@export var armor: Armor\n")
f.close()
```

```gdscript
var base := Armor.new()
base.inner = Resist.new()
var one := Resist.new()
base.resists = [one]

var shallow := base.duplicate() as Armor
expect(shallow.inner == base.inner, "duplicate() 嵌套的 Resource 共享")
expect(is_same(shallow.resists, base.resists), "duplicate() 嵌套的 Array 共享")
shallow.resists[0].ratio = 0.5
expect(one.ratio == 0.5, "duplicate() 后改数组里的子资源，原件跟着变")
one.ratio = 1.0

var copy := base.duplicate(true) as Armor
expect(copy.inner != base.inner and copy.resists[0] != one and not is_same(copy.resists, base.resists), "duplicate(true) 数组和内嵌子资源都复制")
copy.resists[0].ratio = 0.25
expect(one.ratio == 1.0, "duplicate(true) 改副本不影响原件")

DirAccess.make_dir_recursive_absolute("res://data")
ResourceSaver.save(Resist.new(), "res://data/ext_resist.tres")
var ext := load("res://data/ext_resist.tres") as Resist
base.inner = ext
expect(base.duplicate(true).inner == ext, "duplicate(true) 带路径的外部资源仍共享")
expect(base.duplicate_deep(Resource.DEEP_DUPLICATE_NONE).resists[0] == one, "DEEP_DUPLICATE_NONE 不复制子资源")
var internal := base.duplicate_deep(Resource.DEEP_DUPLICATE_INTERNAL) as Armor
expect(internal.resists[0] != one and internal.inner == ext, "DEEP_DUPLICATE_INTERNAL 只复制内嵌的")
expect(base.duplicate_deep().resists[0] != one and base.duplicate_deep().inner == ext, "duplicate_deep 默认 INTERNAL")
var all := base.duplicate_deep(Resource.DEEP_DUPLICATE_ALL) as Armor
expect(all.inner != ext and all.resists[0] != one, "DEEP_DUPLICATE_ALL 连外部资源也复制")

var holder := ArmorHolder.new()
holder.name = "H"
holder.armor = Armor.new()
holder.armor.resists = [Resist.new()]
var scene := make_scene(holder)
var first := scene.instantiate() as ArmorHolder
var second := scene.instantiate() as ArmorHolder
expect(first.armor == second.armor, "同一场景实例化两次，sub_resource 共用")
first.free()
second.free()

holder = ArmorHolder.new()
holder.name = "H"
holder.armor = Armor.new()
holder.armor.resists = [Resist.new()]
holder.armor.resource_local_to_scene = true
scene = make_scene(holder)
first = scene.instantiate() as ArmorHolder
second = scene.instantiate() as ArmorHolder
expect(first.armor != second.armor, "local_to_scene 各得一份")
expect(not is_same(first.armor.resists, second.armor.resists), "数组也复制")
expect(first.armor.resists[0] == second.armor.resists[0], "数组里的子资源仍共享")
first.armor.resists[0].ratio = 0.1
expect(second.armor.resists[0].ratio == 0.1, "只勾外层时另一个实例跟着变")
first.free()
second.free()

holder = ArmorHolder.new()
holder.name = "H"
holder.armor = Armor.new()
holder.armor.resists = [Resist.new()]
holder.armor.resource_local_to_scene = true
holder.armor.resists[0].resource_local_to_scene = true
scene = make_scene(holder)
first = scene.instantiate() as ArmorHolder
second = scene.instantiate() as ArmorHolder
first.armor.resists[0].ratio = 0.1
expect(first.armor.resists[0] != second.armor.resists[0] and second.armor.resists[0].ratio == 1.0, "子资源也勾上才各得一份")
first.free()
second.free()

var shared := Armor.new()
shared.resource_local_to_scene = true
ResourceSaver.save(shared, "res://data/shared_armor.tres")
holder = ArmorHolder.new()
holder.name = "H"
holder.armor = load("res://data/shared_armor.tres") as Armor
expect(holder.armor.resource_path == "res://data/shared_armor.tres", "外部 .tres")
scene = make_scene(holder)
first = scene.instantiate() as ArmorHolder
second = scene.instantiate() as ArmorHolder
expect(first.armor != second.armor and first.armor.resource_path.is_empty(), "外部 .tres 勾了 local_to_scene 同样各得一份")
first.free()
second.free()
```

## SKILL.md `base_stats.duplicate()`

```gdscript
await frames(2)
expect(node.stats != null and node.stats != node.base_stats, "运行时副本和共享原件是两个对象")
node.stats.hp = 3
expect(node.base_stats.hp == 10, "改副本不动原件")
node.stats.speed = 5.0
expect(node.base_stats.speed == 120.0, "speed 同理")
```

## SKILL.md `func start(path`

```gdscript
await frames(2)
DirAccess.make_dir_recursive_absolute("res://scenes")
var main := Node2D.new()
main.name = "Main"
for i in 12:
	var leaf := Node2D.new()
	leaf.name = "Leaf"
	ResourceSaver.save(make_scene(leaf), "res://scenes/leaf%d.tscn" % i)
	main.add_child((load("res://scenes/leaf%d.tscn" % i) as PackedScene).instantiate())
var packed := make_scene(main)
ResourceSaver.save(packed, "res://scenes/main.tscn")
ResourceSaver.save(packed, "res://scenes/main2.tscn")

var done: Array[Resource] = []
node.finished.connect(func(res: Resource) -> void: done.append(res))
expect(not node.is_processing(), "_ready 里先关掉 _process")
node.start("res://scenes/main.tscn")
expect(node.is_processing(), "start 之后开始轮询")
var seen: Array[float] = []
var guard := 0
while done.is_empty() and guard < 600:
	seen.append(node.bar.value)
	await frames(1)
	guard += 1
expect(done.size() == 1 and done[0] is PackedScene, "加载完成发出 finished")
expect(not node.is_processing(), "完成后关掉 _process")
var previous := 0.0
for value in seen:
	expect(value >= previous and value <= 100.0, "进度条单调不超过 100")
	previous = value
var inst := (done[0] as PackedScene).instantiate()
expect(inst.get_child_count() == 12, "加载出来的场景完整")
inst.free()

ResourceLoader.load_threaded_request("res://scenes/main2.tscn")
expect(ResourceLoader.load_threaded_get("res://scenes/main2.tscn") is PackedScene, "请求后立刻 get 会阻塞到加载完")
expect(change_scene_to_packed(done[0] as PackedScene) == OK, "交给 change_scene_to_packed")
await frames(2)
expect(current_scene != null and current_scene.get_child_count() == 12, "切换后新场景在树里")

DirAccess.make_dir_recursive_absolute("res://data/items/sub")
ResourceSaver.save(Resource.new(), "res://data/items/b.tres")
ResourceSaver.save(Resource.new(), "res://data/items/a.tres")
ResourceSaver.save(Resource.new(), "res://data/items/sub/c.tres")
var names := ResourceLoader.list_directory("res://data/items")
names.sort()
expect(names == PackedStringArray(["a.tres", "b.tres", "sub/"]), "list_directory 子目录带 / 后缀 %s" % [names])
expect(ResourceLoader.list_directory("res://").has(".godot/"), "list_directory(res://) 会列出 .godot/")
expect(OS.get_user_data_dir().is_absolute_path(), "get_user_data_dir 是绝对路径")
```

## references/baking-data.md `const SRC`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://data")
var f := FileAccess.open("res://data/items.json", FileAccess.WRITE)
f.store_string('[{"id": "sword", "title": "Sword", "price": 15}, {"id": "potion", "title": "Potion", "price": 5.0}]')
f.close()
```

```gdscript
node._run()
var path := "res://data/items/sword.tres"
expect(FileAccess.file_exists(path) and FileAccess.file_exists("res://data/items/potion.tres"), "每行一个 .tres")
var text := FileAccess.get_file_as_string(path)
expect(text.contains('script_class="ItemData"') and text.contains('id = &"sword"') and text.contains('title = "Sword"') and text.contains("price = 15"), "生成的 .tres 内容 %s" % text)
expect(text.contains('uid="uid://'), "编辑器里执行会写 uid")
var sword := load(path) as ItemData
expect(sword.id == &"sword" and sword.title == "Sword" and sword.price == 15, "读回")
expect((load("res://data/items/potion.tres") as ItemData).price == 5, "浮点价格转成 int")
var uid := ResourceLoader.get_resource_uid(path)
expect(uid != -1, "有 uid")

var f := FileAccess.open("res://data/items.json", FileAccess.WRITE)
f.store_string('[{"id": "sword", "title": "Great Sword", "price": 20}]')
f.close()
node._run()
expect(ResourceLoader.get_resource_uid(path) == uid, "同路径重存 uid 保留")
expect(FileAccess.get_file_as_string(path).contains('title = "Great Sword"') and (load(path) as ItemData).price == 20, "原地更新")
```

## references/baking-data.md `terrain.json`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://data")
var f := FileAccess.open("res://data/terrain.json", FileAccess.WRITE)
f.store_string('{"vertices": [0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1], "indices": [0, 1, 2, 2, 1, 3]}')
f.close()
```

```gdscript
node._run()
var path := "res://baked/terrain.res"
expect(FileAccess.file_exists(path), "烘焙出 .res")
var magic := FileAccess.open(path, FileAccess.READ).get_buffer(4).get_string_from_ascii()
expect(magic == "RSRC", ".res 是二进制")
var mesh := load(path) as ArrayMesh
expect(mesh != null and mesh.get_surface_count() == 1, "load 直接得到 ArrayMesh")
expect(mesh.surface_get_array_len(0) == 4 and mesh.surface_get_array_index_len(0) == 6, "顶点与索引数")
var verts := mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX] as PackedVector3Array
expect(verts[3] == Vector3(1, 0, 1), "顶点内容")
```

## references/builtin-data-resources.md `damage_at`

<!-- run: mode render -->

<!-- check: setup -->
```gdscript
var curve := Curve.new()
curve.add_point(Vector2(0.0, 1.0), 0.0, -1.0)
curve.add_point(Vector2(1.0, 0.0), -1.0, 0.0)
node.falloff = curve
```

```gdscript
expect(is_equal_approx(node.damage_at(0.0, 10.0), 100.0), "近处满伤害")
expect(absf(node.damage_at(5.0, 10.0) - 50.0) < 1.0, "一半距离约一半伤害")
expect(is_zero_approx(node.damage_at(20.0, 10.0)), "超出距离被 clamp")
var curve := node.falloff
expect(curve.bake_resolution == 100, "bake_resolution 默认 100")
expect(curve.min_domain == 0.0 and curve.max_domain == 1.0, "横轴默认 0 到 1")
expect(is_equal_approx(curve.sample(0.25), 0.75) and absf(curve.sample_baked(0.25) - 0.75) < 0.02, "sample 与 sample_baked")
curve.max_domain = 10.0
expect(is_equal_approx(curve.sample(10.0), curve.sample_baked(10.0)) and curve.max_domain == 10.0, "改横轴范围")
curve.max_domain = 1.0

var gradient := Gradient.new()
gradient.set_color(0, Color.RED)
gradient.set_color(1, Color.BLUE)
var gradient_texture := GradientTexture1D.new()
expect(gradient_texture.width == 256, "GradientTexture1D width 默认 256")
gradient_texture.gradient = gradient
var curve_texture := CurveTexture.new()
curve_texture.curve = curve
var xyz := CurveXYZTexture.new()
xyz.curve_x = curve
await frames(2)
expect(curve_texture.texture_mode == CurveTexture.TEXTURE_MODE_RGB, "CurveTexture 默认 RGB 模式")
var view := TextureRect.new()
view.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
view.stretch_mode = TextureRect.STRETCH_SCALE
view.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
view.size = Vector2(256, 16)
view.texture = curve_texture
root.add_child(view)
await RenderingServer.frame_post_draw
await RenderingServer.frame_post_draw
var pixel := root.get_texture().get_image().get_pixel(1, 1)
expect(pixel.r > 0.9 and pixel.g > 0.9 and pixel.b > 0.9, "RGB 模式三个通道存同一条曲线 %s" % [pixel])
curve_texture.texture_mode = CurveTexture.TEXTURE_MODE_RED
await RenderingServer.frame_post_draw
await RenderingServer.frame_post_draw
pixel = root.get_texture().get_image().get_pixel(1, 1)
expect(pixel.r > 0.9 and pixel.g < 0.1 and pixel.b < 0.1, "TEXTURE_MODE_RED 只存红通道 %s" % [pixel])
var flat := Curve.new()
flat.add_point(Vector2(0.0, 1.0))
flat.add_point(Vector2(1.0, 1.0))
xyz.curve_y = Curve.new()
xyz.curve_y.add_point(Vector2(0.0, 0.0))
xyz.curve_y.add_point(Vector2(1.0, 0.0))
xyz.curve_z = flat
view.texture = xyz
await RenderingServer.frame_post_draw
await RenderingServer.frame_post_draw
pixel = root.get_texture().get_image().get_pixel(1, 1)
expect(pixel.r > 0.9 and pixel.g < 0.1 and pixel.b > 0.9, "CurveXYZTexture 三个通道各一条曲线 %s" % [pixel])
view.free()
var particles := ParticleProcessMaterial.new()
particles.scale_curve = curve_texture
particles.color_ramp = gradient_texture
particles.alpha_curve = curve_texture
expect(particles.scale_curve == curve_texture and particles.color_ramp == gradient_texture, "粒子材质直接吃这些纹理")
var radial := GradientTexture2D.new()
radial.fill = GradientTexture2D.FILL_RADIAL
expect(radial.fill == GradientTexture2D.FILL_RADIAL, "GradientTexture2D 径向")
var noise_texture := NoiseTexture2D.new()
noise_texture.noise = FastNoiseLite.new()
var rng := RandomNumberGenerator.new()
expect(rng.rand_weighted(PackedFloat32Array([0.0, 0.0, 1.0])) == 2, "rand_weighted 返回下标")
```

## references/builtin-data-resources.md `show_heat`

<!-- check: setup -->
```gdscript
var gradient := Gradient.new()
gradient.set_color(0, Color.RED)
gradient.set_color(1, Color.BLUE)
node.heat = gradient
```

```gdscript
node.show_heat(0.0)
expect(node.modulate == Color.RED, "0 取第一个色标")
node.show_heat(1.0)
expect(node.modulate == Color.BLUE, "1 取最后一个色标")
node.show_heat(5.0)
expect(node.modulate == Color.BLUE, "超出范围被 clamp")
node.show_heat(0.5)
expect(node.modulate.is_equal_approx(Color(0.5, 0.0, 0.5)), "中间线性插值")
```

## references/builtin-data-resources.md `point_at`

<!-- check: setup -->
```gdscript
var curve := Curve2D.new()
curve.add_point(Vector2(0, 0))
curve.add_point(Vector2(100, 0))
node.curve = curve
var follow := PathFollow2D.new()
follow.name = "Follow"
node.add_child(follow)
```

```gdscript
await frames(2)
expect(node.point_at(0.0).is_equal_approx(Vector2.ZERO), "起点")
expect(node.point_at(0.5).is_equal_approx(Vector2(50, 0)), "中点")
expect(node.point_at(1.0).is_equal_approx(Vector2(100, 0)), "终点")
var follow := node.get_node("Follow") as PathFollow2D
expect(follow.loop, "loop 默认 true")
follow.progress = 150.0
expect(is_equal_approx(follow.progress, 50.0), "超出长度回绕")
follow.loop = false
follow.progress = 150.0
expect(is_equal_approx(follow.progress, 100.0), "loop 关掉后停在末端")
var curve3d := Curve3D.new()
curve3d.add_point(Vector3.ZERO)
curve3d.add_point(Vector3(0, 0, -10))
expect(curve3d.sample_baked_with_rotation(5.0).origin.is_equal_approx(Vector3(0, 0, -5)), "sample_baked_with_rotation")
```

## references/saving-data.md `class_name SaveStore`

```gdscript
if FileAccess.file_exists(SaveStore.PATH):
	DirAccess.remove_absolute(SaveStore.PATH)
expect(SaveStore.read().is_empty(), "没有存档返回空字典")
var state := {"gold": 5, "pos": Vector2(1, 2), "ids": [1, 2], "color": Color.RED}
expect(SaveStore.write(state) == OK, "写入成功")
expect(not FileAccess.file_exists(SaveStore.PATH + ".tmp"), "tmp 已改名")
var back := SaveStore.read()
expect(back["gold"] is int and back["gold"] == 5, "int 读回还是 int")
expect(back["pos"] == Vector2(1, 2) and back["color"] == Color.RED, "Vector2 与 Color 读回")
expect(back["ids"][0] is int and back["ids"].size() == 2, "数组里的 int")

var raw := JSON.parse_string(FileAccess.get_file_as_string(SaveStore.PATH)) as Dictionary
expect(raw["type"] == "Dictionary" and raw["args"][0] == "s:version" and raw["args"][1] == "i:2", "from_native 的 Dictionary 形式，键和 int 带前缀")
expect((JSON.parse_string("[3]") as Array)[0] is float, "parse_string 的数字是 float")
expect(FileAccess.get_file_as_string(SaveStore.PATH).contains("\n\t"), "stringify 用制表符缩进")

var other := {"gold": 9}
SaveStore.write(other)
expect(SaveStore.read() == other, "第二次写入覆盖旧文件")
expect(not FileAccess.file_exists(SaveStore.PATH + ".tmp"), "覆盖后 tmp 也不在")

var legacy := FileAccess.open(SaveStore.PATH, FileAccess.WRITE)
legacy.store_string(JSON.stringify(JSON.from_native({"version": 1, "state": {"coins": 7, "level": 3}})))
legacy.close()
var migrated := SaveStore.read()
expect(migrated == {"gold": 7, "level": 3}, "version 1 的 coins 迁移成 gold %s" % [migrated])
expect(not migrated.has("coins"), "旧键被删")

legacy = FileAccess.open(SaveStore.PATH, FileAccess.WRITE)
legacy.store_string(JSON.stringify(JSON.from_native({"state": {"coins": 2}})))
legacy.close()
expect(SaveStore.read() == {"gold": 2}, "没有 version 字段按 1 处理")

legacy = FileAccess.open(SaveStore.PATH, FileAccess.WRITE)
legacy.store_string("[1, 2]")
legacy.close()
expect(SaveStore.read().is_empty(), "不是 Dictionary 返回空字典")

legacy = FileAccess.open(SaveStore.PATH, FileAccess.WRITE)
legacy.store_string('{"type": "PackedInt32Array", "args": [1, 2]}')
legacy.close()
expect(SaveStore.read().is_empty(), "合法 JSON 但还原出来不是 Dictionary 也返回空字典")

expect(ProjectSettings.has_setting("application/config/use_custom_user_dir") and ProjectSettings.has_setting("application/config/custom_user_dir_name"), "自定义 user 目录的项目设置")

var cfg := ConfigFile.new()
expect(cfg.parse('[a]\nb=Object(Node,"name":"evil")') == OK, "ConfigFile 解析 Object(...)")
var obj: Variant = cfg.get_value("a", "b")
expect(obj is Node, "ConfigFile 会实例化文本里的 Object")
(obj as Node).free()
var made: Variant = str_to_var('Object(Node,"name":"evil")')
expect(made is Node, "str_to_var 会实例化 Object")
(made as Node).free()

var encrypted := FileAccess.open_encrypted_with_pass("user://enc.bin", FileAccess.WRITE, "pw")
encrypted.store_string("secret")
encrypted.close()
expect(FileAccess.open_encrypted_with_pass("user://enc.bin", FileAccess.READ, "pw").get_as_text() == "secret", "加密读回")
expect(FileAccess.get_file_as_bytes("user://enc.bin").get_string_from_ascii().find("secret") == -1, "明文读不到")
var encrypted_cfg := ConfigFile.new()
encrypted_cfg.set_value("a", "b", 1)
expect(encrypted_cfg.save_encrypted_pass("user://enc.cfg", "pw") == OK, "ConfigFile.save_encrypted_pass")
```

## references/saving-data.md `class_name PlayerState`

```gdscript
node.gold = 12
node.item_ids = [&"sword", &"potion"]
var data := node.to_dict()
var direct := PlayerState.from_dict(data)
expect(direct.gold == 12 and direct.item_ids == node.item_ids, "字典直接读回")
var parsed := JSON.parse_string(JSON.stringify(data)) as Dictionary
expect(parsed["gold"] is float, "JSON 读回的 gold 是 float")
var back := PlayerState.from_dict(parsed)
expect(back.gold == 12 and back.item_ids.size() == 2 and back.item_ids[0] == &"sword", "经 JSON 往返")
expect(PlayerState.from_dict({}).gold == 0 and PlayerState.from_dict({}).item_ids.is_empty(), "缺字段回到默认值")
```

## references/saving-data.md `func save_volume`

```gdscript
if FileAccess.file_exists(node.PATH):
	DirAccess.remove_absolute(node.PATH)
expect(node.load_volume() == 1.0, "没有文件返回默认值")
node.save_volume(0.25)
expect(is_equal_approx(node.load_volume(), 0.25), "存取往返")
var cfg := ConfigFile.new()
cfg.load(node.PATH)
cfg.set_value("video", "vsync", true)
cfg.save(node.PATH)
node.save_volume(0.5)
cfg = ConfigFile.new()
cfg.load(node.PATH)
expect(cfg.get_value("video", "vsync") == true and is_equal_approx(cfg.get_value("audio", "master"), 0.5), "保存前先 load 保留别的段落")
```
