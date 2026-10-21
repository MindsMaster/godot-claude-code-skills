# 2D 光照、HDR 与 glow

## 光照最短搭法

```ini
[node name="Dark" type="CanvasModulate" parent="."]
color = Color(0.2, 0.22, 0.35, 1)
```

<!-- check: extends PointLight2D -->
```gdscript
func _ready() -> void:
	var g := Gradient.new()
	g.set_color(0, Color.WHITE)
	g.set_color(1, Color(1, 1, 1, 0))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 256
	t.height = 256
	texture = t
	shadow_enabled = true
```

- `PointLight2D` 没有 `texture` 就不发光，纹理尺寸决定光的大小。编辑器里给 `texture` 选 New GradientTexture2D，Fill 设 Radial 即可，不用写代码。
- 没有 `CanvasModulate` 压暗时，灯只往场景上叠加亮度，亮场景里几乎看不出。
- 一个画布只能有一个 `CanvasModulate`，用 `CanvasLayer` 隔开可以各自着色。
- `DirectionalLight2D` 做日光月光，忽略 `range_item_cull_mask`，对所有 2D 节点生效。
- 阴影需要 `LightOccluder2D` 带 `OccluderPolygon2D`。TileSet 里建 Occlusion Layer 后瓦片自带遮挡。
- 受光与否由 `CanvasItem.light_mask` 与灯的 `range_item_cull_mask` 匹配决定，哪些遮挡体投影由 `shadow_item_cull_mask` 与 `LightOccluder2D.occluder_light_mask` 决定。
- `shadow_enabled` 逐灯收费，只给需要的灯开。
- 法线贴图与高光贴图：精灵的纹理换成 `CanvasTexture`，分别指定 diffuse、normal、specular。灯的 `height` 控制法线光照角度。
- 光照与阴影按视口像素分辨率计算，不跟贴图像素走。像素风要块状光影需要 shader，见 pixel-art.md。
- 一串平级 SubViewport 手搓光照或为每盏灯复制多份节点的做法，先改回内置的灯。

## HDR 2D 与 glow

- 项目设置 `rendering/viewport/hdr_2d` 打开，仅 Forward+ 与 Mobile，启动时读取。运行时改根 `Viewport.use_hdr_2d`。
- 场景里放 `WorldEnvironment`，`Environment.background_mode` 选 canvas，`glow_enabled` 打开。`background_canvas_max_layer` 限制受影响的 CanvasLayer，UI 不想发光就放更高的层。
- 让某个精灵发光：它的 `modulate` 或 `self_modulate` 的 Intensity 调到大于 1。没开 HDR 2D 时 2D 在 SDR 里渲染，颜色会被夹到 1，这招无效。
- 不开 HDR 2D 也能用 glow：把 `glow_hdr_threshold` 降到 1 以下，普通亮度的像素也会发光，但没法逐物体控制。
- 开 HDR 2D 后 2D 在线性空间渲染，canvas_item shader 里作为颜色输入的 sampler 要写 `source_color`，否则偏灰。关闭 HDR 时写了也无害。
- 命中闪白用 shader 的 uniform 配 Tween，不靠 modulate 调大于 1，后者依赖 HDR 2D 与 glow 设置。
- Compatibility 渲染器的 glow 是另一套简化实现，`glow_levels/*`、`glow_strength`、`glow_blend_mode` 无效。
