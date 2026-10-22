# godot-3d

## SKILL.md `jump_velocity: float = 4.5`

<!-- check: setup -->
```gdscript
var body_shape := CollisionShape3D.new()
body_shape.shape = CapsuleShape3D.new()
node.add_child(body_shape)
node.position = Vector3(0.0, 1.0, 0.0)
var ground := StaticBody3D.new()
var ground_shape := CollisionShape3D.new()
var slab := BoxShape3D.new()
slab.size = Vector3(40.0, 1.0, 40.0)
ground_shape.shape = slab
ground.add_child(ground_shape)
ground.position = Vector3(0.0, -0.5, 0.0)
root.add_child(ground)
```

```gdscript
await frames(10)
expect(node.is_on_floor(), "落地后 is_on_floor 为 true")
Input.action_press("move_right")
await frames(20)
expect(is_equal_approx(node.velocity.x, 5.0), "move_right 时 velocity.x 等于 speed")
expect(node.global_position.x > 1.0, "向右移动")
Input.action_release("move_right")
await frames(2)
expect(is_zero_approx(node.velocity.x), "松开后 velocity.x 归零")
Input.action_press("jump")
await frames(2)
expect(node.velocity.y > 3.0 and not node.is_on_floor(), "按下 jump 后起跳")
Input.action_release("jump")
await frames(90)
expect(node.is_on_floor(), "落回地面")
var fresh := CharacterBody3D.new()
expect(is_equal_approx(fresh.floor_max_angle, 0.7853982), "floor_max_angle 默认 45 度")
expect(is_equal_approx(fresh.floor_snap_length, 0.1), "floor_snap_length 默认 0.1")
expect(fresh.floor_stop_on_slope and not fresh.floor_constant_speed and fresh.floor_block_on_wall, "floor 开关默认值")
expect(is_equal_approx(fresh.wall_min_slide_angle, 0.2617994), "wall_min_slide_angle 默认 15 度")
expect(fresh.max_slides == 6 and is_equal_approx(fresh.safe_margin, 0.001), "max_slides 与 safe_margin 默认值")
expect(fresh.motion_mode == CharacterBody3D.MOTION_MODE_GROUNDED, "motion_mode 默认 GROUNDED")
expect(fresh.platform_on_leave == CharacterBody3D.PLATFORM_ON_LEAVE_ADD_VELOCITY, "platform_on_leave 默认 ADD_VELOCITY")
fresh.free()
```

## SKILL.md `LAYER_WORLD: int = 1 << 0`

```gdscript
expect(node.collision_layer == 2, "玩家在第 2 层")
expect(node.collision_mask == 5, "扫描第 1 层与第 3 层")
expect(node.hit_mask == 4, "hit_mask 默认第 3 层")
expect(node.get_collision_layer_value(2) and not node.get_collision_layer_value(1), "第 n 层按层号读")
node.set_collision_mask_value(2, true)
expect(node.collision_mask == 7, "set_collision_mask_value 按层号开单层")
```

## SKILL.md `func pick`

<!-- check: setup -->
```gdscript
var wall := StaticBody3D.new()
wall.name = "Wall"
wall.collision_layer = 1 << 2
var wall_shape := CollisionShape3D.new()
var wall_box := BoxShape3D.new()
wall_box.size = Vector3(4.0, 4.0, 2.0)
wall_shape.shape = wall_box
wall.add_child(wall_shape)
wall.position = Vector3(0.0, 0.0, -5.0)
root.add_child(wall)
var sensor := Area3D.new()
sensor.name = "Sensor"
sensor.collision_layer = 1 << 2
var sensor_shape := CollisionShape3D.new()
var sensor_box := BoxShape3D.new()
sensor_box.size = Vector3(1.0, 1.0, 1.0)
sensor_shape.shape = sensor_box
sensor.add_child(sensor_shape)
sensor.position = Vector3(0.0, 0.0, -2.0)
root.add_child(sensor)
```

```gdscript
await frames(3)
var middle := Vector2(root.size) * 0.5
var sensor := root.get_node("Sensor") as Area3D
var wall := root.get_node("Wall") as StaticBody3D
var hit: Dictionary = node.pick(middle)
expect(hit.get("collider") == sensor, "collide_with_areas 打开后先打到近处的 Area3D")
expect(hit.has("position") and hit.has("normal") and hit.has("rid") and hit.has("shape"), "结果带 position normal collider rid shape")
sensor.collision_layer = 0
await frames(2)
hit = node.pick(middle)
expect(hit.get("collider") == wall, "Area3D 不在掩码里时打到墙")
expect(is_equal_approx((hit["position"] as Vector3).z, -4.0), "命中墙正面")
var space := root.get_world_3d().direct_space_state
var plain := PhysicsRayQueryParameters3D.create(Vector3.ZERO, Vector3(0.0, 0.0, -10.0), 1 << 2)
sensor.collision_layer = 1 << 2
await frames(2)
expect(space.intersect_ray(plain).get("collider") == wall, "默认不打 Area3D")
var from_inside := PhysicsRayQueryParameters3D.create(Vector3(0.0, 0.0, -5.0), Vector3(0.0, 0.0, 5.0), 1 << 2)
expect(space.intersect_ray(from_inside).is_empty(), "从碰撞体内部出发默认不命中该体")
from_inside.hit_from_inside = true
expect(space.intersect_ray(from_inside).get("collider") == wall, "hit_from_inside 后命中")
wall.collision_layer = 1 << 1
await frames(2)
expect(node.pick(middle).get("collider") == sensor, "墙移出掩码后只剩 Area3D 可命中")
sensor.collision_layer = 0
await frames(2)
expect(node.pick(middle).is_empty(), "掩码外没命中时字典为空")
```

## SKILL.md `mouse_sensitivity: float = 0.003`

<!-- run: mode render -->

```gdscript
await frames(2)
var arm := node.get_node("SpringArm3D") as SpringArm3D
expect(is_equal_approx(arm.spring_length, 1.0) and arm.collision_mask == 1, "spring_length 默认 1 collision_mask 默认只有第 1 层")
Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
var motion := InputEventMouseMotion.new()
motion.screen_relative = Vector2(100.0, -50.0)
root.push_input(motion)
expect(is_equal_approx(node.rotation.y, -0.3), "水平移动转枢轴 yaw")
expect(is_equal_approx(arm.rotation.x, 0.15), "垂直移动转弹簧臂 pitch")
motion = InputEventMouseMotion.new()
motion.screen_relative = Vector2(0.0, 10000.0)
root.push_input(motion)
expect(is_equal_approx(arm.rotation.x, -1.2), "pitch 夹在 -1.2")
Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
motion = InputEventMouseMotion.new()
motion.screen_relative = Vector2(100.0, 0.0)
root.push_input(motion)
expect(is_equal_approx(node.rotation.y, -0.3), "鼠标没捕获时不转")
var player := CharacterBody3D.new()
var player_shape := CollisionShape3D.new()
var capsule := CapsuleShape3D.new()
player_shape.shape = capsule
player.add_child(player_shape)
root.add_child(player)
var pivot := Node3D.new()
pivot.set_script(load("res://s3.gd"))
pivot.position = Vector3(0.0, capsule.height * 0.5 + 0.5, 0.0)
var tilted := SpringArm3D.new()
tilted.name = "SpringArm3D"
tilted.add_child(Camera3D.new())
tilted.rotation.x = 1.2
tilted.spring_length = 3.0
pivot.add_child(tilted)
player.add_child(pivot)
await frames(4)
expect(is_equal_approx(tilted.get_hit_length(), 3.0), "_ready 排除了父级玩家 弹簧臂伸到全长")
tilted.remove_excluded_object(player.get_rid())
await frames(4)
expect(tilted.get_hit_length() < 1.0, "没排除时扫进玩家碰撞体而缩短")
player.free()
```

## SKILL.md `func go_to`

<!-- check: setup -->
```gdscript
var nav_mesh := NavigationMesh.new()
nav_mesh.vertices = PackedVector3Array([Vector3(-6, 0, -6), Vector3(-6, 0, 6), Vector3(6, 0, 6), Vector3(6, 0, -6)])
nav_mesh.add_polygon(PackedInt32Array([0, 1, 2, 3]))
var region := NavigationRegion3D.new()
region.navigation_mesh = nav_mesh
root.add_child(region)
NavigationServer3D.map_force_update(region.get_navigation_map())
node.position = Vector3(-4.0, 0.0, -4.0)
```

```gdscript
var target := Vector3(4.0, 0.0, 4.0)
var start := node.global_position.distance_to(target)
node.go_to(target)
await frames(120)
expect(node.global_position.distance_to(target) < start - 3.0, "沿导航路径朝目标移动")
var agent := node.get_node("NavigationAgent3D") as NavigationAgent3D
expect(not agent.is_navigation_finished() and agent.target_position == target, "未到达时 is_navigation_finished 为 false")
node.global_position = target
await frames(10)
expect(agent.is_navigation_finished(), "到达目标后 is_navigation_finished 为 true")
expect(is_equal_approx(NavigationMesh.new().cell_size, float(ProjectSettings.get_setting("navigation/3d/default_cell_size"))), "NavigationMesh.cell_size 与项目默认一致")
```

## references/culling-and-instancing.md `visibility_range_end = 10.0`

<!-- run: mode render -->

<!-- check: setup -->
```gdscript
var red := StandardMaterial3D.new()
red.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
red.albedo_color = Color.RED
var blue := StandardMaterial3D.new()
blue.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
blue.albedo_color = Color.BLUE
var near_mesh := node.get_node("Near") as MeshInstance3D
near_mesh.mesh = BoxMesh.new()
near_mesh.material_override = red
near_mesh.position.x = -1.0
var far_mesh := node.get_node("Far") as MeshInstance3D
far_mesh.mesh = BoxMesh.new()
far_mesh.material_override = blue
far_mesh.position.x = 1.0
```

```gdscript
var make_vp := func(q_w: int, q_h: int) -> SubViewport:
	var q_view := SubViewport.new()
	q_view.size = Vector2i(q_w, q_h)
	q_view.own_world_3d = true
	q_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var q_env := Environment.new()
	q_env.background_mode = Environment.BG_COLOR
	q_env.background_color = Color.BLACK
	var q_world := WorldEnvironment.new()
	q_world.environment = q_env
	q_view.add_child(q_world)
	root.add_child(q_view)
	return q_view
var new_stage := func(q_view: SubViewport) -> Node3D:
	var q_old := q_view.get_node_or_null("Stage")
	if q_old != null:
		q_view.remove_child(q_old)
		q_old.free()
	var q_stage := Node3D.new()
	q_stage.name = "Stage"
	q_view.add_child(q_stage)
	return q_stage
var snap := func(q_view: SubViewport) -> Image:
	await frames(1)
	await RenderingServer.frame_post_draw
	return q_view.get_texture().get_image()
var cls := func(q_c: Color) -> int:
	if q_c.r > 0.5 and q_c.b < 0.5:
		return 1
	if q_c.b > 0.5 and q_c.r < 0.5:
		return 2
	return 0
var near_mesh := node.get_node("Near") as MeshInstance3D
var far_mesh := node.get_node("Far") as MeshInstance3D
expect(is_equal_approx(near_mesh.visibility_range_end, 10.0) and is_equal_approx(far_mesh.visibility_range_begin, 10.0), "范围已设置")
expect(near_mesh.visibility_range_fade_mode == GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED, "fade_mode 默认 Disabled")
var fresh := MeshInstance3D.new()
expect(is_zero_approx(fresh.visibility_range_begin) and is_zero_approx(fresh.visibility_range_end), "begin 与 end 默认 0")
fresh.free()
var vp := make_vp.call(160, 90) as SubViewport
var rig := new_stage.call(vp) as Node3D
var eye := Camera3D.new()
eye.position = Vector3(0.0, 0.0, 5.0)
rig.add_child(eye)
root.remove_child(node)
rig.add_child(node)
var shot := await snap.call(vp) as Image
var count := func(pic: Image, which: int) -> int:
	var n := 0
	for y in pic.get_height():
		for x in pic.get_width():
			if cls.call(pic.get_pixel(x, y)) == which:
				n += 1
	return n
expect(count.call(shot, 1) > 100 and count.call(shot, 2) == 0, "相机在 5 米处只看到近处的红色网格")
eye.position.z = 15.0
shot = await snap.call(vp) as Image
expect(count.call(shot, 1) == 0 and count.call(shot, 2) > 8, "相机在 15 米处只看到远处的蓝色网格")
vp.free()
```

## references/culling-and-instancing.md `func build`

```gdscript
var mesh := BoxMesh.new()
node.build(mesh, 100, 10.0)
var mm := node.multimesh
expect(mm.instance_count == 100, "实例数")
expect(mm.transform_format == MultiMesh.TRANSFORM_3D and mm.use_custom_data and not mm.use_colors, "格式与自定义数据")
expect(mm.visible_instance_count == -1, "visible_instance_count 默认 -1")
expect(mm.get_instance_custom_data(5).r >= 0.0 and mm.get_instance_custom_data(5).r <= 1.0, "自定义数据写入")
expect(absf(mm.get_instance_transform(7).origin.x) <= 10.0, "实例位置在范围内")
expect(mm.custom_aabb.size.is_equal_approx(Vector3(20.0, 10.0, 20.0)), "custom_aabb")
```

## references/culling-and-instancing.md `func spawn`

<!-- run: mode render -->

```gdscript
var make_vp := func(q_w: int, q_h: int) -> SubViewport:
	var q_view := SubViewport.new()
	q_view.size = Vector2i(q_w, q_h)
	q_view.own_world_3d = true
	q_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var q_env := Environment.new()
	q_env.background_mode = Environment.BG_COLOR
	q_env.background_color = Color.BLACK
	var q_world := WorldEnvironment.new()
	q_world.environment = q_env
	q_view.add_child(q_world)
	root.add_child(q_view)
	return q_view
var new_stage := func(q_view: SubViewport) -> Node3D:
	var q_old := q_view.get_node_or_null("Stage")
	if q_old != null:
		q_view.remove_child(q_old)
		q_old.free()
	var q_stage := Node3D.new()
	q_stage.name = "Stage"
	q_view.add_child(q_stage)
	return q_stage
var snap := func(q_view: SubViewport) -> Image:
	await frames(1)
	await RenderingServer.frame_post_draw
	return q_view.get_texture().get_image()
var cls := func(q_c: Color) -> int:
	if q_c.r > 0.5 and q_c.b < 0.5:
		return 1
	if q_c.b > 0.5 and q_c.r < 0.5:
		return 2
	return 0
var vp := make_vp.call(320, 180) as SubViewport
var rig := new_stage.call(vp) as Node3D
var top_down := Camera3D.new()
top_down.projection = Camera3D.PROJECTION_ORTHOGONAL
top_down.size = 4.0
top_down.position = Vector3(0.0, 5.0, 0.0)
top_down.rotation_degrees.x = -90.0
rig.add_child(top_down)
var floor_mesh := MeshInstance3D.new()
var floor_plane := PlaneMesh.new()
floor_plane.size = Vector2(10.0, 10.0)
floor_mesh.mesh = floor_plane
var floor_paint := StandardMaterial3D.new()
floor_paint.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
floor_mesh.material_override = floor_paint
rig.add_child(floor_mesh)
root.remove_child(node)
rig.add_child(node)
node.spawn(make_texture(8, 8, Color.RED), Vector3.ZERO, Vector3.UP)
var decal := node.get_child(node.get_child_count() - 1) as Decal
expect(decal != null and decal.size == Vector3(0.6, 0.4, 0.6), "贴花尺寸 Y 轴是投影深度")
expect(decal.global_basis.y.is_equal_approx(Vector3.UP), "贴花的 Y 轴对准法线")
var shot := await snap.call(vp) as Image
var red := 0
for x in shot.get_width():
	if cls.call(shot.get_pixel(x, 90)) == 1:
		red += 1
expect(red > 10, "Forward+ 上贴花投到地面")
Engine.time_scale = 30.0
for i in 30:
	await process_frame
Engine.time_scale = 1.0
expect(not is_instance_valid(decal), "淡出后贴花释放")
vp.free()
```

## references/import-and-levels.md `_post_import`

```gdscript
var scene := Node3D.new()
var wall := StaticBody3D.new()
scene.add_child(wall)
wall.owner = scene
var door := StaticBody3D.new()
wall.add_child(door)
door.owner = scene
var result := node._post_import(scene)
expect(result == scene, "必须返回场景")
expect(wall.collision_layer == 2 and door.collision_layer == 2, "所有 StaticBody3D 改到第 2 层")
scene.free()
```

## references/import-and-levels.md `func load_model`

<!-- check: prepare -->
```gdscript
var model_root := Node3D.new()
model_root.name = "Model"
var box_node := MeshInstance3D.new()
box_node.name = "Box"
box_node.mesh = BoxMesh.new()
model_root.add_child(box_node)
box_node.owner = model_root
var document := GLTFDocument.new()
var state := GLTFState.new()
document.append_from_scene(model_root, state)
document.write_to_filesystem(state, "res://model.glb")
model_root.free()
```

```gdscript
var model := node.load_model("res://model.glb")
expect(model != null, "glb 加载出节点")
expect(model.find_child("Box", true, false) is MeshInstance3D, "带回网格节点")
node.add_child(model)
expect(node.get_child_count() == 1, "add_child 加入场景")
```

## references/import-and-levels.md `func place`

<!-- check: setup -->
```gdscript
var library := MeshLibrary.new()
library.create_item(0)
library.set_item_mesh(0, BoxMesh.new())
node.mesh_library = library
```

```gdscript
expect(node.cell_size == Vector3(2.0, 2.0, 2.0), "cell_size 默认 2")
expect(node.cell_octant_size == 8 and not node.bake_navigation, "cell_octant_size 默认 8 bake_navigation 默认关")
expect(node.get_cell_item(Vector3i(1, 0, 2)) == GridMap.INVALID_CELL_ITEM, "空格返回 INVALID_CELL_ITEM")
node.place(Vector3(3.0, 0.5, 5.0), 0)
expect(node.get_cell_item(Vector3i(1, 0, 2)) == 0, "世界坐标落到对应格子")
```

## references/physics-3d.md `func bodies_in_radius`

<!-- check: setup -->
```gdscript
var spots := {"Near": Vector3(1.0, 0.0, 0.0), "Above": Vector3(0.0, 1.0, 0.0), "Far": Vector3(10.0, 0.0, 0.0)}
for label: String in spots:
	var body := StaticBody3D.new()
	body.name = label
	body.collision_layer = 2 if label == "Above" else 1
	var body_shape := CollisionShape3D.new()
	var ball := SphereShape3D.new()
	ball.radius = 0.5
	body_shape.shape = ball
	body.add_child(body_shape)
	body.position = spots[label]
	root.add_child(body)
```

```gdscript
await frames(3)
var found := node.bodies_in_radius(Vector3.ZERO, 3.0, 1)
expect(found.size() == 1 and found[0].name == &"Near", "掩码第 1 层只找到 Near")
found = node.bodies_in_radius(Vector3.ZERO, 3.0, 3)
expect(found.size() == 2, "掩码第 1 与 2 层找到两个")
found = node.bodies_in_radius(Vector3.ZERO, 20.0, 3)
expect(found.size() == 3, "半径放大后找到 Far")
```

## references/physics-3d.md `func has_ground_ahead`

<!-- check: setup -->
```gdscript
var probe := node.get_node("GroundProbe") as ShapeCast3D
expect(probe.collision_mask == 1 and probe.max_results == 32, "ShapeCast3D 默认只有第 1 层 max_results 32")
probe.shape = SphereShape3D.new()
probe.target_position = Vector3(0.0, -2.0, 0.0)
var ground := StaticBody3D.new()
ground.name = "Ground"
var ground_shape := CollisionShape3D.new()
var slab := BoxShape3D.new()
slab.size = Vector3(10.0, 1.0, 10.0)
ground_shape.shape = slab
ground.add_child(ground_shape)
ground.position = Vector3(0.0, -1.5, 0.0)
root.add_child(ground)
```

```gdscript
await frames(3)
expect(node.has_ground_ahead(), "前方有地面")
var ground := root.get_node("Ground") as StaticBody3D
root.remove_child(ground)
await frames(3)
expect(not node.has_ground_ahead(), "地面移走后没有")
ground.free()
```

## references/skeleton-modifiers.md `func look_with_head`

<!-- check: setup -->
```gdscript
node.add_bone("Head")
```

```gdscript
var target := Node3D.new()
target.position = Vector3(0.0, 0.0, 5.0)
root.add_child(target)
node.look_with_head(target)
var look := node.get_child(node.get_child_count() - 1) as LookAtModifier3D
expect(look.bone_name == "Head" and look.target_node == look.get_path_to(target), "骨骼与目标")
expect(look.forward_axis == SkeletonModifier3D.BONE_AXIS_PLUS_Z and look.use_angle_limitation, "forward_axis 默认 +Z 且启用角度限制")
expect(is_equal_approx(look.primary_limit_angle, deg_to_rad(70.0)) and is_equal_approx(look.duration, 0.2), "限制角度与时长")
await frames(5)
expect(look.is_target_within_limitation(), "目标在正前方时在限制内")
target.position = Vector3(0.0, 0.0, -5.0)
await frames(5)
expect(not look.is_target_within_limitation(), "目标在背后时超出限制")
var fresh := LookAtModifier3D.new()
expect(is_zero_approx(fresh.duration), "duration 默认 0")
fresh.free()
```

## references/skeleton-modifiers.md `func setup_leg_ik`

<!-- check: setup -->
```gdscript
node.add_bone("UpperLeg_L")
node.add_bone("LowerLeg_L")
node.add_bone("Foot_L")
node.set_bone_parent(1, 0)
node.set_bone_parent(2, 1)
node.set_bone_rest(1, Transform3D(Basis.IDENTITY, Vector3(0.0, -1.0, 0.0)))
node.set_bone_rest(2, Transform3D(Basis.IDENTITY, Vector3(0.0, -1.0, 0.0)))
node.reset_bone_poses()
```

```gdscript
var foot := Node3D.new()
foot.position = Vector3(0.5, -1.5, 0.0)
root.add_child(foot)
var knee := Node3D.new()
knee.position = Vector3(0.0, -1.0, 1.0)
root.add_child(knee)
var ik := node.setup_leg_ik(foot, knee)
expect(ik.setting_count == 1, "一条链")
expect(ik.get_root_bone_name(0) == "UpperLeg_L" and ik.get_middle_bone_name(0) == "LowerLeg_L" and ik.get_end_bone_name(0) == "Foot_L", "三根骨骼")
expect(ik.get_target_node(0) == ik.get_path_to(foot) and ik.get_pole_node(0) == ik.get_path_to(knee), "目标与极向量")
var solved: Array[Vector3] = []
node.skeleton_updated.connect(func() -> void: solved.append(node.get_bone_global_pose(2).origin))
await frames(5)
expect(not solved.is_empty() and solved.back().distance_to(foot.global_position) < 0.05, "skeleton_updated 里脚骨到达目标")
expect(node.get_bone_global_pose(2).origin.is_equal_approx(Vector3(0.0, -2.0, 0.0)), "更新之外读到的是未修改的静止姿势")
ik.influence = 0.0
solved.clear()
await frames(5)
expect(solved.back().is_equal_approx(Vector3(0.0, -2.0, 0.0)), "influence 为 0 时修改器不起作用")
```
