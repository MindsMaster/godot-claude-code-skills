# 虚拟显示器渲染验证

`--headless` 用的是空渲染器，不出图。验证 billboard、阴影、排序、过滤这类渲染行为，要用虚拟显示器加软件 OpenGL，在 Compatibility 渲染器上读像素。

## 命令

```
xvfb-run -a godot --path <工程> --rendering-driver opengl3 --resolution 320x180 -s check.gd
```

- 工程的 `rendering/renderer/rendering_method` 设为 `gl_compatibility`。没有 Vulkan 的环境下 Forward+ 与 Mobile 起不来，会退回 Compatibility。
- 只能验证 Compatibility 上有的行为。体积雾、景深、`Decal`、Forward+ 的 glow 与 SSAO 这里验证不了，要在目标渲染器上自己看。
- 用 `SceneTree` 的 `_initialize` 而不是 `_init`，前者里节点才算在树内，`look_at` 才可用。
- 视口尺寸要等第一帧之后才对，不要在 `_initialize` 里取。

## 读像素

```gdscript
extends SceneTree

func _initialize() -> void:
	var camera := Camera3D.new()
	root.add_child(camera)
	camera.look_at_from_position(Vector3(0, 0, 3), Vector3.ZERO)
	var sprite := Sprite3D.new()
	sprite.texture = load("res://character.png")
	sprite.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	root.add_child(sprite)
	for i in 3:
		await process_frame
	var image := root.get_texture().get_image()
	@warning_ignore("integer_division")
	var center := image.get_pixelv(image.get_size() / 2)
	print(center)
	quit()
```

- 等 3 帧再取图，3 帧下读数稳定，更少的帧数没有试过。
- 背景用 `Environment.BG_COLOR` 纯黑，精灵用纯色贴图，读中心点与左右偏移点，比对颜色就能判断翻转、遮挡、阴影、裁剪。
- 数宽度和高度时按颜色阈值逐行逐列扫，不看单点。
- 阴影用 `DirectionalLight3D` 的 `shadow_enabled`，地面用受光的白色材质，统计暗色像素数。精灵不受光时读到的是贴图颜色，不会混入阴影。
- 相机位置参与结果，`look_at_from_position` 的目标点和相机距离不同，实际俯仰角会偏离名义值，计算比例时用真实角度。

## 已验证项

在 4.7.2 Compatibility 加 llvmpipe 上读像素得到的结论，换显卡驱动可能不同，正文里标了实测的条目来自这里：

- billboard 下 `scale.x = -1` 不翻转，`flip_h` 翻转，父节点旋转 180 度无效。
- `ALPHA_CUT_DISABLED` 不投影，`DISCARD` 与 `OPAQUE_PREPASS` 投影轮廓正确，`HASH` 不裁剪。`double_sided = false` 在光从背面来时不投影。
- 排序下 `sorting_offset` 与 `render_priority` 仅在混合透明时生效。
- billboard 的法线转向相机，`FIXED_Y` 的法线水平。
- 正交 `size` 与 `pixel_size` 的换算，每贴图像素 1.5 个屏幕像素时列宽 2、1 交替。
- SubViewport 不继承项目的默认过滤、取整、HDR 2D。
- 贴图被 3D 使用后导入选项被自动改成 VRAM Compressed 加 mipmap。
