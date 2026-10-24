---
name: godot-2d-in-3d
description: 在 Godot 4 的 3D 场景里放 2D 角色时用，2.5D 纸片人 HD-2D 像素角色配 3D 场景。Sprite3D AnimatedSprite3D billboard 正对镜头、pixel_size、投影阴影 cast_shadow、透明排序、像素清晰不发糊、SubViewport 把 2D 贴进 3D、Label3D、景深移轴。纯 2D 游戏见 godot-2d。
---

# Godot 2D 角色放进 3D 场景

用 Sprite3D、SubViewport 把 2D 美术放进真 3D 场景，配 Environment 做 HD-2D 观感。纯 2D 项目、TileMapLayer、Camera2D 不在这里，见 godot-2d。动画状态机见 godot-animation，着色器细节见 godot-shaders-vfx，UI 主题见 godot-ui。

本页标了实测的条目，是在 Godot 4.7.2 上用 xvfb 虚拟显示器加软件渲染读像素得到的，Compatibility 用 llvmpipe 软件 OpenGL，Forward+ 用 lavapipe 软件 Vulkan，方法见 references/render-check.md。billboard、翻转、光照、排序、像素对齐、阴影在两个渲染器上读数一致，差异只有 `ALPHA_CUT_HASH` 与 `Decal`。Mobile 与真实显卡上的效果只按 XML 与官方文档写。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 3D 里的 2D 角色 | `Sprite3D`、`AnimatedSprite3D` | 手写四边形网格加 shader |
| 始终面向相机 | `SpriteBase3D.billboard` 取 `BILLBOARD_FIXED_Y` | 每帧 `look_at` 相机 |
| 朝向翻转 | `flip_h` | `scale.x = -1`，billboard 下无效 |
| 角色阴影 | `alpha_cut` 取 `ALPHA_CUT_DISCARD` 或 `ALPHA_CUT_OPAQUE_PREPASS` | 额外画一个阴影网格 |
| 脚下软阴影 | `Sprite3D` 平放，或 `Decal` 限 Forward+ 与 Mobile | 每帧射线加手摆网格 |
| 2D 场景、2D 骨骼、Spine 贴进 3D | `SubViewport` 加 `ViewportTexture` | 逐帧 `get_image` 拷贝 |
| 世界里的文字 | `Label3D` | 每个文字一个 SubViewport |
| 屏幕固定 HUD | `CanvasLayer` 加 Control | 3D 里摆 UI 面板 |
| 头顶血条跟随 | `Camera3D.unproject_position` 定位 Control，或 Sprite3D | 手算投影矩阵 |
| 泛光、环境光遮蔽、雾 | `WorldEnvironment` 的 `Environment` | 多个 SubViewport 叠 bloom |
| 移轴景深 | `CameraAttributesPractical` 的近远模糊 | 后处理 shader 手写模糊 |

## 取舍表

先定路线再动手，中途换路线要重做美术摆放与相机。

| 维度 | 2D 节点手算透视伪 3D | 真 3D 加 Sprite3D |
|---|---|---|
| 摆放 | 位置、缩放、排序全靠每帧自己算 | 节点在 3D 空间，相机负责投影 |
| 相机自由度 | 固定角度，旋转或俯仰要重写公式 | 任意移动、旋转、改 fov |
| 前后遮挡 | 手改 `z_index` 或 `y_sort_enabled` | 深度缓冲，透明物要处理排序 |
| 光照阴影 | `Light2D` 平面光，阴影靠 `LightOccluder2D` | 真 3D 光源，精灵可接受并投射阴影 |
| 雾、景深、SSAO | 没有，只有 glow，要 HDR 2D 或 `BG_CANVAS` | `Environment` 与相机属性，按渲染器取舍 |
| 像素对齐 | 项目设置一键取整，见 godot-2d | 要满足整数倍像素规则，见下 |
| 物理 | `CharacterBody2D` 现成 | 用 3D 物理，或 2D 逻辑再映射 xz |
| 地图工具 | `TileMapLayer` | `GridMap` 或自建网格 |
| 渲染器限制 | HDR 2D 不支持 Compatibility | 效果随渲染器增减，见 references/hd2d-environment.md |
| 适合 | 横版、固定视角、深度仅作缩放层 | 视角会转或俯仰、要真实光影与景深 |

需要旋转镜头、动态光影、雾、景深中的任意一个，直接走真 3D。只需要前景大、后景小时，手算缩放更省事。

## 做法

### 角色 Sprite3D 最短配置

```gdscript
extends Sprite3D

func _ready() -> void:
	pixel_size = 1.0 / 32.0
	billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	shaded = true
	var used := texture.get_image().get_used_rect()
	offset.y = used.end.y - texture.get_height() * 0.5
```

- `pixel_size` 默认 0.01，一张 32 像素的图只有 0.32 米。按每米多少个贴图像素定，32 像素每米就是 `1.0 / 32.0`。
- `offset` 单位是贴图像素。居中的精灵向上偏移半个高度，原点就落在图片下沿；脚底贴地、旋转和缩放以脚为轴，要对准的是不透明脚底，不是图片下沿。
- 贴图底部常留透明行，直接取半个高度会让脚悬空。先量脚底行：`Image.get_used_rect()` 的 `end.y` 是最后一个不透明行的下沿，`offset.y` 取它减半个高度。16x16 的图最后一行透明，`offset.y` 是 7 不是 8，`pixel_size` 为 0.0625 时脚悬空 0.0625 米。上面的代码只适用于单帧贴图，精灵表要按帧区域量。写 `.tscn` 时读不了运行时数据，用脚本或 PIL 读像素算出常数。
- `shaded` 默认 false，精灵不受光，光照与阴影接收都要手动开。
- `texture_filter` 默认 `TEXTURE_FILTER_LINEAR_WITH_MIPMAPS`，像素图会糊。
- 导入页的 Detect 3D：贴图第一次被 3D 使用时编辑器自动把它改成 VRAM Compressed 加 mipmap，并输出日志，像素图会出块。在 Import 面板把 Detect 3D > Compress To 设为 Disabled 并保持 Compress > Mode 为 Lossless，再重导入。
- TextureAtlas 导入类型只支持 2D，不能给 Sprite3D 用。

C# 的枚举类型名带后缀，名字以编译为准：

<!-- check: extends Sprite3D -->
```csharp
public override void _Ready()
{
    PixelSize = 1f / 32f;
    Billboard = BaseMaterial3D.BillboardModeEnum.FixedY;
    TextureFilter = BaseMaterial3D.TextureFilterEnum.Nearest;
    AlphaCut = SpriteBase3D.AlphaCutMode.Discard;
    Shaded = true;
}
```

### billboard 三种模式

| 模式 | 行为 | 用在 |
|---|---|---|
| `BILLBOARD_DISABLED` | 按节点自身朝向，法线固定 | 地面贴花、告示牌 |
| `BILLBOARD_ENABLED` | 精灵平面始终正对相机，相机俯仰时精灵跟着后仰 | 特效、光点、从任意角度看的图标 |
| `BILLBOARD_FIXED_Y` | 精灵保持竖直，只绕世界 Y 转向相机 | HD-2D 角色，站立物 |

- 正交相机俯仰角为 p 时，`FIXED_Y` 精灵的屏幕高度是原高度乘 cos p，`ENABLED` 不缩短。实测俯仰 41.6 度，原高 72 像素缩到 54 像素，与 72 乘 cos 41.6 度吻合。想保持原高，把 `scale.y` 设为 1 除以 cos p。
- billboard 下绕 Y 的朝向由相机决定，实测父节点转 180 度无效。`ENABLED` 实测保留正缩放，负缩放的符号丢失。
- `ENABLED` 下精灵绕自身原点后仰，原点在中心时下沿会抬离地面。角色用 `FIXED_Y` 并把原点放脚底。

### 朝向翻转

只用 `flip_h`，`AnimatedSprite3D` 同样有。

```gdscript
extends AnimatedSprite3D

func face(direction_x: float) -> void:
	if direction_x != 0.0:
		flip_h = direction_x < 0.0
```

`scale.x = -1` 在 billboard 下不翻转，实测左右颜色不变。再配 `double_sided = false`，`ENABLED` 下实测精灵整个被背面剔除而消失。父节点转 180 度、父节点负缩放同样没有效果。非 billboard 下负缩放可以翻转。

### alpha_cut、阴影与排序

| `alpha_cut` | 阴影 | 边缘 | 排序 |
|---|---|---|---|
| `ALPHA_CUT_DISABLED` | 不投影，实测 0 像素 | 平滑半透明 | 按节点原点距离从后往前，会错 |
| `ALPHA_CUT_DISCARD` | 轮廓正确，只投不透明部分 | 硬边，配 MSAA 与 `alpha_antialiasing_mode` | 写深度，无排序问题 |
| `ALPHA_CUT_OPAQUE_PREPASS` | 轮廓正确 | 不透明部分进深度预通道，边缘平滑 | 排序较稳，比前两者贵 |
| `ALPHA_CUT_HASH` | Forward+ 实测轮廓与 `DISCARD` 一致 | 抖动点阵 | 写深度 |

- `ALPHA_CUT_HASH` 在 4.7.2 Compatibility 加 llvmpipe 上实测不裁剪任何像素，alpha 为 0 的区域照样画出，阴影也是整块。Forward+ 加 lavapipe 上实测裁剪正确，阴影与 `DISCARD` 一致。Compatibility 项目先别用。
- 要接收 `DirectionalLight3D` 阴影并给别的物体投影，选 `DISCARD`，像素风的首选。半透明羽化边才选 `OPAQUE_PREPASS`。
- MSAA 对 alpha 裁剪的边缘效果差，需要精灵的 `alpha_antialiasing_mode` 设为 `ALPHA_ANTIALIASING_ALPHA_TO_COVERAGE`，或开 FXAA、TAA。
- `double_sided` 默认 true。设为 false 后，光从精灵背面来时不投影，实测同一光照下双面投 320 像素、单面 0 像素。billboard 精灵的正面朝相机，背光的主光会让阴影消失，要投影就保持双面。
- `billboard` 与阴影同时开时，阴影渲染按场景里的相机朝向，多相机场景结果未定义。
- 相机绕角色转时，billboard 精灵的影子跟着相机转向变形，光从相机侧面来时变窄。4.7.2 Compatibility 实测同一精灵同一光照下，顺光影子 2016 像素，侧光 0 像素，夹角 45 度 1383 像素。要稳定的影子：可见精灵 `cast_shadow` 关掉，另加同贴图、同 `alpha_cut`、同 `offset`、不开 billboard 的副本，`cast_shadow` 设 `SHADOW_CASTING_SETTING_SHADOWS_ONLY`，正面朝主光的水平方向。副本方案实测顺光 2016 像素，侧光 1978 像素，夹角 45 度 1991 像素，差在像素取样。
- 混合透明的物体不写深度，也不进法线粗糙度缓冲，依赖这些缓冲的 SSAO 等效果不会作用在它上面。HD-2D 角色用不透明系的 `alpha_cut`。

排序只在 `ALPHA_CUT_DISABLED` 时调。实测两张重叠精灵，A 在前 0.5 米：

| 设置 | 重叠处看到 |
|---|---|
| 默认 | 离相机近的 A |
| B 的 `sorting_offset` 设 2.0 | B |
| B 的 `render_priority` 设 1 | B |
| B 的 `no_depth_test` 设 true | A，B 先画，后画的 A 盖在上面 |
| 两者 `DISCARD`，B 的优先级与偏移都调高 | A，深度决定，两项都无效 |

- `sorting_offset` 在 `VisualInstance3D` 上，单位米，按排序距离加偏移。`render_priority` 只在透明物之间生效，不改变透明与不透明的先后。
- 不要靠 `no_depth_test` 解决排序，它关掉深度测试，精灵会穿墙可见。

### 光照

- `shaded = true` 后精灵接收 `Light3D`。billboard 模式下精灵的法线跟着转向相机，光线从相机一侧来才亮。
- 实测相机在 +Z 看精灵、光沿 -Z 传播，亮度 1；相机转到 +X、光沿 -X 传播，仍是 1；光从精灵背后来为 0。
- `FIXED_Y` 的法线水平，正上方来的光照不亮。俯仰 40 度的相机、光竖直向下，`ENABLED` 亮度约 0.83，`FIXED_Y` 为 0。主光要有水平分量并来自相机一侧，背光面靠环境光补。
- 精灵整面一个法线，没有凹凸。要法线贴图，用 `QuadMesh` 加 `StandardMaterial3D`，它同样支持 billboard，但 `billboard_keep_scale` 默认 false 会丢缩放。
- 需要环境光才不至于全黑：`Environment.ambient_light_source` 设成颜色或天空。

### 相机

```gdscript
extends Camera3D

func _ready() -> void:
	projection = Camera3D.PROJECTION_ORTHOGONAL
	size = 360.0 * (1.0 / 32.0)
```

- 正交 `keep_aspect` 默认 `KEEP_HEIGHT`，`size` 是视口高度对应的米数。想让一个贴图像素对应一个屏幕像素，`size = 视口高度像素 × pixel_size`，再除以整数倍放大。实测视口高 180、`pixel_size` 0.02，`size` 取 3.6 时 16 像素宽的精灵正好 16 像素。
- 透视下一个贴图像素对应一个屏幕像素的距离是 `视口高度 × pixel_size ÷ (2 × tan(fov ÷ 2))`，只在这个距离的平面上成立。
- 正交没有近大远小，视差靠相机移动与多层场景。透视有真实视差和前后缩放，但贴图像素在屏幕上大小随距离变，像素风容易出现粗细不均。
- 俯仰角决定地面与站立物的比例：竖直物体按 cos 缩短，地面纵深按 sin 缩短。角度越大越像俯视，越小越像侧视。经验起点是俯仰 25 到 45 度、透视 fov 20 到 35 度，这一条不是官方数值，按美术调。
- `fov` 小则透视变形小，接近正交，同时相机要退得更远。
- 3D 分辨率与 UI 缩放分开处理：`display/window/stretch/mode` 取 `canvas_items` 时 3D 不受拉伸影响，UI 按比例缩放。取 `viewport` 时 3D 也被渲染成低分辨率再放大。

### 像素对齐与闪烁

- 保证每个贴图像素占整数个屏幕像素。实测正交相机下每贴图像素 1.5 屏幕像素时，相邻贴图列宽交替 2、1、2、1；取 2 或 3 时全部一致。
- 缩放用整数倍：调相机 `size` 或视口整数缩放，不用任意比例。
- 整数倍下相机平移 0.37 个贴图像素，列宽不变，实测。
- `TEXTURE_FILTER_NEAREST` 不采样 mipmap，远处发颗粒感。`TEXTURE_FILTER_NEAREST_WITH_MIPMAPS` 远处平滑，需要导入时生成 mipmap，由 Detect 3D 自动打开。
- 透视相机下做不到全局整数倍，接受近处清晰、远处不均，或改正交。

### 地面阴影 blob

`Decal` 需要 Forward+ 或 Mobile，4.7.2 Compatibility 加 llvmpipe 实测不显示，Forward+ 加 lavapipe 实测显示，XML 也写明 Compatibility 不支持。通用写法是平放的 Sprite3D：

```gdscript
extends Sprite3D

func _ready() -> void:
	var gradient := Gradient.new()
	gradient.set_color(0, Color(0.0, 0.0, 0.0, 0.8))
	gradient.set_color(1, Color(0.0, 0.0, 0.0, 0.0))
	var tex := GradientTexture2D.new()
	tex.gradient = gradient
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	tex.width = 64
	tex.height = 64
	texture = tex
	axis = Vector3.AXIS_Y
	pixel_size = 0.02
	position.y = 0.01
```

- `axis` 取 Y 让精灵平放朝上。抬高 0.01 米避免与地面同深度闪烁。
- 用 `Decal` 时，`cull_mask` 要排除角色所在的渲染层，否则贴花也投到角色身上。贴花不能改变半透明材质的透明度。
- `Decal` 的 `texture_albedo` 不能直接用 ViewportTexture，需要先 `get_image` 再建 `ImageTexture`。

### SubViewport、文字与 UI

SubViewport 贴图、世界内 UI、Label3D、屏幕叠加 HUD 见 references/subviewport-ui.md。HD-2D 的环境、雾、景深配置见 references/hd2d-environment.md。

## 陷阱

- `Sprite3D` 默认不受光、默认线性加 mipmap 过滤、`pixel_size` 默认 0.01，三项都要改。`double_sided` 默认 true，保持，单面会让背光时阴影消失。
- `scale.x = -1` 翻转，在 billboard 下无效，单面渲染时还可能消失。用 `flip_h`。
- `ALPHA_CUT_DISABLED` 不投影，半透明精灵互相遮挡会错序。角色一律用不透明系的 `alpha_cut`。
- `render_priority` 与 `sorting_offset` 对 `DISCARD`、`OPAQUE_PREPASS` 无效，那是深度的事。
- SubViewport 不继承项目的默认纹理过滤与像素取整，2D 内容进了 SubViewport 又变糊，见 references/subviewport-ui.md。
- 图片被 3D 使用后被自动改成 VRAM Compressed，像素图出块。关掉 Detect 3D 的压缩。
- `Decal` 在 Compatibility 4.7 不可用，用平放 Sprite3D 替代。
- 手算透视缩放伪 3D 时每帧维护位置、缩放、排序与光照，需求里出现旋转镜头、动态光影或景深就改真 3D。
- 本页没有在 Mobile 上渲染验证的条目，HDR 2D 的 SubViewport 色彩在两个渲染器上都没验证。

## 参考

- references/subviewport-ui.md SubViewport 贴进 3D 的设置、Label3D、世界内 UI、屏幕叠加
- references/hd2d-environment.md Environment 配方、渲染器支持表、移轴景深
- references/render-check.md 用虚拟显示器读像素验证渲染行为，已验证项清单
- https://docs.godotengine.org/en/stable/tutorials/3d/3d_rendering_limitations.html
- https://docs.godotengine.org/en/stable/tutorials/3d/3d_text.html
- https://docs.godotengine.org/en/stable/tutorials/3d/environment_and_post_processing.html
- https://docs.godotengine.org/en/stable/tutorials/3d/using_decals.html
- https://docs.godotengine.org/en/stable/tutorials/rendering/viewports.html
- https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_images.html
