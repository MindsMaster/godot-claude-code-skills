# godot-2d

## SKILL.md `const JUMP`

<!-- check: setup -->
```gdscript
var body_shape := CollisionShape2D.new()
body_shape.shape = RectangleShape2D.new()
(body_shape.shape as RectangleShape2D).size = Vector2(16, 16)
node.add_child(body_shape)
```

```gdscript
var floor_body := StaticBody2D.new()
var floor_shape := CollisionShape2D.new()
floor_shape.shape = RectangleShape2D.new()
(floor_shape.shape as RectangleShape2D).size = Vector2(2000, 20)
floor_body.add_child(floor_shape)
floor_body.position = Vector2(0, 100)
node.get_parent().add_child(floor_body)
await frames(60)
expect(node.is_on_floor(), "落到地面后 is_on_floor")
var start_x := node.position.x
Input.action_press("right")
await frames(30)
Input.action_release("right")
expect(is_equal_approx(node.velocity.x, 160.0), "按右键 velocity.x 为 SPEED")
expect(node.position.x - start_x > 70.0, "半秒向右走了约 80 像素")
Input.action_press("jump")
await frames(2)
Input.action_release("jump")
expect(node.velocity.y < 0.0 or node.position.y < 82.0, "按跳跃键向上")
await frames(90)
expect(node.is_on_floor(), "落回地面")
floor_body.queue_free()
```

## SKILL.md `Input.get_vector`

<!-- check: setup -->
```gdscript
node.motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
var body_shape := CollisionShape2D.new()
body_shape.shape = RectangleShape2D.new()
(body_shape.shape as RectangleShape2D).size = Vector2(16, 16)
node.add_child(body_shape)
```

```gdscript
var wall := StaticBody2D.new()
var wall_shape := CollisionShape2D.new()
wall_shape.shape = RectangleShape2D.new()
(wall_shape.shape as RectangleShape2D).size = Vector2(2000, 20)
wall.add_child(wall_shape)
wall.position = Vector2(0, 30)
node.get_parent().add_child(wall)
Input.action_press("down")
Input.action_press("right")
await frames(30)
expect(not node.is_on_floor(), "floating 模式没有地面")
expect(node.is_on_wall(), "floating 模式所有碰撞按墙处理")
expect(is_equal_approx(node.velocity.x, 120.0 / sqrt(2.0)) or node.velocity.x > 80.0, "沿墙滑动速度保持")
Input.action_release("down")
Input.action_release("right")
Input.action_press("right")
var before := node.position.x
await frames(30)
Input.action_release("right")
expect(absf((node.position.x - before) - 60.0) < 2.0, "俯视角半秒 60 像素")
wall.queue_free()
```

## SKILL.md `signal collected`

<!-- check: setup -->
```gdscript
var area_shape := node.get_node("CollisionShape2D") as CollisionShape2D
area_shape.shape = RectangleShape2D.new()
(area_shape.shape as RectangleShape2D).size = Vector2(32, 32)
```

```gdscript
var got: Array[Node2D] = []
node.collected.connect(func(by: Node2D) -> void: got.append(by))
var body := CharacterBody2D.new()
var body_shape := CollisionShape2D.new()
body_shape.shape = RectangleShape2D.new()
(body_shape.shape as RectangleShape2D).size = Vector2(8, 8)
body.add_child(body_shape)
body.position = Vector2(500, 0)
node.get_parent().add_child(body)
await frames(3)
expect(node.get_overlapping_bodies().is_empty(), "远处没有重叠")
body.position = Vector2.ZERO
expect(node.get_overlapping_bodies().is_empty(), "刚移动完立刻查不到")
await frames(3)
expect(got.size() == 1 and got[0] == body, "body_entered 触发一次 collected")
expect((node.get_node("CollisionShape2D") as CollisionShape2D).disabled, "set_deferred 禁用了形状")
body.queue_free()
```

## SKILL.md `_ground.get_collision_point`

<!-- check: setup -->
```gdscript
var body_shape := CollisionShape2D.new()
body_shape.shape = RectangleShape2D.new()
(body_shape.shape as RectangleShape2D).size = Vector2(16, 16)
node.add_child(body_shape)
var probe := node.get_node("GroundProbe") as RayCast2D
probe.target_position = Vector2(0, 12)
probe.collision_mask = 1
```

```gdscript
var probe := node.get_node("GroundProbe") as RayCast2D
await frames(2)
expect(not probe.is_colliding(), "没有地面时不碰撞，exclude_parent 排除自己")
var floor_body := StaticBody2D.new()
var floor_shape := CollisionShape2D.new()
floor_shape.shape = RectangleShape2D.new()
(floor_shape.shape as RectangleShape2D).size = Vector2(200, 10)
floor_body.add_child(floor_shape)
floor_body.position = Vector2(0, 10)
node.get_parent().add_child(floor_body)
await frames(2)
expect(probe.is_colliding(), "脚下有地面")
expect(probe.get_collider() == floor_body, "碰到地面")
expect(is_equal_approx(probe.get_collision_point().y, 5.0), "碰撞点在地面上沿")
probe.target_position = Vector2(0, 2)
expect(probe.is_colliding(), "改 target_position 后不 force 仍是旧结果")
probe.force_raycast_update()
expect(not probe.is_colliding(), "force_raycast_update 后立刻是新结果")
probe.enabled = false
probe.target_position = Vector2(0, 12)
probe.force_raycast_update()
expect(probe.is_colliding(), "enabled 为 false 时 force_raycast_update 仍然有效")
floor_body.queue_free()
```

## SKILL.md `PhysicsRayQueryParameters2D.create`

<!-- check: setup -->
```gdscript
var body_shape := CollisionShape2D.new()
body_shape.shape = RectangleShape2D.new()
(body_shape.shape as RectangleShape2D).size = Vector2(16, 16)
node.add_child(body_shape)
node.position = Vector2(100, 0)
```

```gdscript
var wall := StaticBody2D.new()
var wall_shape := CollisionShape2D.new()
wall_shape.shape = RectangleShape2D.new()
(wall_shape.shape as RectangleShape2D).size = Vector2(10, 200)
wall.add_child(wall_shape)
wall.position = Vector2(50, 0)
wall.collision_layer = 1 << 2
node.get_parent().add_child(wall)
await frames(2)
Input.action_press("fire")
await frames(3)
Input.action_release("fire")
var space := node.get_world_2d().direct_space_state
var query := PhysicsRayQueryParameters2D.create(node.global_position, Vector2.ZERO, (1 << 0) | (1 << 2), [node.get_rid()])
var hit := space.intersect_ray(query)
expect(hit.collider == wall, "mask 含第 3 层时命中墙")
expect(is_equal_approx(hit.position.x, 55.0), "命中点在墙右侧面")
for key: String in ["position", "normal", "collider", "collider_id", "rid", "shape"]:
	expect(hit.has(key), "intersect_ray 结果有 " + key)
var other := PhysicsRayQueryParameters2D.create(node.global_position, Vector2.ZERO, 1 << 1)
expect(space.intersect_ray(other).is_empty(), "mask 不含墙所在层时为空")
var plain := PhysicsRayQueryParameters2D.new()
expect(plain.collision_mask == 0xffffffff, "查询参数 mask 默认全部层")
expect(not plain.collide_with_areas and plain.collide_with_bodies, "查询参数默认不打 Area2D")
expect(not PhysicsPointQueryParameters2D.new().collide_with_areas, "点查询默认不打 Area2D")
expect(not PhysicsShapeQueryParameters2D.new().collide_with_areas, "形状查询默认不打 Area2D")
var inside := PhysicsRayQueryParameters2D.create(node.global_position, node.global_position + Vector2(60, 0), 0xffffffff)
expect(space.intersect_ray(inside).is_empty(), "体内出发默认不命中自己")
inside.hit_from_inside = true
expect(space.intersect_ray(inside).get("collider") == node, "hit_from_inside 命中自己")
inside.exclude = [node.get_rid()]
expect(space.intersect_ray(inside).is_empty(), "exclude 排除自己")
var through := PhysicsRayQueryParameters2D.create(node.global_position + Vector2(30, 0), node.global_position + Vector2(-30, 0), 0xffffffff)
expect(space.intersect_ray(through).get("collider") == node, "射线穿过自己的形状会命中自己")
wall.queue_free()
```

## references/physics-queries.md `_ledge`

<!-- check: setup -->
```gdscript
var probe := node.get_node("LedgeProbe") as ShapeCast2D
probe.shape = RectangleShape2D.new()
(probe.shape as RectangleShape2D).size = Vector2(8, 8)
probe.position.x = 20.0
```

```gdscript
var probe := node.get_node("LedgeProbe") as ShapeCast2D
expect(probe.max_results == 32 and probe.collision_mask == 1 and is_zero_approx(probe.margin), "ShapeCast2D 默认值")
expect(not probe.collide_with_areas and probe.exclude_parent, "ShapeCast2D 默认不打 Area2D 且排除父级")
expect(probe.target_position == Vector2(0, 50), "ShapeCast2D 默认 target_position")
expect(not node.has_ground_ahead(1.0), "没有地面")
var ground := StaticBody2D.new()
var ground_shape := CollisionShape2D.new()
ground_shape.shape = RectangleShape2D.new()
(ground_shape.shape as RectangleShape2D).size = Vector2(100, 10)
ground.add_child(ground_shape)
ground.position = Vector2(50, 30)
node.get_parent().add_child(ground)
await frames(2)
expect(node.has_ground_ahead(1.0), "右侧有地面")
expect(probe.position.x == 20.0, "朝右时 x 为正")
expect(not node.has_ground_ahead(-1.0), "左侧悬空")
expect(probe.position.x == -20.0, "朝左时 x 为负")
probe.position.x = 20.0
probe.enabled = false
probe.force_shapecast_update()
expect(probe.is_colliding(), "enabled 为 false 时 force_shapecast_update 仍有效")
probe.enabled = true
probe.target_position = Vector2.ZERO
probe.position = Vector2(50, 30)
probe.force_shapecast_update()
expect(probe.is_colliding() and probe.get_collision_count() == 1, "target_position 为零时当场重叠检测")
expect(probe.get_collider(0) == ground, "重叠的是 ground")
var ray := RayCast2D.new()
expect(ray.target_position == Vector2(0, 50) and ray.collision_mask == 1, "RayCast2D 默认值")
expect(not ray.collide_with_areas and ray.collide_with_bodies and ray.exclude_parent and not ray.hit_from_inside, "RayCast2D 默认开关")
expect(ray.enabled, "RayCast2D 默认启用")
ray.free()
ground.queue_free()
```

## references/physics-queries.md `func enemies_in_radius`

```gdscript
var parent := node.get_parent()
var make_body := func(pos: Vector2, layer: int) -> StaticBody2D:
	var body := StaticBody2D.new()
	var shape := CollisionShape2D.new()
	shape.shape = RectangleShape2D.new()
	(shape.shape as RectangleShape2D).size = Vector2(4, 4)
	body.add_child(shape)
	body.position = pos
	body.collision_layer = layer
	parent.add_child(body)
	return body
var near: StaticBody2D = make_body.call(Vector2(10, 0), 1)
var far: StaticBody2D = make_body.call(Vector2(100, 0), 1)
var other_layer: StaticBody2D = make_body.call(Vector2(20, 0), 2)
var area := Area2D.new()
var area_shape := CollisionShape2D.new()
area_shape.shape = RectangleShape2D.new()
(area_shape.shape as RectangleShape2D).size = Vector2(4, 4)
area.add_child(area_shape)
area.position = Vector2(0, 10)
parent.add_child(area)
await frames(2)
var found: Array[Node2D] = node.enemies_in_radius(Vector2.ZERO, 30.0, 1)
expect(found.size() == 2 and found.has(near) and found.has(area), "半径内的 body 与 Area2D")
expect(not found.has(far) and not found.has(other_layer), "半径外与 mask 外的不返回")
expect(node.enemies_in_radius(Vector2.ZERO, 30.0, 2) == [other_layer], "mask 选第 2 层")
var crowd: Array[StaticBody2D] = []
for i in 40:
	crowd.append(make_body.call(Vector2(500, 0), 4))
await frames(2)
var query := PhysicsShapeQueryParameters2D.new()
var circle := CircleShape2D.new()
circle.radius = 20.0
query.shape = circle
query.transform = Transform2D(0.0, Vector2(500, 0))
query.collision_mask = 4
var space := node.get_world_2d().direct_space_state
expect(space.intersect_shape(query).size() == 32, "max_results 默认 32")
expect(space.intersect_shape(query, 40).size() == 40, "max_results 可调")
expect(node.enemies_in_radius(Vector2(500, 0), 20.0, 4).size() == 16, "示例传 16")
for method: String in ["cast_motion", "collide_shape", "get_rest_info"]:
	expect(ClassDB.class_has_method("PhysicsDirectSpaceState2D", method), "有方法 " + method)
for body in crowd:
	body.queue_free()
near.queue_free()
far.queue_free()
other_layer.queue_free()
area.queue_free()
```

## references/physics-queries.md `func clickable_at`

```gdscript
var parent := node.get_parent()
var area := Area2D.new()
var area_shape := CollisionShape2D.new()
area_shape.shape = RectangleShape2D.new()
(area_shape.shape as RectangleShape2D).size = Vector2(20, 20)
area.add_child(area_shape)
area.position = Vector2(50, 50)
parent.add_child(area)
var concave := StaticBody2D.new()
var concave_shape := CollisionShape2D.new()
var concave_polygon := ConcavePolygonShape2D.new()
concave_polygon.segments = PackedVector2Array([Vector2(-20, -20), Vector2(20, -20), Vector2(20, -20), Vector2(20, 20), Vector2(20, 20), Vector2(-20, 20), Vector2(-20, 20), Vector2(-20, -20)])
concave_shape.shape = concave_polygon
concave.add_child(concave_shape)
concave.position = Vector2(200, 0)
parent.add_child(concave)
var segments := StaticBody2D.new()
var segments_polygon := CollisionPolygon2D.new()
segments_polygon.build_mode = CollisionPolygon2D.BUILD_SEGMENTS
segments_polygon.polygon = PackedVector2Array([Vector2(-20, -20), Vector2(20, -20), Vector2(20, 20), Vector2(-20, 20)])
segments.add_child(segments_polygon)
segments.position = Vector2(300, 0)
parent.add_child(segments)
var layer := CanvasLayer.new()
var layered := Area2D.new()
var layered_shape := CollisionShape2D.new()
layered_shape.shape = RectangleShape2D.new()
(layered_shape.shape as RectangleShape2D).size = Vector2(20, 20)
layered.add_child(layered_shape)
layered.position = Vector2(400, 0)
layer.add_child(layered)
parent.add_child(layer)
await frames(2)
var hits := node.clickable_at(Vector2(50, 50))
expect(hits.size() == 1 and hits[0].collider == area, "点中 Area2D")
for key: String in ["collider", "collider_id", "rid", "shape"]:
	expect(hits[0].has(key), "intersect_point 结果有 " + key)
expect(not hits[0].has("position"), "intersect_point 结果没有 position")
expect(node.clickable_at(Vector2(0, 0)).is_empty(), "空白处为空")
expect(node.clickable_at(Vector2(200, 0)).is_empty(), "ConcavePolygonShape2D 内部点不命中")
expect(node.clickable_at(Vector2(300, 0)).is_empty(), "Segments 模式内部点不命中")
expect(node.clickable_at(Vector2(400, 0)).is_empty(), "CanvasLayer 里的对象默认查不到")
var query := PhysicsPointQueryParameters2D.new()
query.position = Vector2(400, 0)
query.collide_with_areas = true
query.canvas_instance_id = layer.get_instance_id()
expect(node.get_world_2d().direct_space_state.intersect_point(query).size() == 1, "填 canvas_instance_id 后查到")
area.queue_free()
concave.queue_free()
segments.queue_free()
layer.queue_free()
```

## references/camera-parallax.md `func fit_camera_limits`

<!-- check: setup -->
```gdscript
var tiles := TileSet.new()
tiles.tile_size = Vector2i(32, 16)
var source := TileSetAtlasSource.new()
source.texture = make_texture(32, 16)
source.texture_region_size = Vector2i(32, 16)
tiles.add_source(source, 0)
source.create_tile(Vector2i.ZERO)
node.tile_set = tiles
for cell: Vector2i in [Vector2i(-1, -2), Vector2i(3, 4), Vector2i(0, 0)]:
	node.set_cell(cell, 0, Vector2i.ZERO)
```

```gdscript
var cam := Camera2D.new()
node.get_parent().add_child(cam)
node.fit_camera_limits(cam)
expect(cam.limit_left == -32 and cam.limit_top == -32, "左上限制取 used_rect 起点乘格子尺寸")
expect(cam.limit_right == 128 and cam.limit_bottom == 80, "右下限制取 used_rect 终点乘格子尺寸")
expect("limit_enabled" in cam and cam.limit_enabled, "limit_enabled 存在且默认开")
cam.limit_left = 0
cam.limit_right = 3000
cam.limit_top = 0
cam.limit_bottom = 2000
cam.position = Vector2(3900, 500)
await frames(3)
var clamped := cam.get_screen_center_position().x
expect(clamped <= 3000.0, "limit 夹住相机中心")
cam.offset = Vector2(200, 0)
await frames(3)
expect(cam.get_screen_center_position().x > clamped + 150.0, "offset 可以越过 limit")
cam.offset = Vector2.ZERO
cam.position_smoothing_enabled = true
cam.position_smoothing_speed = 6.0
cam.position = Vector2(500, 500)
cam.reset_smoothing()
await frames(3)
cam.position = Vector2(1500, 500)
await frames(1)
expect(cam.get_screen_center_position().x < 1500.0, "不 reset 时相机追赶目标")
expect(not is_equal_approx(cam.get_screen_center_position().x, cam.get_target_position().x), "开平滑时中心与目标不同")
cam.position = Vector2(2500, 500)
cam.reset_smoothing()
await frames(1)
expect(is_equal_approx(cam.get_screen_center_position().x, 2500.0), "同一帧 reset_smoothing 后下一帧到位")
cam.queue_free()
```

## references/camera-parallax.md `func add_trauma`

```gdscript
node.add_trauma(2.0)
await frames(3)
expect(node.offset != Vector2.ZERO, "有 trauma 时 offset 抖动")
expect(absf(node.offset.x) <= node.max_offset and absf(node.offset.y) <= node.max_offset, "偏移不超过 max_offset")
await frames(90)
expect(node.offset == Vector2.ZERO, "trauma 衰减完 offset 归零")
```

## references/drawing.md `func _draw`

```gdscript
var draws: Array[int] = [0]
node.draw.connect(func() -> void: draws[0] += 1)
node.queue_redraw()
await frames(3)
var base := draws[0]
expect(base >= 1, "queue_redraw 后执行 _draw")
await frames(10)
expect(draws[0] == base, "没有 queue_redraw 就不重画")
node.size = Vector2i(10, 10)
await frames(3)
expect(draws[0] == base + 1, "setter 里 queue_redraw 触发一次重画")
```

## references/drawing.md `max_points`

```gdscript
var target := node.get_node("Target") as Node2D
expect(node.top_level, "拖尾 top_level 为 true")
expect(node.global_position == Vector2.ZERO, "节点留在原点")
for i in 40:
	target.position = Vector2(i * 5, 10)
	await frames(1)
expect(node.get_point_count() == node.max_points, "超出长度后保持 max_points")
expect(node.get_point_position(node.get_point_count() - 1) == target.global_position, "最后一个点是目标位置")
```

## references/lighting-glow.md `func _ready`

<!-- run: mode render -->

```gdscript
expect(node.texture is GradientTexture2D and node.shadow_enabled, "_ready 建出渐变贴图并开阴影")
var parent := node.get_parent()
var dark := CanvasModulate.new()
dark.color = Color(0.2, 0.22, 0.35, 1)
parent.add_child(dark)
var wall := Sprite2D.new()
wall.texture = make_texture(400, 200, Color.WHITE)
wall.position = Vector2(300, 100)
parent.add_child(wall)
node.position = Vector2(200, 100)
var dim := PointLight2D.new()
dim.position = Vector2(400, 100)
parent.add_child(dim)
await RenderingServer.frame_post_draw
await RenderingServer.frame_post_draw
var image := node.get_viewport().get_texture().get_image()
var lit := image.get_pixel(200, 100)
var unlit := image.get_pixel(400, 100)
expect(lit.r > 0.8, "有贴图的灯照亮 " + str(lit))
expect(unlit.r < 0.3, "没有 texture 的灯不发光 " + str(unlit))
parent.remove_child(dark)
await RenderingServer.frame_post_draw
await RenderingServer.frame_post_draw
var bright := node.get_viewport().get_texture().get_image().get_pixel(400, 100)
expect(bright.r > 0.95, "没有 CanvasModulate 时精灵本身就是亮的 " + str(bright))
dark.free()
dim.queue_free()
wall.queue_free()
```

## references/navigation-culling.md `screen_exited.connect`

<!-- run: mode render -->

<!-- check: setup -->
```gdscript
var notifier := node.get_node("VisibleOnScreenNotifier2D") as VisibleOnScreenNotifier2D
notifier.rect = Rect2(-8, -8, 16, 16)
node.position = Vector2(20, 20)
```

```gdscript
var notifier := node.get_node("VisibleOnScreenNotifier2D") as VisibleOnScreenNotifier2D
await frames(5)
expect(notifier.is_on_screen(), "在屏幕内")
var enabler := VisibleOnScreenEnabler2D.new()
expect(enabler.enable_mode == VisibleOnScreenEnabler2D.ENABLE_MODE_INHERIT, "enable_mode 默认继承")
expect(enabler.enable_node_path == NodePath(".."), "enable_node_path 默认指向父节点")
enabler.free()
node.position = Vector2(5000, 5000)
await frames(5)
expect(not is_instance_valid(node) or node.is_queued_for_deletion(), "出屏后 queue_free")
node = null
```

## references/navigation-culling.md `func go_to`

```gdscript
var agent := node.get_node("NavigationAgent2D") as NavigationAgent2D
var polygon := NavigationPolygon.new()
polygon.vertices = PackedVector2Array([Vector2(-100, -100), Vector2(500, -100), Vector2(500, 300), Vector2(-100, 300)])
polygon.add_polygon(PackedInt32Array([0, 1, 2, 3]))
var region := NavigationRegion2D.new()
region.navigation_polygon = polygon
node.get_parent().add_child(region)
expect(is_equal_approx(agent.max_speed, 100.0), "max_speed 默认 100")
await frames(5)
node.go_to(Vector2(200, 0))
var deadline := Time.get_ticks_msec() + 10000
while node.position.distance_to(Vector2(200, 0)) > 8.0 and Time.get_ticks_msec() < deadline:
	await frames(1)
await frames(10)
expect(node.position.distance_to(Vector2(200, 0)) < 8.0, "走到目标 " + str(node.position))
expect(agent.is_navigation_finished(), "到达后 is_navigation_finished")
expect(node.velocity.is_zero_approx(), "到达后速度归零")
agent.avoidance_enabled = true
var computed: Array[int] = [0]
agent.velocity_computed.connect(func(_v: Vector2) -> void: computed[0] += 1)
var physics_start := Engine.get_physics_frames()
node.go_to(Vector2(200, 100))
deadline = Time.get_ticks_msec() + 10000
while node.position.distance_to(Vector2(200, 100)) > 8.0 and Time.get_ticks_msec() < deadline:
	await frames(1)
await frames(10)
var elapsed := Engine.get_physics_frames() - physics_start
expect(absi(computed[0] - elapsed) <= 3, "开避障后 velocity_computed 每物理帧发射 %d 次 %d 帧" % [computed[0], elapsed])
expect(node.position.distance_to(Vector2(200, 100)) < 8.0, "避障下也走到目标 " + str(node.position))
expect(node.velocity.is_zero_approx(), "避障下到达后速度归零")
var lone := NavigationAgent2D.new()
lone.avoidance_enabled = true
var safe: Array[Vector2] = [Vector2(-1, -1)]
lone.velocity_computed.connect(func(v: Vector2) -> void: safe[0] = v)
var holder := Node2D.new()
holder.add_child(lone)
node.get_parent().add_child(holder)
lone.velocity = Vector2(50, 0)
await frames(5)
expect(safe[0].is_zero_approx(), "没设过 target_position 时 safe_velocity 为零 " + str(safe[0]))
lone.target_position = Vector2(100, 0)
lone.velocity = Vector2(50, 0)
await frames(5)
expect(not safe[0].is_zero_approx(), "设过 target_position 后 safe_velocity 非零 " + str(safe[0]))
holder.queue_free()
region.queue_free()
```

## references/tilemaplayer.md `func damage_at`

<!-- check: setup -->
```gdscript
var tiles := TileSet.new()
tiles.tile_size = Vector2i(16, 16)
tiles.add_physics_layer()
tiles.add_custom_data_layer()
tiles.set_custom_data_layer_name(0, "damage")
tiles.set_custom_data_layer_type(0, TYPE_INT)
tiles.add_terrain_set()
tiles.set_terrain_set_mode(0, TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES)
tiles.add_terrain(0)
tiles.set_terrain_name(0, 0, "Ground")
var source := TileSetAtlasSource.new()
source.texture = make_texture(48, 48)
source.texture_region_size = Vector2i(16, 16)
tiles.add_source(source, 0)
var table := {
	Vector2i(0, 0): "right bottom|bottom_right",
	Vector2i(1, 0): "left right bottom|bottom_left bottom_right",
	Vector2i(2, 0): "left bottom|bottom_left",
	Vector2i(0, 1): "top right bottom|top_right bottom_right",
	Vector2i(1, 1): "top right bottom left|top_right bottom_right bottom_left top_left",
	Vector2i(2, 1): "top left bottom|top_left bottom_left",
	Vector2i(0, 2): "top right|top_right",
	Vector2i(1, 2): "top left right|top_left top_right",
	Vector2i(2, 2): "top left|top_left",
}
for coords: Vector2i in table:
	source.create_tile(coords)
	var data := source.get_tile_data(coords, 0)
	data.terrain_set = 0
	data.terrain = 0
	data.add_collision_polygon(0)
	data.set_collision_polygon_points(0, 0, PackedVector2Array([Vector2(-8, -8), Vector2(8, -8), Vector2(8, 8), Vector2(-8, 8)]))
	var parts: PackedStringArray = (table[coords] as String).split("|")
	for side: String in parts[0].split(" "):
		data.set_terrain_peering_bit(ClassDB.class_get_integer_constant("TileSet", "CELL_NEIGHBOR_%s_SIDE" % side.to_upper()) as TileSet.CellNeighbor, 0)
	for corner: String in parts[1].split(" "):
		data.set_terrain_peering_bit(ClassDB.class_get_integer_constant("TileSet", "CELL_NEIGHBOR_%s_CORNER" % corner.to_upper()) as TileSet.CellNeighbor, 0)
source.get_tile_data(Vector2i(0, 0), 0).set_custom_data("damage", 5)
node.tile_set = tiles
```

```gdscript
await frames(2)
var cell := Vector2i(2, 3)
expect(node.get_cell_source_id(cell) == -1 and node.get_cell_tile_data(cell) == null, "空格子 source -1 且 tile_data 为 null")
node.paint(cell)
expect(node.get_cell_source_id(cell) == 0 and node.get_cell_atlas_coords(cell) == Vector2i(0, 0), "paint 写入格子")
expect(node.map_to_local(cell) == Vector2(40, 56), "map_to_local 是格子中心")
expect(node.damage_at(Vector2(40, 56)) == 5, "damage_at 读自定义数据")
expect(node.damage_at(Vector2(200, 200)) == 0, "空格子 damage_at 返回 0")
node.position = Vector2(100, 50)
var world := node.cell_center_world(cell)
expect(world == Vector2(140, 106), "cell_center_world 是世界坐标")
expect(node.damage_at(world) == 5, "移动图层后 damage_at 仍然对")
expect(node.local_to_map(world) != cell and node.local_to_map(node.to_local(world)) == cell, "local_to_map 吃局部坐标")
node.clear_cell(cell)
expect(node.get_cell_source_id(cell) == -1, "clear_cell 清掉格子")
node.position = Vector2.ZERO
node.clear()
for x in 3:
	node.paint(Vector2i(x, 0))
node.set_cell(Vector2i(5, 5), 0, Vector2i(1, 0))
expect(node.get_used_cells().size() == 4, "get_used_cells 4 格")
expect(node.get_used_cells_by_id(0, Vector2i(0, 0)).size() == 3, "get_used_cells_by_id 按图集坐标过滤")
expect(node.get_used_rect() == Rect2i(0, 0, 6, 6), "get_used_rect 包围盒")
expect(node.get_surrounding_cells(Vector2i(1, 1)).size() == 4, "方形瓦片 4 个邻格")
expect(node.get_neighbor_cell(Vector2i(1, 1), TileSet.CELL_NEIGHBOR_RIGHT_SIDE) == Vector2i(2, 1), "右邻格")
expect(ClassDB.class_has_method("TileMapLayer", "set_cells_terrain_path"), "有 set_cells_terrain_path")

node.clear()
var mover := CharacterBody2D.new()
var mover_shape := CollisionShape2D.new()
mover_shape.shape = RectangleShape2D.new()
(mover_shape.shape as RectangleShape2D).size = Vector2(4, 4)
mover.add_child(mover_shape)
mover.position = Vector2(88, 60)
node.get_parent().add_child(mover)
await frames(3)
var space := node.get_world_2d().direct_space_state
var probe := PhysicsPointQueryParameters2D.new()
probe.position = Vector2(88, 88)
node.set_cell(Vector2i(5, 5), 0, Vector2i(0, 0))
expect(mover.move_and_collide(Vector2(0, 40), true) == null, "set_cell 后立刻撞不到")
node.update_internals()
expect(space.intersect_point(probe).is_empty(), "update_internals 之后空间查询仍要等一个物理步")
expect(mover.move_and_collide(Vector2(0, 40), true) != null, "update_internals 之后立刻撞得到")
await frames(1)
expect(space.intersect_point(probe).size() == 1, "下一个物理步之后空间查询查得到")
node.collision_enabled = false
node.update_internals()
await frames(1)
expect(space.intersect_point(probe).is_empty(), "collision_enabled 为 false 关碰撞")
node.collision_enabled = true
node.update_internals()
await frames(1)
expect(node.physics_quadrant_size == 16, "physics_quadrant_size 默认 16")

var area := Area2D.new()
var area_shape := CollisionShape2D.new()
area_shape.shape = RectangleShape2D.new()
(area_shape.shape as RectangleShape2D).size = Vector2(4, 4)
area.add_child(area_shape)
area.position = Vector2(88, 88)
area.collision_mask = 1
var entered: Array[Node] = []
area.body_entered.connect(func(body: Node2D) -> void: entered.append(body))
node.get_parent().add_child(area)
await frames(3)
expect(entered.size() == 1 and entered[0] == node, "body_entered 参数是 TileMapLayer")
area.queue_free()

var hit := mover.move_and_collide(Vector2(0, 40))
expect(hit != null and node.get_coords_for_body_rid(hit.get_collider_rid()) == Vector2i(0, 0), "默认返回块坐标")
node.physics_quadrant_size = 1
node.update_internals()
mover.position = Vector2(88, 60)
await frames(2)
hit = mover.move_and_collide(Vector2(0, 40))
expect(hit != null and node.get_coords_for_body_rid(hit.get_collider_rid()) == Vector2i(5, 5), "physics_quadrant_size 为 1 时返回精确格子")
mover.queue_free()

node.clear()
node.tile_map_data = PackedByteArray([0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 253, 255, 0, 0, 1, 0, 0, 0, 0, 0])
expect(node.get_used_cells().size() == 3, "手编 tile_map_data 读出 3 格")
expect(node.get_cell_atlas_coords(Vector2i(0, 2)) == Vector2i(0, 0) and node.get_cell_atlas_coords(Vector2i(1, 2)) == Vector2i(0, 0), "(0, 2) 与 (1, 2) 图集坐标 (0, 0)")
expect(node.get_cell_source_id(Vector2i(-1, -3)) == 0 and node.get_cell_atlas_coords(Vector2i(-1, -3)) == Vector2i(1, 0), "(-1, -3) 图集坐标 (1, 0)")
var fresh := TileMapLayer.new()
fresh.tile_set = node.tile_set
fresh.tile_map_data = PackedByteArray([0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 253, 255, 0, 0, 1, 0, 0, 0, 0, 0])
expect(fresh.tile_map_data.size() == 2 + 12 * 3, "总长 2 加 12 乘格数")
fresh.free()

node.clear()
var level := Node2D.new()
var ground := TileMapLayer.new()
ground.name = "Ground"
ground.tile_set = node.tile_set
ResourceSaver.save(node.tile_set, "res://ground_tiles.tres")
ground.tile_set = load("res://ground_tiles.tres") as TileSet
level.add_child(ground)
ground.owner = level
var seed_scene := PackedScene.new()
seed_scene.pack(level)
ResourceSaver.save(seed_scene, "res://level.tscn")
level.free()
var reload := (load("res://level.tscn") as PackedScene).instantiate()
var reload_ground := reload.get_node("Ground") as TileMapLayer
reload_ground.clear()
for x in range(-2, 10):
	reload_ground.set_cell(Vector2i(x, 5), 0, Vector2i(0, 0))
var repacked := PackedScene.new()
repacked.pack(reload)
ResourceSaver.save(repacked, "res://level.tscn")
reload.free()
var saved := (load("res://level.tscn") as PackedScene).instantiate()
var saved_ground := saved.get_node("Ground") as TileMapLayer
expect(saved_ground.get_used_cells().size() == 12, "存回的场景读回 12 格")
expect(saved_ground.tile_set.resource_path == "res://ground_tiles.tres", "tile_set 仍是外部资源引用")
var text := FileAccess.get_file_as_string("res://level.tscn")
expect(text.contains("format=4") and text.contains("tile_map_data = PackedByteArray(\""), "存回后 format=4 且 tile_map_data 是 base64")
saved.free()
```

## references/tilemaplayer.md `func paint_ground`

```gdscript
var build := func(mode: int, sides: bool, corners: bool, all_bits: bool) -> TileSet:
	var tiles := TileSet.new()
	tiles.tile_size = Vector2i(16, 16)
	tiles.add_terrain_set()
	tiles.set_terrain_set_mode(0, mode as TileSet.TerrainMode)
	tiles.add_terrain(0)
	tiles.set_terrain_name(0, 0, "Ground")
	var source := TileSetAtlasSource.new()
	source.texture = make_texture(48, 48)
	source.texture_region_size = Vector2i(16, 16)
	tiles.add_source(source, 0)
	var table := {
		Vector2i(0, 0): "right bottom|bottom_right",
		Vector2i(1, 0): "left right bottom|bottom_left bottom_right",
		Vector2i(2, 0): "left bottom|bottom_left",
		Vector2i(0, 1): "top right bottom|top_right bottom_right",
		Vector2i(1, 1): "top right bottom left|top_right bottom_right bottom_left top_left",
		Vector2i(2, 1): "top left bottom|top_left bottom_left",
		Vector2i(0, 2): "top right|top_right",
		Vector2i(1, 2): "top left right|top_left top_right",
		Vector2i(2, 2): "top left|top_left",
	}
	for coords: Vector2i in table:
		source.create_tile(coords)
		var data := source.get_tile_data(coords, 0)
		data.terrain_set = 0
		data.terrain = 0
		var parts: PackedStringArray = (table[coords] as String).split("|")
		var side_text: String = "top right bottom left" if all_bits else parts[0]
		var corner_text: String = "top_right bottom_right bottom_left top_left" if all_bits else parts[1]
		if sides:
			for side: String in side_text.split(" "):
				data.set_terrain_peering_bit(ClassDB.class_get_integer_constant("TileSet", "CELL_NEIGHBOR_%s_SIDE" % side.to_upper()) as TileSet.CellNeighbor, 0)
		if corners:
			for corner: String in corner_text.split(" "):
				data.set_terrain_peering_bit(ClassDB.class_get_integer_constant("TileSet", "CELL_NEIGHBOR_%s_CORNER" % corner.to_upper()) as TileSet.CellNeighbor, 0)
	return tiles

var rect: Array[Vector2i] = []
for y in 3:
	for x in 4:
		rect.append(Vector2i(x, y))
var expected := {
	Vector2i(0, 0): Vector2i(0, 0), Vector2i(1, 0): Vector2i(1, 0), Vector2i(3, 0): Vector2i(2, 0),
	Vector2i(0, 1): Vector2i(0, 1), Vector2i(2, 1): Vector2i(1, 1), Vector2i(3, 1): Vector2i(2, 1),
	Vector2i(0, 2): Vector2i(0, 2), Vector2i(2, 2): Vector2i(1, 2), Vector2i(3, 2): Vector2i(2, 2),
}

node.tile_set = build.call(TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES, true, true, false)
node.paint_ground(rect)
for cell: Vector2i in expected:
	expect(node.get_cell_atlas_coords(cell) == expected[cell], "9 宫格 %s 选对瓦片，实际 %s" % [cell, node.get_cell_atlas_coords(cell)])

var pair: Array[Vector2i] = [Vector2i(10, 0), Vector2i(11, 0), Vector2i(10, 1), Vector2i(11, 1)]
node.paint_ground(pair)
expect(node.get_cell_atlas_coords(Vector2i(10, 0)) == Vector2i(0, 0) and node.get_cell_atlas_coords(Vector2i(11, 1)) == Vector2i(2, 2), "2x2 矩形能铺")
var strip: Array[Vector2i] = [Vector2i(20, 0), Vector2i(21, 0), Vector2i(22, 0)]
node.paint_ground(strip)
var empty_count := 0
for cell in strip:
	if node.get_cell_source_id(cell) == -1:
		empty_count += 1
expect(empty_count == 3, "一格厚的浮台整条是空的")

node.clear()
node.tile_set = build.call(TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES, true, false, false)
node.paint_ground(rect)
var side_only_ok := true
for cell: Vector2i in expected:
	side_only_ok = side_only_ok and node.get_cell_atlas_coords(cell) == expected[cell]
expect(side_only_ok, "mode 0 只写 side，矩形地面也能连对")

node.clear()
node.tile_set = build.call(TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES, true, true, true)
node.paint_ground(rect)
var holes := 0
for cell in rect:
	if node.get_cell_source_id(cell) == -1:
		holes += 1
expect(holes > 0, "每块写满 8 个 bit 出现空洞 %d" % holes)

var names := ["RIGHT_SIDE", "BOTTOM_RIGHT_CORNER", "BOTTOM_SIDE", "BOTTOM_LEFT_CORNER", "LEFT_SIDE", "TOP_LEFT_CORNER", "TOP_SIDE", "TOP_RIGHT_CORNER"]
var numbers := [0, 3, 4, 7, 8, 11, 12, 15]
var modes := [
	[true, false, true, false, true, false, true, false],
	[false, true, false, true, false, true, false, true],
	[true, false, true, false, true, false, true, false],
]
var order := [TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES, TileSet.TERRAIN_MODE_MATCH_CORNERS, TileSet.TERRAIN_MODE_MATCH_SIDES]
var all_valid := [true, true, true, true, true, true, true, true]
for i in 3:
	var tiles: TileSet = build.call(order[i], i != 1, i != 2, false)
	var data := (tiles.get_source(0) as TileSetAtlasSource).get_tile_data(Vector2i(1, 1), 0)
	for n in 8:
		var bit := ClassDB.class_get_integer_constant("TileSet", "CELL_NEIGHBOR_" + (names[n] as String)) as TileSet.CellNeighbor
		expect(int(bit) == numbers[n], "常量 %s 为 %d" % [names[n], numbers[n]])
		var want: bool = all_valid[n] if i == 0 else modes[i][n]
		expect(data.is_valid_terrain_peering_bit(bit) == want, "mode %d 的 %s 有效性" % [i, names[n]])
expect(order == [0, 1, 2], "mode 取值 0 角加边 1 只角 2 只边")
```

## references/tilemaplayer.md `func dig`

<!-- check: setup -->
```gdscript
var tiles := TileSet.new()
tiles.tile_size = Vector2i(16, 16)
tiles.add_physics_layer()
tiles.add_custom_data_layer()
tiles.set_custom_data_layer_name(0, "damage")
tiles.set_custom_data_layer_type(0, TYPE_INT)
tiles.add_terrain_set()
tiles.set_terrain_set_mode(0, TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES)
tiles.add_terrain(0)
tiles.set_terrain_name(0, 0, "Ground")
var source := TileSetAtlasSource.new()
source.texture = make_texture(48, 48)
source.texture_region_size = Vector2i(16, 16)
tiles.add_source(source, 0)
var table := {
	Vector2i(0, 0): "right bottom|bottom_right",
	Vector2i(1, 0): "left right bottom|bottom_left bottom_right",
	Vector2i(2, 0): "left bottom|bottom_left",
	Vector2i(0, 1): "top right bottom|top_right bottom_right",
	Vector2i(1, 1): "top right bottom left|top_right bottom_right bottom_left top_left",
	Vector2i(2, 1): "top left bottom|top_left bottom_left",
	Vector2i(0, 2): "top right|top_right",
	Vector2i(1, 2): "top left right|top_left top_right",
	Vector2i(2, 2): "top left|top_left",
}
for coords: Vector2i in table:
	source.create_tile(coords)
	var data := source.get_tile_data(coords, 0)
	data.terrain_set = 0
	data.terrain = 0
	data.add_collision_polygon(0)
	data.set_collision_polygon_points(0, 0, PackedVector2Array([Vector2(-8, -8), Vector2(8, -8), Vector2(8, 8), Vector2(-8, 8)]))
	var parts: PackedStringArray = (table[coords] as String).split("|")
	for side: String in parts[0].split(" "):
		data.set_terrain_peering_bit(ClassDB.class_get_integer_constant("TileSet", "CELL_NEIGHBOR_%s_SIDE" % side.to_upper()) as TileSet.CellNeighbor, 0)
	for corner: String in parts[1].split(" "):
		data.set_terrain_peering_bit(ClassDB.class_get_integer_constant("TileSet", "CELL_NEIGHBOR_%s_CORNER" % corner.to_upper()) as TileSet.CellNeighbor, 0)
source.get_tile_data(Vector2i(0, 0), 0).set_custom_data("damage", 5)
node.tile_set = tiles
```

```gdscript
var parent := node.get_parent()
var other := Snippet.new()
other.tile_set = node.tile_set
parent.add_child(other)
var block: Array[Vector2i] = []
for y in 3:
	for x in 7:
		block.append(Vector2i(x, y))
node.set_cells_terrain_connect(block, 0, 0)
other.set_cells_terrain_connect(block, 0, 0)
expect(node.get_cell_atlas_coords(Vector2i(2, 0)) == Vector2i(1, 0) and node.get_cell_atlas_coords(Vector2i(4, 0)) == Vector2i(1, 0), "挖之前顶行是顶边瓦片")
node.erase_cell(Vector2i(3, 0))
expect(node.get_cell_source_id(Vector2i(3, 0)) == -1, "erase_cell 清掉这一格")
expect(node.get_cell_atlas_coords(Vector2i(2, 0)) == Vector2i(1, 0) and node.get_cell_atlas_coords(Vector2i(4, 0)) == Vector2i(1, 0), "erase_cell 不刷新邻格")
other.dig(Vector2i(3, 0))
expect(other.get_cell_source_id(Vector2i(3, 0)) == -1, "dig 清掉这一格")
expect(other.get_cell_atlas_coords(Vector2i(2, 0)) == Vector2i(2, 0), "dig 后左侧换成右上角")
expect(other.get_cell_atlas_coords(Vector2i(4, 0)) == Vector2i(0, 0), "dig 后右侧换成左上角")
expect(other.get_cell_atlas_coords(Vector2i(3, 1)) == Vector2i(1, 0), "dig 后下方一格换成顶边")
other.queue_free()
```

## references/tilemaplayer.md `func flash`

<!-- run: mode render -->

<!-- check: setup -->
```gdscript
var tiles := TileSet.new()
tiles.tile_size = Vector2i(16, 16)
tiles.add_physics_layer()
tiles.add_custom_data_layer()
tiles.set_custom_data_layer_name(0, "damage")
tiles.set_custom_data_layer_type(0, TYPE_INT)
tiles.add_terrain_set()
tiles.set_terrain_set_mode(0, TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES)
tiles.add_terrain(0)
tiles.set_terrain_name(0, 0, "Ground")
var source := TileSetAtlasSource.new()
source.texture = make_texture(48, 48)
source.texture_region_size = Vector2i(16, 16)
tiles.add_source(source, 0)
var table := {
	Vector2i(0, 0): "right bottom|bottom_right",
	Vector2i(1, 0): "left right bottom|bottom_left bottom_right",
	Vector2i(2, 0): "left bottom|bottom_left",
	Vector2i(0, 1): "top right bottom|top_right bottom_right",
	Vector2i(1, 1): "top right bottom left|top_right bottom_right bottom_left top_left",
	Vector2i(2, 1): "top left bottom|top_left bottom_left",
	Vector2i(0, 2): "top right|top_right",
	Vector2i(1, 2): "top left right|top_left top_right",
	Vector2i(2, 2): "top left|top_left",
}
for coords: Vector2i in table:
	source.create_tile(coords)
	var data := source.get_tile_data(coords, 0)
	data.terrain_set = 0
	data.terrain = 0
	data.add_collision_polygon(0)
	data.set_collision_polygon_points(0, 0, PackedVector2Array([Vector2(-8, -8), Vector2(8, -8), Vector2(8, 8), Vector2(-8, 8)]))
	var parts: PackedStringArray = (table[coords] as String).split("|")
	for side: String in parts[0].split(" "):
		data.set_terrain_peering_bit(ClassDB.class_get_integer_constant("TileSet", "CELL_NEIGHBOR_%s_SIDE" % side.to_upper()) as TileSet.CellNeighbor, 0)
	for corner: String in parts[1].split(" "):
		data.set_terrain_peering_bit(ClassDB.class_get_integer_constant("TileSet", "CELL_NEIGHBOR_%s_CORNER" % corner.to_upper()) as TileSet.CellNeighbor, 0)
source.get_tile_data(Vector2i(0, 0), 0).set_custom_data("damage", 5)
node.tile_set = tiles
```

```gdscript
var cell := Vector2i(1, 1)
var other := Vector2i(2, 1)
node.set_cell(cell, 0, Vector2i(0, 0))
node.set_cell(other, 0, Vector2i(0, 0))
await RenderingServer.frame_post_draw
await RenderingServer.frame_post_draw
var image := node.get_viewport().get_texture().get_image()
expect(image.get_pixel(24, 24).is_equal_approx(Color.WHITE), "没 flash 前是白色")
node.flash(cell)
await RenderingServer.frame_post_draw
await RenderingServer.frame_post_draw
image = node.get_viewport().get_texture().get_image()
var flashed := image.get_pixel(24, 24)
expect(absf(flashed.g - 0.5) < 0.05 and flashed.r > 0.95, "flash 的格子被改色 " + str(flashed))
expect(image.get_pixel(40, 24).is_equal_approx(Color.WHITE), "别的格子不受影响")
```

## references/tilemaplayer.md `SCENE_PATH`

<!-- check: prepare -->
```gdscript
var image := Image.create_empty(16, 16, false, Image.FORMAT_RGBA8)
image.fill(Color.WHITE)
var tiles := TileSet.new()
tiles.tile_size = Vector2i(16, 16)
var source := TileSetAtlasSource.new()
source.texture = ImageTexture.create_from_image(image)
source.texture_region_size = Vector2i(16, 16)
tiles.add_source(source, 0)
source.create_tile(Vector2i(0, 0))
ResourceSaver.save(tiles, "res://ground_tiles.tres")
var level := Node2D.new()
level.name = "Level"
var ground := TileMapLayer.new()
ground.name = "Ground"
ground.tile_set = load("res://ground_tiles.tres") as TileSet
level.add_child(ground)
ground.owner = level
var packed := PackedScene.new()
packed.pack(level)
ResourceSaver.save(packed, "res://level.tscn")
level.free()
```
