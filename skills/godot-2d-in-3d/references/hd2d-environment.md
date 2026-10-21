# HD-2D 环境配方

像素角色放进带光影、雾、景深的 3D 场景。所有效果都挂在 `WorldEnvironment` 或相机上，不需要额外视口。

## 渲染器支持

数据来自 `Environment`、`CameraAttributes` 的 XML 与官方 3D 后处理页。

| 效果 | Forward+ | Mobile | Compatibility |
|---|---|---|---|
| `glow_enabled` | 支持 | 支持，范围偏小，`glow_hdr_threshold` 要降到 0.9 左右，`glow_intensity` 要升到 1.5 | 简化实现，`glow_levels/*`、`glow_strength`、`glow_blend_mode` 无效 |
| `ssao_enabled` | 支持 | 不支持 | 4.6 起有简化版，只有 radius 与 intensity 可调 |
| `fog_enabled` | XML 无限制说明 | XML 无限制说明 | 4.7.2 llvmpipe 实测有效 |
| `volumetric_fog_enabled` | 支持 | 不支持 | 不支持 |
| 景深 `dof_blur_*` | 支持 | 支持 | 不支持 |
| `ssr_enabled`、`ssil_enabled`、SDFGI | 支持 | 不支持 | 不支持 |
| `Decal` | 支持 | 支持，每个网格最多 8 个 | 4.7 不支持 |

项目设置 `rendering/renderer/rendering_method` 选渲染器。HD-2D 的景深、体积雾要求 Forward+。

## 配方

<!-- check: extends WorldEnvironment -->
```gdscript
func _ready() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.55, 0.65, 0.8)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.6, 0.65, 0.8)
	env.ambient_light_energy = 0.6

	env.glow_enabled = true
	env.glow_intensity = 0.4
	env.glow_bloom = 0.1

	env.ssao_enabled = true
	env.ssao_radius = 1.0
	env.ssao_intensity = 2.0

	env.fog_enabled = true
	env.fog_light_color = Color(0.7, 0.75, 0.9)
	env.fog_density = 0.01
	env.fog_aerial_perspective = 0.3

	env.adjustment_enabled = true
	env.adjustment_saturation = 1.15
	env.adjustment_contrast = 1.05
	environment = env

	var attributes := CameraAttributesPractical.new()
	attributes.dof_blur_far_enabled = true
	attributes.dof_blur_far_distance = 12.0
	attributes.dof_blur_far_transition = 8.0
	attributes.dof_blur_near_enabled = true
	attributes.dof_blur_near_distance = 3.0
	attributes.dof_blur_near_transition = 2.0
	attributes.dof_blur_amount = 0.08
	camera_attributes = attributes
```

- 场景里只放一个 `WorldEnvironment`。`Camera3D.environment` 与 `Camera3D.attributes` 可以按相机覆盖，当前相机有设置时优先于 `WorldEnvironment`。
- 光线要用 `DirectionalLight3D` 当主光，`shadow_enabled` 打开。角色用 `ALPHA_CUT_DISCARD` 或 `ALPHA_CUT_OPAQUE_PREPASS` 才投影，见 SKILL.md。
- 环境光决定背光面的亮度，HD-2D 里常取偏冷的色加主光偏暖。`FIXED_Y` 精灵的法线水平，竖直向下的光照不到它。
- `ssao_enabled` 要深度与法线，混合透明的精灵不进这些缓冲，不会被遮蔽。角色用不透明系的 `alpha_cut` 才吃到。
- `fog_aerial_perspective` 让远处的天空色混进雾里，层次感更强。

## 移轴景深

官方文档把近远模糊同时开启称为 tilt shift 效果。

- 远模糊：`dof_blur_far_enabled`，`dof_blur_far_distance` 是开始模糊的距离，`dof_blur_far_transition` 为正时是模糊从 0 增长到最大值的过渡距离，为负时按物理方式增长。
- 近模糊：`dof_blur_near_enabled`，`dof_blur_near_distance` 以内开始模糊。
- `dof_blur_amount` 是最大模糊量，值大代价高，按画风尽量小。
- 景深按相机深度模糊，不按屏幕位置。相机俯视时屏幕下方近、上方远，两侧模糊叠加就成了上下虚化的移轴观感。相机越平，效果越接近普通景深。
- 景深在 `transparent_bg` 为 true 的视口上不工作。
- 焦点距离要设成角色到相机的实际距离：相机 `global_position` 与角色 `global_position` 的距离，把 `dof_blur_far_distance` 设得比它稍大、`dof_blur_near_distance` 设得比它稍小。

## 调试

- 效果不出现时先看渲染器：Compatibility 下体积雾、景深、`Decal` 都不显示。
- glow 作用在超过 `glow_hdr_threshold` 的像素上，默认 1.0。要让精灵发光，把材质的亮度推过阈值，或降低阈值。在 4.7.2 Compatibility 加 llvmpipe 上读像素没有看到 glow 效果，原因未查明，这一条未验证。
