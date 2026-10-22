# 虚拟显示器渲染验证

`--headless` 用的是空渲染器，不出图。验证 billboard、阴影、排序、过滤这类渲染行为，要用虚拟显示器加软件渲染读像素。软件 OpenGL 跑 Compatibility，软件 Vulkan 跑 Forward+ 与 Mobile。

## 命令

```
xvfb-run -a godot --path <工程> --rendering-driver opengl3 --resolution 320x180 -s check.gd
xvfb-run -a godot --path <工程> --rendering-driver vulkan --resolution 320x180 -s check.gd
```

- 第一条是 Compatibility，用 Mesa llvmpipe 软件 OpenGL。第二条用 Mesa lavapipe 软件 Vulkan，渲染器按工程设置 `rendering/renderer/rendering_method`，默认 Forward+，命令行加 `--rendering-method mobile` 跑 Mobile。Ubuntu 上装 `mesa-vulkan-drivers`。
- 4.7.2 实测第二条打印 `Vulkan 1.4.318 - Forward+ - Using Device #0: Unknown - llvmpipe (LLVM 20.1.2, 256 bits)`，Mobile 打印 `Forward Mobile`。
- Vulkan 起不来时引擎只打一条 `switching to OpenGL 3` 警告就退回 Compatibility，脚本照常跑完。脚本开头断言 `RenderingServer.get_current_rendering_method()` 等于 `"forward_plus"`，否则读到的是 Compatibility 的像素。
- lavapipe 是 CPU 软件渲染。空脚本实测启动约 5.5 秒，opengl3 约 0.9 秒。每多一种材质或光照变体多一次着色器编译，场景里变体多时单个脚本要几十秒，CI 里给足超时，机器有负载时更慢。
- 软件渲染的像素与真实显卡不保证逐值一致。同一个默认清屏色像素，Forward+ 读 0.298，Compatibility 读 0.302。比对时给阈值，数色块宽度和像素数比单点颜色可靠。
- 体积雾、景深、`Decal`、SSAO、glow 的 Forward+ 行为用第二条命令验证，Compatibility 的差异见下面的已验证项。Mobile 与真实显卡上的表现这里仍然验证不了。
- 在 `_initialize` 里 `root` 还不在树内，引擎先调用 `_initialize`，之后才把 `root` 接上树。此时加到 `root` 下的节点 `is_inside_tree()` 为 false，`look_at` 报错且不生效，先 `await process_frame`。
- 视口尺寸也要等第一帧，实测 `_initialize` 里 `root.size` 是 (100, 100)，一帧之后才是窗口尺寸。

## 读像素

```gdscript
extends SceneTree

func _initialize() -> void:
	var camera := Camera3D.new()
	root.add_child(camera)
	var sprite := Sprite3D.new()
	sprite.texture = load("res://character.png")
	sprite.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	root.add_child(sprite)
	await process_frame
	camera.look_at_from_position(Vector3(0, 0, 3), Vector3.ZERO)
	for i in 3:
		await process_frame
	var image := root.get_texture().get_image()
	@warning_ignore("integer_division")
	var center := image.get_pixelv(image.get_size() / 2)
	print(center)
	quit()
```

- 取图前等 3 帧。本例在两个渲染器上从 1 帧起读数就稳定，复杂场景保留余量。
- 背景用 `Environment.BG_COLOR` 纯黑，精灵用纯色贴图，读中心点与左右偏移点，比对颜色就能判断翻转、遮挡、阴影、裁剪。
- 数宽度和高度时按颜色阈值逐行逐列扫，不看单点。
- 阴影用 `DirectionalLight3D` 的 `shadow_enabled`，地面用受光的白色材质，统计暗色像素数。精灵不受光时读到的是贴图颜色，不会混入阴影。
- 相机位置参与结果，`look_at_from_position` 的目标点和相机距离不同，实际俯仰角会偏离名义值，计算比例时用真实角度。

## 已验证项

在 4.7.2 上读像素得到的结论，Compatibility 用 llvmpipe，Forward+ 用 lavapipe，换显卡驱动可能不同。正文里标了实测的条目来自这里，除下面列出的差异外两个渲染器读数一致：

- billboard 下 `scale.x = -1` 不翻转，`flip_h` 翻转，父节点旋转 180 度无效。
- `ALPHA_CUT_DISABLED` 不投影，`DISCARD` 与 `OPAQUE_PREPASS` 投影轮廓正确。`double_sided = false` 在光从背面来时不投影。
- 排序下 `sorting_offset` 与 `render_priority` 仅在混合透明时生效。
- billboard 的法线转向相机，`FIXED_Y` 的法线水平。
- 正交 `size` 与 `pixel_size` 的换算，每贴图像素 1.5 个屏幕像素时列宽 1、2 交替。
- SubViewport 不继承项目的默认过滤、取整、HDR 2D。
- 贴图被 3D 使用后导入选项被自动改成 VRAM Compressed 加 mipmap。

两个渲染器的差异：

- `ALPHA_CUT_HASH` 在 Compatibility 不裁剪，在 Forward+ 裁剪正确，阴影与 `DISCARD` 一致。
- `Decal` 在 Compatibility 不显示，在 Forward+ 显示。
- 体积雾与景深在 Compatibility 只打警告，在 Forward+ 有效。
- 自发光材质的泛光两边都有。Forward+ 的 `glow_blend_mode` 默认 `GLOW_BLEND_MODE_SCREEN`，改成 `GLOW_BLEND_MODE_SOFTLIGHT` 后黑底上没有泛光。
- 没有 `WorldEnvironment` 也没有灯时，`shaded` 的红色精灵在 Forward+ 读到 0.3 的红，来自默认清屏色的环境光，Compatibility 读 0。
