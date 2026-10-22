# godot-2d-in-3d

## SKILL.md `offset.y = used.end.y`

<!-- run: mode render -->

<!-- check: setup -->
```gdscript
var image := Image.create_empty(16, 16, false, Image.FORMAT_RGBA8)
image.fill_rect(Rect2i(0, 0, 16, 15), Color.RED)
node.texture = ImageTexture.create_from_image(image)
```

```gdscript
var snap := func() -> Image:
	await frames(3)
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()
var red_box := func(q_image: Image) -> Rect2i:
	var q_min := Vector2i(1 << 20, 1 << 20)
	var q_max := Vector2i(-1, -1)
	for y in q_image.get_height():
		for x in q_image.get_width():
			var c := q_image.get_pixel(x, y)
			if c.r - c.g > 0.15:
				q_min = Vector2i(mini(q_min.x, x), mini(q_min.y, y))
				q_max = Vector2i(maxi(q_max.x, x), maxi(q_max.y, y))
	return Rect2i(q_min, q_max - q_min + Vector2i.ONE)
expect(is_equal_approx(node.pixel_size, 1.0 / 32.0), "pixel_size 每米 32 像素")
expect(node.billboard == BaseMaterial3D.BILLBOARD_FIXED_Y and node.shaded, "billboard 与 shaded")
expect(node.texture_filter == BaseMaterial3D.TEXTURE_FILTER_NEAREST and node.alpha_cut == SpriteBase3D.ALPHA_CUT_DISCARD, "过滤与 alpha_cut")
expect(is_equal_approx(node.offset.y, 7.0), "最后一行透明的 16x16 贴图 offset.y 是 7")
var fresh := Sprite3D.new()
expect(is_equal_approx(fresh.pixel_size, 0.01) and not fresh.shaded and fresh.double_sided, "pixel_size 默认 0.01 shaded 默认 false double_sided 默认 true")
expect(fresh.texture_filter == BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS, "texture_filter 默认线性加 mipmap")
fresh.free()
var cam := Camera3D.new()
cam.projection = Camera3D.PROJECTION_ORTHOGONAL
cam.size = float(root.size.y) / 32.0
cam.position = Vector3(0.0, 0.0, 5.0)
root.add_child(cam)
var box := red_box.call(await snap.call()) as Rect2i
expect(box.size == Vector2i(16, 15), "每贴图像素一个屏幕像素 不透明部分 16x15")
expect(box.end.y == root.size.y >> 1, "不透明脚底落在原点所在的屏幕行")
node.offset.y = 0.0
box = red_box.call(await snap.call()) as Rect2i
expect(box.end.y == (root.size.y >> 1) + 7, "offset.y 为 0 时脚底悬在原点下方 7 像素")
cam.free()
```

## SKILL.md `func face`

<!-- run: mode render -->

<!-- check: setup -->
```gdscript
var image := Image.create_empty(16, 16, false, Image.FORMAT_RGBA8)
image.fill(Color.RED)
image.fill_rect(Rect2i(8, 0, 8, 16), Color.BLUE)
var sheet := SpriteFrames.new()
sheet.add_frame(&"default", ImageTexture.create_from_image(image))
node.sprite_frames = sheet
node.pixel_size = 0.02
node.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
```

```gdscript
var snap := func() -> Image:
	await frames(3)
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()
var red_is_left := func(q_image: Image) -> bool:
	var q_red := 0.0
	var q_blue := 0.0
	var q_red_n := 0
	var q_blue_n := 0
	for y in q_image.get_height():
		for x in q_image.get_width():
			var c := q_image.get_pixel(x, y)
			if c.r > 0.5 and c.b < 0.3:
				q_red += x
				q_red_n += 1
			elif c.b > 0.5 and c.r < 0.3:
				q_blue += x
				q_blue_n += 1
	return q_red_n > 0 and q_blue_n > 0 and q_red / q_red_n < q_blue / q_blue_n
var cam := Camera3D.new()
cam.projection = Camera3D.PROJECTION_ORTHOGONAL
cam.size = float(root.size.y) * 0.02
cam.position = Vector3(0.0, 0.0, 5.0)
root.add_child(cam)
expect(red_is_left.call(await snap.call()), "未翻转时红在左")
node.face(-1.0)
expect(node.flip_h, "向左 flip_h 为 true")
expect(not red_is_left.call(await snap.call()), "billboard 下 flip_h 翻转")
node.face(0.0)
expect(node.flip_h, "方向为 0 时保持上次朝向")
node.face(1.0)
expect(not node.flip_h and red_is_left.call(await snap.call()), "向右还原")
node.scale.x = -1.0
expect(red_is_left.call(await snap.call()), "billboard 下 scale.x 为 -1 不翻转")
node.scale.x = 1.0
node.billboard = BaseMaterial3D.BILLBOARD_DISABLED
node.scale.x = -1.0
expect(not red_is_left.call(await snap.call()), "非 billboard 下负缩放翻转")
node.scale.x = 1.0
node.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
node.scale.x = -1.0
node.double_sided = false
await frames(3)
await RenderingServer.frame_post_draw
var gone := root.get_texture().get_image()
var red_seen := 0
for y in gone.get_height():
	for x in gone.get_width():
		if gone.get_pixel(x, y).r - gone.get_pixel(x, y).g > 0.15:
			red_seen += 1
expect(red_seen == 0, "billboard 加负缩放加单面 精灵被背面剔除")
cam.free()
```

## SKILL.md `size = 360.0`

<!-- run: mode render -->

```gdscript
var snap := func() -> Image:
	await frames(3)
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()
var red_width := func(q_image: Image) -> int:
	var q_row := q_image.get_height() >> 1
	var q_n := 0
	for x in q_image.get_width():
		var c := q_image.get_pixel(x, q_row)
		if c.r > 0.5 and c.g < 0.3:
			q_n += 1
	return q_n
expect(node.projection == Camera3D.PROJECTION_ORTHOGONAL and is_equal_approx(node.size, 11.25), "正交 size 为 360 乘 pixel_size")
expect(node.keep_aspect == Camera3D.KEEP_HEIGHT, "keep_aspect 默认 KEEP_HEIGHT")
var image := Image.create_empty(16, 16, false, Image.FORMAT_RGBA8)
image.fill(Color.RED)
var sprite := Sprite3D.new()
sprite.texture = ImageTexture.create_from_image(image)
sprite.pixel_size = 0.02
sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
root.add_child(sprite)
node.position = Vector3(0.0, 0.0, 5.0)
node.size = float(root.size.y) * 0.02
expect(red_width.call(await snap.call()) == 16, "size 等于视口高度乘 pixel_size 时 16 像素宽的精灵占 16 像素")
node.size = float(root.size.y) * 0.02 / 2.0
expect(red_width.call(await snap.call()) == 32, "size 减半放大 2 倍")
var eye := Camera3D.new()
eye.fov = 40.0
var distance := float(root.size.y) * 0.02 / (2.0 * tan(deg_to_rad(eye.fov) / 2.0))
eye.position = Vector3(0.0, 0.0, distance)
root.add_child(eye)
eye.make_current()
var measured := red_width.call(await snap.call()) as int
expect(absi(measured - 16) <= 1, "透视下按公式算出的距离上一贴图像素对应一屏幕像素")
sprite.free()
eye.free()
```

## SKILL.md `gradient.set_color(0`

<!-- run: mode render -->

```gdscript
var snap := func() -> Image:
	await frames(3)
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()
expect(node.axis == Vector3.AXIS_Y and is_equal_approx(node.position.y, 0.01), "平放朝上并抬高 0.01")
expect(node.texture is GradientTexture2D and node.texture.get_width() == 64, "径向渐变贴图")
var ground := MeshInstance3D.new()
var plane := PlaneMesh.new()
plane.size = Vector2(30.0, 30.0)
ground.mesh = plane
root.add_child(ground)
var cam := Camera3D.new()
cam.projection = Camera3D.PROJECTION_ORTHOGONAL
cam.size = 8.0
cam.position = Vector3(0.0, 5.0, 0.0)
cam.rotation_degrees = Vector3(-90.0, 0.0, 0.0)
root.add_child(cam)
var lit := await snap.call() as Image
var middle := lit.get_pixel(lit.get_width() >> 1, lit.get_height() >> 1)
var edge := lit.get_pixel(4, 4)
expect(middle.r < edge.r - 0.1, "blob 中心比地面暗")
node.visible = false
var bare := await snap.call() as Image
expect(is_equal_approx(bare.get_pixel(bare.get_width() >> 1, bare.get_height() >> 1).r, edge.r), "去掉 blob 后中心与地面一致")
cam.free()
ground.free()
```

## references/subviewport-ui.md `_viewport.disable_3d = true`

<!-- run: mode render -->

```gdscript
var snap := func() -> Image:
	await frames(3)
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()
var box_of := func(q_image: Image, q_blue: bool) -> Rect2i:
	var q_min := Vector2i(1 << 20, 1 << 20)
	var q_max := Vector2i(-1, -1)
	for y in q_image.get_height():
		for x in q_image.get_width():
			var c := q_image.get_pixel(x, y)
			var q_hit := c.b > 0.5 and c.r < 0.3 if q_blue else c.r > 0.5 and c.b < 0.3
			if q_hit:
				q_min = Vector2i(mini(q_min.x, x), mini(q_min.y, y))
				q_max = Vector2i(maxi(q_max.x, x), maxi(q_max.y, y))
	return Rect2i(q_min, q_max - q_min + Vector2i.ONE)
var view := node.get_node("SubViewport") as SubViewport
var sprite := node.get_node("Sprite3D") as Sprite3D
expect(view.size == Vector2i(128, 128) and view.disable_3d and view.transparent_bg, "尺寸 关 3D 透明背景")
expect(view.canvas_item_default_texture_filter == Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST, "SubViewport 手动设 Nearest")
expect(sprite.texture == view.get_texture(), "Sprite3D 用 ViewportTexture")
var top := ColorRect.new()
top.color = Color.RED
top.size = Vector2(128.0, 16.0)
view.add_child(top)
var bottom := ColorRect.new()
bottom.color = Color.BLUE
bottom.position = Vector2(0.0, 112.0)
bottom.size = Vector2(128.0, 16.0)
view.add_child(bottom)
sprite.offset.y = 64.0
var cam := Camera3D.new()
cam.projection = Camera3D.PROJECTION_ORTHOGONAL
cam.size = float(root.size.y) / 32.0
cam.position = Vector3(0.0, 0.0, 5.0)
root.add_child(cam)
var shot := await snap.call() as Image
var red := box_of.call(shot, false) as Rect2i
var blue := box_of.call(shot, true) as Rect2i
expect(red.size.x == 128 and red.size.y == 16 and blue.size.y == 16, "2D 内容原样贴出")
expect(red.position.y < blue.position.y, "上下方向与 2D 一致")
expect(blue.end.y == root.size.y >> 1, "offset.y 取视口高度一半 视口底边落在原点")
cam.free()
```

## references/subviewport-ui.md `text = "Lv 12"`

```gdscript
var fresh := Label3D.new()
expect(not fresh.shaded and fresh.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, "shaded 默认 false cast_shadow 默认关")
expect(is_equal_approx(fresh.pixel_size, 0.005) and fresh.font_size == 32 and fresh.outline_size == 12, "pixel_size font_size outline_size 默认值")
expect(fresh.alpha_cut == Label3D.ALPHA_CUT_DISABLED, "alpha_cut 默认 DISABLED")
expect(not fresh.fixed_size, "fixed_size 默认 false")
fresh.free()
expect(node.text == "Lv 12" and node.outline_size == 8 and is_equal_approx(node.pixel_size, 0.01), "脚本里的设置")
expect(node.billboard == BaseMaterial3D.BILLBOARD_FIXED_Y and node.alpha_cut == Label3D.ALPHA_CUT_DISCARD, "billboard 与 alpha_cut")
```

## references/subviewport-ui.md `unproject_position`

<!-- check: setup -->
```gdscript
var camera := Camera3D.new()
camera.position = Vector3(0.0, 0.0, 5.0)
root.add_child(camera)
node.size = Vector2(20.0, 10.0)
```

```gdscript
await frames(3)
var target := node.target
target.position = Vector3(1.0, 0.5, 0.0)
await frames(3)
var camera := root.get_camera_3d()
expect(node.visible, "目标在相机前时可见")
expect(node.position.is_equal_approx(camera.unproject_position(target.global_position) - node.size * 0.5), "控件中心对准投影点")
target.position = Vector3(0.0, 0.0, 10.0)
await frames(3)
expect(not node.visible, "目标在相机后方时隐藏")
```

## references/hd2d-environment.md `CameraAttributesPractical.new()`

<!-- run: mode render -->

```gdscript
var snap := func() -> Image:
	await frames(3)
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()
var distance := func(q_a: Image, q_b: Image) -> float:
	var q_sum := 0.0
	for y in q_a.get_height():
		for x in q_a.get_width():
			var c1 := q_a.get_pixel(x, y)
			var c2 := q_b.get_pixel(x, y)
			q_sum += absf(c1.r - c2.r) + absf(c1.g - c2.g) + absf(c1.b - c2.b)
	return q_sum / (q_a.get_width() * q_a.get_height())
var env := node.environment
expect(env.glow_enabled and env.ssao_enabled and env.fog_enabled and env.adjustment_enabled, "效果开关都打开")
expect(env.background_mode == Environment.BG_COLOR and env.ambient_light_source == Environment.AMBIENT_SOURCE_COLOR, "背景与环境光取颜色")
expect(node.camera_attributes is CameraAttributesPractical, "相机属性是 CameraAttributesPractical")
var attributes := node.camera_attributes as CameraAttributesPractical
expect(attributes.dof_blur_far_enabled and attributes.dof_blur_near_enabled and is_equal_approx(attributes.dof_blur_far_distance, 12.0), "近远景深都打开")
expect(is_equal_approx(Environment.new().glow_hdr_threshold, 1.0) and Environment.new().glow_blend_mode == Environment.GLOW_BLEND_MODE_SCREEN, "glow_hdr_threshold 默认 1.0 glow_blend_mode 默认 SCREEN")
var ground := MeshInstance3D.new()
var plane := PlaneMesh.new()
plane.size = Vector2(60.0, 60.0)
ground.mesh = plane
root.add_child(ground)
for z: float in [-3.0, -8.0, -14.0]:
	var pillar := MeshInstance3D.new()
	pillar.mesh = BoxMesh.new()
	pillar.position = Vector3(0.0, 0.5, z)
	root.add_child(pillar)
var sun := DirectionalLight3D.new()
sun.rotation_degrees = Vector3(-50.0, 30.0, 0.0)
root.add_child(sun)
var cam := Camera3D.new()
cam.position = Vector3(0.0, 2.0, 3.0)
cam.rotation_degrees = Vector3(-12.0, 0.0, 0.0)
root.add_child(cam)
var with_effects := await snap.call() as Image
node.environment = null
node.camera_attributes = null
var without_effects := await snap.call() as Image
expect(distance.call(with_effects, without_effects) as float > 0.05, "配方里的效果改变画面")
node.environment = env
node.camera_attributes = attributes
var again := await snap.call() as Image
expect(distance.call(with_effects, again) as float < 0.001, "还原后画面一致")
node.environment = env
var env_only := await snap.call() as Image
var env_fog_off := env.duplicate() as Environment
env_fog_off.fog_enabled = false
node.environment = env_fog_off
var no_fog := await snap.call() as Image
expect(distance.call(env_only, no_fog) as float > 0.01, "fog_enabled 单独改变画面")
cam.free()
ground.free()
sun.free()
```

## references/render-check.md `get_texture().get_image()`

<!-- run: mode render -->

<!-- check: prepare -->
```gdscript
var image := Image.create_empty(16, 32, false, Image.FORMAT_RGBA8)
image.fill(Color.RED)
image.save_png("res://character.png")
```
