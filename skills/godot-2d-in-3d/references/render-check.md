# 虚拟显示器渲染验证

`--headless` 用空渲染器，不出图。验证 billboard、阴影、排序、过滤，用虚拟显示器加软件渲染读像素。

## 命令

```
xvfb-run -a godot --path <工程> --rendering-driver opengl3 --resolution 320x180 -s check.gd
xvfb-run -a godot --path <工程> --rendering-driver vulkan --resolution 320x180 -s check.gd
```

| 命令 | 渲染器 | 软件实现 |
|---|---|---|
| `--rendering-driver opengl3` | Compatibility | Mesa llvmpipe |
| `--rendering-driver vulkan` | 按工程 `rendering/renderer/rendering_method`，默认 Forward+ | Mesa lavapipe |
| 再加 `--rendering-method mobile` | Mobile | Mesa lavapipe |

- Ubuntu 上装 `mesa-vulkan-drivers`
- 4.7.2 实测 Vulkan 打印 `Vulkan 1.4.318 - Forward+ - Using Device #0: Unknown - llvmpipe (LLVM 20.1.2, 256 bits)`
- Mobile 打印 `Forward Mobile`
- Vulkan 起不来时只打一条 `switching to OpenGL 3` 警告，退回 Compatibility
- 脚本开头断言 `RenderingServer.get_current_rendering_method()` 等于 `"forward_plus"`
- lavapipe 空脚本启动约 5.5 秒，opengl3 约 0.9 秒
- 每种材质或光照变体多一次着色器编译，CI 给足超时
- 软件渲染像素与真显卡不保证逐值一致，比对给阈值
- 同一清屏色 Forward+ 读 0.298，Compatibility 读 0.302
- 数色块宽度和像素数比单点颜色可靠
- Mobile 与真实显卡上的表现这里验证不了

| `_initialize` 里 | 做法 |
|---|---|
| `root` 还不在树内，加到它下面的节点 `look_at` 报错 | 先 `await process_frame` |
| `root.size` 是 (100, 100) | 一帧之后才是窗口尺寸 |

## 读像素

C# 项目同样用这个 GDScript 脚本：

<!-- check: gdonly -->
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

- 取图前等 3 帧，复杂场景保留余量
- 背景用 `Environment.BG_COLOR` 纯黑，精灵用纯色贴图
- 读中心点与左右偏移点，判断翻转、遮挡、阴影、裁剪
- 数宽高时按颜色阈值逐行逐列扫，不看单点
- 阴影：`DirectionalLight3D` 开 `shadow_enabled`，地面用受光白色材质，数暗色像素
- 精灵不受光时读到贴图颜色，不混入阴影
- `look_at_from_position` 的实际俯仰角会偏离名义值，算比例用真实角度

## 已验证项

4.7.2 上读像素的结论，换显卡驱动可能不同。两个渲染器读数一致的：

- billboard 下 `scale.x = -1` 不翻转，`flip_h` 翻转，父节点旋转 180 度无效
- `ALPHA_CUT_DISABLED` 不投影，`DISCARD` 与 `OPAQUE_PREPASS` 投影轮廓正确
- `double_sided = false` 在光从背面来时不投影
- `sorting_offset` 与 `render_priority` 仅在混合透明时生效
- billboard 的法线转向相机，`FIXED_Y` 的法线水平
- 每贴图像素 1.5 个屏幕像素时列宽 1、2 交替
- SubViewport 不继承项目的默认过滤、取整、HDR 2D
- 贴图被 3D 使用后导入选项自动改成 VRAM Compressed 加 mipmap

| 差异项 | Compatibility | Forward+ |
|---|---|---|
| `ALPHA_CUT_HASH` | 不裁剪 | 裁剪正确，阴影同 `DISCARD` |
| `Decal` | 不显示 | 显示 |
| 体积雾、景深 | 只打警告 | 有效 |
| 自发光泛光 | 有 | 有，`GLOW_BLEND_MODE_SOFTLIGHT` 下黑底无泛光 |
| 无环境无灯时 `shaded` 红色精灵 | 读 0 | 读 0.3 的红，来自默认清屏色环境光 |
