# HD-2D 环境配方

像素角色放进带光影、雾、景深的 3D 场景。效果都挂在 `WorldEnvironment` 或相机上，不需要额外视口。

## 渲染器支持

数据来自 `Environment`、`CameraAttributes` 的 XML 与官方 3D 后处理页。

| 效果 | Forward+ | Mobile | Compatibility |
|---|---|---|---|
| `glow_enabled` | 支持 | 支持，动态范围上限 2.0，`glow_hdr_threshold` 要降到 0.9 左右，`glow_intensity` 要升到 1.5 | 简化实现，`glow_levels/*`、`glow_strength`、`glow_blend_mode` 无效 |
| `ssao_enabled` | 支持 | 不支持 | 4.6 起有简化版，只有 radius 与 intensity 可调 |
| `fog_enabled` | 支持 | 支持 | 支持，4.7.2 llvmpipe 实测有效 |
| `volumetric_fog_enabled` | 支持 | 不支持 | 不支持 |
| 景深 `dof_blur_*` | 支持 | 支持 | 不支持 |
| `ssr_enabled`、`ssil_enabled`、SDFGI | 支持 | 不支持 | 不支持 |
| `Decal` | 支持 | 支持，每个网格最多 8 个 | 4.7 不支持 |

- 渲染器在 `rendering/renderer/rendering_method` 选
- 体积雾要求 Forward+，景深要求 Forward+ 或 Mobile

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

```csharp
public partial class Hd2dEnvironment : WorldEnvironment
{
    public override void _Ready()
    {
        var env = new Godot.Environment
        {
            BackgroundMode = Godot.Environment.BGMode.Color,
            BackgroundColor = new Color(0.55f, 0.65f, 0.8f),
            AmbientLightSource = Godot.Environment.AmbientSource.Color,
            AmbientLightColor = new Color(0.6f, 0.65f, 0.8f),
            AmbientLightEnergy = 0.6f,
            GlowEnabled = true,
            GlowIntensity = 0.4f,
            GlowBloom = 0.1f,
            SsaoEnabled = true,
            SsaoRadius = 1.0f,
            SsaoIntensity = 2.0f,
            FogEnabled = true,
            FogLightColor = new Color(0.7f, 0.75f, 0.9f),
            FogDensity = 0.01f,
            AdjustmentEnabled = true,
            AdjustmentSaturation = 1.15f,
            AdjustmentContrast = 1.05f,
        };
        Environment = env;

        CameraAttributes = new CameraAttributesPractical
        {
            DofBlurFarEnabled = true,
            DofBlurFarDistance = 12.0f,
            DofBlurFarTransition = 8.0f,
            DofBlurNearEnabled = true,
            DofBlurNearDistance = 3.0f,
            DofBlurNearTransition = 2.0f,
            DofBlurAmount = 0.08f,
        };
    }
}
```

- C# 里写 `Godot.Environment`，`using System;` 时与 System.Environment 重名
- 场景里只放一个 `WorldEnvironment`
- `Camera3D.environment` 与 `Camera3D.attributes` 按相机覆盖，优先于 `WorldEnvironment`
- 主光用 `DirectionalLight3D`，开 `shadow_enabled`
- 角色用 `ALPHA_CUT_DISCARD` 或 `ALPHA_CUT_OPAQUE_PREPASS` 才投影
- 环境光决定背光面亮度，常取偏冷环境色加偏暖主光
- `FIXED_Y` 精灵法线水平，竖直向下的光照不到它
- 混合透明精灵不进深度法线缓冲，不被 SSAO 遮蔽
- `fog_aerial_perspective` 要求 `background_mode` 为 `BG_SKY`，上例 `BG_COLOR` 下无效

## 移轴景深

近远模糊同时开启，官方称 tilt shift 效果。

| 属性 | 含义 |
|---|---|
| `dof_blur_far_distance` | 远模糊开始的距离 |
| `dof_blur_far_transition` | 正值是模糊增长到最大的过渡距离，负值按物理方式增长 |
| `dof_blur_near_distance` | 以内开始近模糊 |
| `dof_blur_amount` | 最大模糊量，越大越贵 |

- 景深按相机深度模糊，不按屏幕位置
- 相机俯视时屏幕下方近上方远，两头模糊即成移轴观感
- 相机越平，越接近普通景深
- `transparent_bg` 为 true 的视口上景深不工作
- 焦点距离取相机到角色的实际距离
- `dof_blur_far_distance` 稍大于它，`dof_blur_near_distance` 稍小于它

## 调试

- 效果不出现先看渲染器，Compatibility 下体积雾、景深、`Decal` 不显示
- 体积雾与景深在 Compatibility 打警告，如 `Depth of field blur is only available when using the Forward+ or Mobile renderer.`
- 上例在 4.7.2 Forward+ 读像素，glow、SSAO、雾、景深开关都改变画面
- glow 作用在超过 `glow_hdr_threshold` 的像素上，默认 1.0
- `SpriteBase3D.modulate` 不支持超过 1.0 的亮度
- 精灵发光：降低阈值、设 `glow_bloom`，或 `material_override` 用自发光
- 实测 `emission_energy_multiplier` 为 4 的自发光，两个渲染器都出泛光
- Forward+ 的 `glow_blend_mode` 默认 `GLOW_BLEND_MODE_SCREEN`
- 改成 `GLOW_BLEND_MODE_SOFTLIGHT` 后黑底上读不到泛光
