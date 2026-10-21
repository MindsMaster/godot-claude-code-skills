# SubViewport、文字与 UI

## 把 2D 场景贴进 3D

用在 2D 骨骼动画、带粒子或着色器的 2D 特效、没有 3D 节点的第三方 2D 动画库，如 Spine 运行时。纯静态图集直接用 `Sprite3D` 更省。

<!-- check: extends Node3D -->
```gdscript
@onready var _viewport: SubViewport = $SubViewport
@onready var _sprite: Sprite3D = $Sprite3D

func _ready() -> void:
	_viewport.size = Vector2i(128, 128)
	_viewport.disable_3d = true
	_viewport.transparent_bg = true
	_viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	_sprite.texture = _viewport.get_texture()
	_sprite.pixel_size = 1.0 / 32.0
	_sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	_sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_OPAQUE_PREPASS
	_sprite.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
```

2D 内容放在 SubViewport 下，角色原点对准视口底边中点，Sprite3D 的 `offset.y` 设为视口高度的一半，原点落在脚底。上下方向与 2D 一致，实测没有翻转。

## SubViewport 属性

默认值与行为来自 XML 与 4.7.2 实测。

| 属性 | 默认 | 要点 |
|---|---|---|
| `size` | 512x512 | 渲染目标的像素数，Sprite3D 世界尺寸是 `size × pixel_size` |
| `transparent_bg` | false | 不开时背景是默认清屏色，实测灰色 0.3，贴到 3D 里是一块灰底 |
| `disable_3d` | false | 纯 2D 内容开 true，不创建 3D 渲染 |
| `render_target_update_mode` | `UPDATE_WHEN_VISIBLE` | 贴图在某帧被绘制才重渲。`UPDATE_ONCE` 渲一次后停，`UPDATE_ALWAYS` 每帧渲，`UPDATE_DISABLED` 不渲，`UPDATE_WHEN_PARENT_VISIBLE` 看父节点可见性 |
| `render_target_clear_mode` | `CLEAR_MODE_ALWAYS` | 每帧清屏。`CLEAR_MODE_NEVER` 保留上一帧，做拖影或累积，`CLEAR_MODE_ONCE` 下一帧清一次后转 `NEVER` |
| `canvas_item_default_texture_filter` | 线性 | 不继承项目设置，见下 |
| `snap_2d_transforms_to_pixel` | false | 不继承项目设置 |
| `use_hdr_2d` | false | 不继承项目设置 |
| `size_2d_override` | 0 | 非零时 2D 逻辑尺寸与渲染尺寸分离 |
| `size_2d_override_stretch` | false | 为 true 时 2D 内容拉伸填满渲染目标 |

- 项目里把 `rendering/textures/canvas_textures/default_texture_filter` 设成 Nearest 后，主视口是 Nearest，新建的 SubViewport 仍是线性。实测 2x2 贴图放大 16 倍，SubViewport 默认下有 14 个中间色像素，改成 Nearest 后为 0。像素风要给每个 SubViewport 手动设 `canvas_item_default_texture_filter`。
- 同理 `snap_2d_transforms_to_pixel` 和 `use_hdr_2d` 也要逐个设。
- `size_2d_override` 设 32x32，配合 `size` 64x64 与 `size_2d_override_stretch` 为 true，2D 坐标仍按 32x32 布局，输出分辨率翻倍。实测布局比例不变，Sprite3D 的 `pixel_size` 要相应减半才能保持世界尺寸。
- `ViewportTexture` 始终属于场景本地，场景根未 ready 时取到的数据可能不对。在代码里用 `get_texture` 取最稳妥。编辑器里指定时 `viewport_path` 相对场景根，不相对使用它的节点。
- 开 `use_hdr_2d` 后 `ViewportTexture` 是线性编码，直接显示会偏暗，需要时 `Image.linear_to_srgb` 转换。
- 高分辨率的 `ViewportTexture` 随场景实例化会造成卡顿，预先创建。
- `Decal`、`Light3D`、`PointLight2D` 不能直接用 `ViewportTexture`，先 `get_image` 建 `ImageTexture`，操作较慢，不要每帧做。
- 同一个 SubViewport 里可以摆多个角色，各自的 Sprite3D 用 `region_enabled` 与 `region_rect` 取自己的一块，省渲染目标。每个 SubViewport 都是一次独立渲染。

## 转发输入到世界内 UI

把 Control 面板渲染进 SubViewport 再贴到四边形上做世界内 UI，点击时射线求交，换算成视口坐标后用 `Viewport.push_input` 送进 SubViewport。官方有 GUI in 3D 演示项目，照它的射线与坐标换算写，不要自己推。

## Label3D

<!-- check: extends Label3D -->
```gdscript
func _ready() -> void:
	text = "Lv 12"
	font_size = 32
	pixel_size = 0.01
	outline_size = 8
	billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	alpha_cut = Label3D.ALPHA_CUT_DISCARD
```

- 默认值：`shaded` false、`cast_shadow` 关、`pixel_size` 0.005、`font_size` 32、`outline_size` 12、`alpha_cut` 为 `DISABLED`。
- 多个带描边的 Label3D 重叠会排序错乱，`alpha_cut` 取 `ALPHA_CUT_DISCARD` 缓解，代价是字边不如平滑；`ALPHA_CUT_OPAQUE_PREPASS` 保留平滑并可投影，仍有部分排序问题。
- 远处文字变糊：给字体开 mipmap，或改用 MSDF 字体渲染。
- `fixed_size` 为 true 时文字在屏幕上大小不随距离变，大小仍受相机 fov 或正交 `size` 影响。
- 要更清晰，把 `font_size` 调大同时把 `pixel_size` 调小。
- `Label3D` 不继承 UI 主题，字体用字体子资源设置。

选择：多数情况用 `Label3D`。要自定义 shader、字形有厚度、要自带投影用 `TextMesh`，它只支持动态字体，不支持位图字体。要整套 Control 的主题、按钮交互，用投影到屏幕的 Control。

## 投影到屏幕的 Control

血条、名牌用相机把 3D 点投到 2D，放在 `CanvasLayer` 下的 Control 上。不会被 3D 几何遮挡，需要时用射线判断。

<!-- check: extends Control -->
```gdscript
@export var target: Node3D

func _process(_delta: float) -> void:
	var camera := get_viewport().get_camera_3d()
	if camera == null or target == null:
		return
	var world_pos := target.global_position
	visible = not camera.is_position_behind(world_pos)
	position = camera.unproject_position(world_pos) - size * 0.5
```

- 分辨率和宽高比变化要在脚本里处理，Control 的缩放不随距离自动变化。
- 世界内跟着物体走、需要被遮挡、需要随距离缩放的，用 `Sprite3D` 或 `Label3D`。

## 屏幕叠加 HUD

- 3D 场景里的 HUD、暂停菜单放 `CanvasLayer` 下的 Control，不受 3D 相机影响。`layer` 大的在上。
- `display/window/stretch/mode` 取 `canvas_items` 时 UI 按分辨率缩放，3D 保持原生分辨率。取 `viewport` 时 3D 也变成低分辨率，像素风 UI 与 3D 都被放大。
- 要单独降 3D 分辨率，用 `Viewport.scaling_3d_scale`，UI 不受影响。
