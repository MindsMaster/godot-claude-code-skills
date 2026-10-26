# godot-performance

## SKILL.md `game/bullets`

```gdscript
await frames(2)
expect(Performance.has_custom_monitor("game/bullets"), "_ready 里注册了监视器")
expect(Performance.get_custom_monitor("game/bullets") == 0, "初始 0 颗")
node._bullets = 7
expect(Performance.get_custom_monitor("game/bullets") == 7, "监视器读回调返回值")
expect(Performance.get_custom_monitor_names().has("game/bullets"), "id 在名单里")
var orphan := Node.new()
expect(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT) >= 1.0, "孤儿节点监视器计入未进树的节点")
var count_before := Performance.get_monitor(Performance.OBJECT_NODE_COUNT)
var doomed := Node.new()
root.add_child(doomed)
doomed.queue_free()
expect(Performance.get_monitor(Performance.OBJECT_NODE_COUNT) == count_before + 1.0, "queue_free 的节点同一帧里仍计数")
orphan.free()
await frames(2)
expect(Performance.get_monitor(Performance.OBJECT_NODE_COUNT) == count_before, "帧末释放后节点数回落")
root.remove_child(node)
expect(not Performance.has_custom_monitor("game/bullets"), "_exit_tree 里注销了监视器")
```

## SKILL.md `func activate`

<!-- run: mode render -->

```gdscript
await frames(5)
expect(not node.is_processing() and not node.is_physics_processing(), "_ready 里关了两个回调")
expect(is_zero_approx(node.position.x), "关着不动")
node.activate()
await frames(10)
expect(node.is_physics_processing() and node.position.x > 10.0, "activate 后 _physics_process 在跑")
var x_hidden := node.position.x
node.hide()
await frames(5)
expect(node.position.x > x_hidden, "hide() 不停回调")
var x_disabled := node.position.x
node.process_mode = Node.PROCESS_MODE_DISABLED
await frames(5)
expect(is_equal_approx(node.position.x, x_disabled), "PROCESS_MODE_DISABLED 停回调")
var enabler := VisibleOnScreenEnabler2D.new()
expect(enabler.enable_node_path == NodePath(".."), "enable_node_path 默认父节点")
expect(enabler.enable_mode == VisibleOnScreenEnabler2D.ENABLE_MODE_INHERIT, "enable_mode 默认 INHERIT")
enabler.free()
var enemy := Node2D.new()
var zone := VisibleOnScreenEnabler2D.new()
zone.rect = Rect2(-64.0, -64.0, 128.0, 128.0)
enemy.add_child(zone)
enemy.position = Vector2(5000.0, 5000.0)
root.add_child(enemy)
await frames(3)
await RenderingServer.frame_post_draw
expect(enemy.process_mode == Node.PROCESS_MODE_DISABLED, "区域在屏幕外时目标被禁用")
enemy.position = Vector2(200.0, 200.0)
await frames(3)
await RenderingServer.frame_post_draw
expect(enemy.process_mode == Node.PROCESS_MODE_INHERIT, "区域进入屏幕后按 enable_mode 启用")
enemy.free()
```

## SKILL.md `func show_count`

<!-- run: mode render -->

```gdscript
await frames(2)
expect(node.multimesh.instance_count == 2000 and node.multimesh.visible_instance_count == 0, "一次分配 2000，起始显示 0")
node.show_count(5)
expect(node.multimesh.visible_instance_count == 5, "visible_instance_count 控制显示数量")
expect(node.multimesh.get_instance_transform_2d(3).origin.is_equal_approx(Vector2(30.0, 0.0)), "实例 3 的位置")
expect(node.multimesh.get_instance_color(3) == Color.WHITE, "实例颜色")
var big := MultiMesh.new()
big.transform_format = MultiMesh.TRANSFORM_3D
big.use_colors = true
big.use_custom_data = true
big.instance_count = 2
expect(big.buffer.size() == 2 * (12 + 4 + 4), "3D 带颜色和自定义数据每实例 20 个 float")
var small := MultiMesh.new()
small.transform_format = MultiMesh.TRANSFORM_2D
small.use_colors = true
small.instance_count = 2
expect(small.buffer.size() == 2 * (8 + 4), "2D 带颜色每实例 12 个 float")
small.buffer = PackedFloat32Array([1, 0, 0, 5, 0, 1, 0, 6, 1, 0, 0, 1, 1, 0, 0, 7, 0, 1, 0, 8, 0, 1, 0, 1])
expect(small.get_instance_transform_2d(1).origin.is_equal_approx(Vector2(7.0, 8.0)), "2D 行主序 origin 在第 4 和第 8 个")
expect(small.get_instance_color(1) == Color(0, 1, 0, 1), "颜色接在变换后")
```

## SKILL.md `WorkerThreadPool.add_group_task`

```gdscript
node.start(2000)
var deadline := Time.get_ticks_msec() + 5000
while node._task_id != -1 and Time.get_ticks_msec() < deadline:
	await frames(1)
expect(node._task_id == -1, "任务完成后 _process 里回收")
expect(is_equal_approx(node._results[1999], sqrt(1999.0)) and is_equal_approx(node._results[4], 2.0), "每个元素都被算到")
node.start(200000)
node.queue_free()
```

## SKILL.md `load_threaded_request`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://levels")
var level := Node2D.new()
level.name = "Level1"
var packed := PackedScene.new()
packed.pack(level)
ResourceSaver.save(packed, "res://levels/level_1.tscn")
level.free()
```

```gdscript
await frames(2)
expect(not node.is_processing(), "_ready 里先关 _process")
node.start_load()
expect(node.is_processing(), "start_load 打开 _process")
var deadline := Time.get_ticks_msec() + 5000
while current_scene == null and Time.get_ticks_msec() < deadline:
	await frames(1)
await frames(3)
expect(node._progress.size() == 1, "progress 数组只有一个元素")
expect(current_scene != null and current_scene.name == "Level1", "加载完后切到新场景")
expect(not node.is_processing(), "加载完停止轮询")
```

## references/hotspots.md `canvas_item_add_texture_rect`

<!-- run: mode render -->

```gdscript
node.spawn(make_texture(32, 32, Color.WHITE), Vector2(200.0, 300.0))
node.spawn(make_texture(32, 32, Color.WHITE), Vector2(500.0, 300.0))
await frames(3)
await RenderingServer.frame_post_draw
var image := root.get_texture().get_image()
expect(image.get_pixel(200, 290).is_equal_approx(Color.WHITE), "第一颗子弹画在 canvas_item 父节点下")
expect(image.get_pixel(500, 290).is_equal_approx(Color.WHITE), "第二颗子弹")
expect(not image.get_pixel(350, 290).is_equal_approx(Color.WHITE), "两颗之间是背景")
expect(node._positions.size() == 2 and node._positions[0].y < 300.0, "_process 里向上移动")
expect(node._items.size() == 2, "两个 RID 记录在案")
```

## references/hotspots.md `bullet_scene`

<!-- check: setup -->
```gdscript
node.bullet_scene = make_scene(Node2D.new())
```

```gdscript
var first := node.acquire()
var second := node.acquire()
expect(first != second and first.get_parent() == node and node.get_child_count() == 2, "池空时各自实例化并挂上")
node.release(first)
expect(first.get_parent() == null and node.get_child_count() == 1, "release 摘出场景树")
var third := node.acquire()
expect(third == first, "复用池里的节点")
node.release(first)
```

## references/hotspots.md `func fill`

<!-- run: mode render -->

```gdscript
node.fill(4)
await frames(2)
expect(node.multimesh.instance_count == 4, "4 个实例")
expect(node.multimesh.get_instance_transform_2d(2) == Transform2D(Vector2(1.0, 0.0), Vector2(0.0, 1.0), Vector2(20.0, 0.0)), "buffer 的 8 个 float 布局")
expect(node.multimesh.buffer.size() == 32, "buffer 长度是实例数乘 8")
```

## references/hotspots.md `_enemies_by_id`

<!-- check: setup -->
```gdscript
var boss := Node2D.new()
boss.name = "Boss"
boss.add_to_group(&"boss")
root.add_child(boss)
```

```gdscript
await frames(2)
expect(node._boss == get_first_node_in_group(&"boss"), "_ready 里取到分组里的 boss")
var enemy := Node2D.new()
root.add_child(enemy)
node.register(enemy, 7)
expect(node._enemies_by_id.get(7) == enemy, "按 id 索引")
enemy.queue_free()
await frames(2)
expect(not node._enemies_by_id.has(7), "tree_exited 清掉索引")
get_first_node_in_group(&"boss").free()
```

## references/hotspots.md `debug_label`

```gdscript
await frames(3)
expect(node.debug_label.text.begins_with("nodes "), "调试构建里更新了文字")
expect(OS.is_debug_build() and not OS.has_feature("template"), "编辑器二进制是调试构建且不是导出模板")
```

## references/profiling.md `Performance.TIME_PROCESS`

```gdscript
await frames(3)
expect(node.visible == OS.is_debug_build(), "调试构建里显示")
expect(node.text.contains("fps") and node.text.contains("draws"), "叠加文字")
expect(Performance.get_monitor(Performance.MEMORY_STATIC) > 0.0, "MEMORY_STATIC 调试构建可用")
```

## references/profiling.md `func measure`

```gdscript
var per_call := node.measure(func() -> void: OS.delay_usec(1000), 20)
expect(per_call >= 1000.0 and per_call < 20000.0, "单次约 1000 微秒")
expect(node.measure(func() -> void: pass) >= 0.0, "默认 1000 次")
```

## references/many-entities.md `_members`

```gdscript
var a := Node2D.new()
var b := Node2D.new()
root.add_child(a)
root.add_child(b)
node.register(a)
node.register(b)
await frames(10)
expect(not a.is_physics_processing(), "实体自己的回调关掉")
expect(a.position.x > 5.0 and is_equal_approx(a.position.x, b.position.x), "管理器每帧推进全部实体")
b.free()
await frames(2)
expect(node._members.size() == 1, "离树时从列表移除")
a.free()
```

## references/many-entities.md `func _flush_doomed`

<!-- run: mode render -->

```gdscript
node.spawn(Vector2(0.0, 0.0), Vector2.ZERO)
node.spawn(Vector2(10.0, 0.0), Vector2(0.0, -100000.0))
node.spawn(Vector2(20.0, 0.0), Vector2.ZERO)
await frames(2)
expect(node._count == 2, "飞出界的那个被删")
expect(node._positions[1].is_equal_approx(Vector2(20.0, 0.0)), "末尾元素搬进空位")
expect(node.multimesh.visible_instance_count == 2, "visible_instance_count 跟着活跃数")
expect(node.multimesh.get_instance_transform_2d(1).origin.is_equal_approx(Vector2(20.0, 0.0)), "实例按新下标写")
node.kill(0)
node.kill(0)
node._flush_doomed()
expect(node._count == 1 and node._positions[0].is_equal_approx(Vector2(20.0, 0.0)), "重复登记只删一次")
for i in node.CAPACITY:
	node.spawn(Vector2.ZERO, Vector2.ZERO)
expect(node._count == node.CAPACITY and not node.spawn(Vector2.ZERO, Vector2.ZERO), "满了拒绝")
```

## references/many-entities.md `func query`

```gdscript
var points := PackedVector2Array([Vector2(10.0, 10.0), Vector2(70.0, 10.0), Vector2(300.0, 300.0), Vector2(-20.0, 5.0)])
node.rebuild(points, 4)
expect(node._cells.size() == 4, "四个点落在四格")
var near: PackedInt32Array = node.query(Vector2(20.0, 10.0), 60.0, points)
near.sort()
expect(near == PackedInt32Array([0, 1, 3]), "半径内跨格的邻居都找到")
expect(node.query(Vector2(1000.0, 1000.0), 10.0, points).is_empty(), "空格子直接跳过")
node.rebuild(points, 2)
expect(node.query(Vector2(300.0, 300.0), 10.0, points).is_empty(), "只登记前 count 个")
```

## references/crowd-characters.md `desired_direction`

<!-- check: setup -->
```gdscript
var capsule := CollisionShape3D.new()
var shape := CapsuleShape3D.new()
shape.radius = 0.4
shape.height = 1.8
capsule.shape = shape
node.add_child(capsule)
node.position = Vector3(0.0, 1.0, 0.0)
var floor_body := StaticBody3D.new()
var floor_shape := CollisionShape3D.new()
var box := BoxShape3D.new()
box.size = Vector3(40.0, 1.0, 40.0)
floor_shape.shape = box
floor_body.add_child(floor_shape)
floor_body.position = Vector3(0.0, -0.5, 0.0)
root.add_child(floor_body)
```

```gdscript
await frames(60)
expect(node.is_on_floor(), "落地")
var rest := node.position
await frames(10)
expect(node.position.is_equal_approx(rest) and node.is_on_floor(), "静止跳过时位置与地面状态不变")
node.desired_direction = Vector3(1.0, 0.0, 0.0)
await frames(15)
expect(node.position.x > rest.x + 0.5 and node.is_on_floor(), "有速度时照常移动")
node.desired_direction = Vector3.ZERO
await frames(5)
var stop := node.position
await frames(5)
expect(node.position.is_equal_approx(stop) and node.is_on_floor(), "停下后又跳过")
```

## references/crowd-characters.md `velocity_computed`

```gdscript
await frames(2)
expect(node._agent.avoidance_enabled and is_equal_approx(node._agent.neighbor_distance, 4.0), "_ready 里开了避让")
node.desired_velocity = Vector3(2.0, 0.0, 0.0)
await frames(20)
expect(node.velocity.is_equal_approx(Vector3(2.0, 0.0, 0.0)), "没有邻居时安全速度等于期望速度")
expect(node.position.x > 0.3, "回调里 move_and_slide 推进")
var agent := NavigationAgent3D.new()
expect(is_equal_approx(agent.neighbor_distance, 50.0) and agent.max_neighbors == 10 and not agent.use_3d_avoidance, "默认值")
agent.free()
```

## references/render-submission.md `func upload`

<!-- run: mode render -->

```gdscript
await frames(2)
expect(RenderingServer.mesh_surface_get_format_vertex_stride(node._mesh.surface_get_format(0), node.MAX_VERTS) == node.VERTEX_BYTES, "只有位置时每顶点 12 字节")
var tri := PackedVector3Array([Vector3(0.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0), Vector3(1.0, 1.0, 0.0), Vector3(2.0, 1.0, 0.0), Vector3(1.0, 2.0, 0.0)])
node.upload(tri)
await frames(1)
var verts: PackedVector3Array = node._mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
expect(verts.size() == node.MAX_VERTS, "容量不变")
expect(verts[4].is_equal_approx(Vector3(2.0, 1.0, 0.0)), "局部写入生效")
node.upload(tri.slice(0, 3))
await frames(1)
verts = node._mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
expect(verts[1].is_equal_approx(Vector3(1.0, 0.0, 0.0)) and verts[4].is_zero_approx(), "变少时尾部清零")
expect(RenderingServer.mesh_get_custom_aabb(node._mesh.get_rid()).is_equal_approx(node._mesh.custom_aabb), "custom_aabb 交给了渲染服务器")
```

## references/engine-fast-paths.md `func world_outline`

```gdscript
node.position = Vector2(10.0, 0.0)
node.rotation = PI / 2.0
await frames(1)
var out: PackedVector2Array = node.world_outline(PackedVector2Array([Vector2(1.0, 0.0)]))
expect(out[0].is_equal_approx(Vector2(10.0, 1.0)), "整组乘全局变换")
var back := PackedVector2Array([Vector2(10.0, 1.0)]) * node.global_transform
expect(back[0].is_equal_approx(Vector2(1.0, 0.0)), "数组在左是逆变换")
expect(node.joined(PackedStringArray(["a", "b", "c"])) == "a, b, c", "join 一次拼好")
```
