# 渲染器 光照 阴影 GI

选型表在 SKILL.md。这里是差异细节、灯与阴影参数、烘焙设置。

## 渲染器差异

| 项 | Compatibility | Mobile | Forward+ |
|---|---|---|---|
| 驱动 | OpenGL | Vulkan D3D12 Metal | Vulkan D3D12 Metal |
| 网页 | 唯一选择 | 否 | 否 |
| 灯数量 | 每网格 8 个 | 每网格 8 个 每视图 256 个 | 每簇 512 个 可调 |
| 方向光 | 最多 8 个 | 最多 8 个 | 最多 8 个 |
| 光照投影纹理 | 否 | 是 | 是 |
| 定位灯 PCSS | 否 | 是 | 是 |
| 方向光 PCSS | 否 | 否 | 是 |
| ReflectionProbe | 每网格 2 个 | 每网格 8 个 | 场景中最多 256 个 默认 64 |
| LightmapGI | 能渲染 烘焙需 RenderingDevice | 是 | 是 |
| SSAO | 是 | 否 | 是 |
| VoxelGI SDFGI SSIL SSR 体积雾 次表面散射 | 否 | 否 | 是 |
| 色调映射 雾 泛光 调整 | 是 泛光实现更简单 | 是 | 是 |
| 全屏 shader 后处理 | 是 | 是 | 是 |
| `CompositorEffect` | 否 | 是 | 是 |
| 粒子拖尾 粒子 SDF 碰撞 | 否 | 是 | 是 |
| 景深模糊 | 否 | 是 | 是 |
| 2D HDR 视口 `rendering/viewport/hdr_2d` | 否 | 是 | 是 |
| TAA FSR2 | 否 | 否 | 是 |
| FXAA SMAA | 否 | 是 | 是 |
| 法线粗糙度缓冲 | 否 | 否 | 是 |
| 贴花 `Decal` | 否 | 每网格资源 8 个 | 数量不限 与灯共用簇上限 512 |
| 自动曝光 | 否 | 否 | 是 |

- 新功能先进 Forward+，Mobile 随后，Compatibility 最后
- Forward+ 或 Mobile 在 Vulkan 不可用时回落到 D3D12，反过来也一样，两者都不行回落 Compatibility，由 `rendering/rendering_device/fallback_to_opengl3` 控制
- 色彩精度：Compatibility RGBA8，Mobile RGB10A2 开 HDR 2D 时 RGBA16F，Forward+ RGBA16F
- Compatibility 下 Environment 的 `glow_levels/*` `glow_normalized` `glow_strength` `glow_blend_mode` `glow_mix` `glow_map` 无效
- 选渲染器写在 `rendering/renderer/rendering_method`，值 `forward_plus` `mobile` `gl_compatibility`，可加 `.mobile` 特性覆盖

## 灯

| 灯 | 要点 |
|---|---|
| `DirectionalLight3D` | 太阳。阴影用 PSSM 分 2 或 4 段。`directional_shadow_max_distance` 设成场景所需 |
| `OmniLight3D` | `omni_range` 是衰减范围。`omni_shadow_mode` 默认立方体 双抛物面更快但有形变 |
| `SpotLight3D` | 阴影只渲一张图 比全向灯快。张角超过 89 度阴影失效 |
| `AreaLight3D` | 4.7+ 矩形面光 最贵 少用。Compatibility 里不投影且不支持纹理 Mobile 里半影大小不随距离变化 |

- 灯的 `shadow_enabled` 默认关
- 灯的 `light_cull_mask` 决定照亮哪些可见层，`shadow_caster_mask` 4.4+ 决定哪些层投影
- 距离淡出：`distance_fade_enabled` 加 `distance_fade_begin` `distance_fade_shadow` `distance_fade_length`，大场景里减少灯数
- 灯的 `light_indirect_energy` 控制它对 GI 的贡献
- PCSS 很贵。方向光用 `light_angular_distance` 大于 0 开启，定位灯用 `light_size`。给玩家一个关闭选项
- 开 `rendering/lights_and_shadows/use_physical_light_units` 后灯用物理单位，配合 `CameraAttributesPhysical`

## 阴影参数

| 项 | 做法 |
|---|---|
| 自阴影纹路 | 先加 `shadow_normal_bias` 再加 `shadow_bias`。加太多阴影会变薄或脱离物体 |
| 近处糊 | 调 `directional_shadow_split_1` 让第一段更小 |
| 段间过渡明显 | 开 `directional_shadow_blend_splits` 牺牲细节与性能 |
| 远处突然消失 | `directional_shadow_fade_start` 与 `directional_shadow_max_distance` 配合 完全覆盖场景时可设 1.0 |
| 大面片缺阴影 | `directional_shadow_pancake_size` 最后才动 |
| 薄墙漏光 | `GeometryInstance3D.cast_shadow` 用双面 |
| 小物件不要阴影 | `cast_shadow` 设 Off 减少阴影绘制 |
| 方向光阴影分辨率 | `rendering/lights_and_shadows/directional_shadow/size` 默认 4096 低端降到 2048 |
| 阴影滤波 | `rendering/lights_and_shadows/directional_shadow/soft_shadow_filter_quality` 与 `positional_shadow/soft_shadow_filter_quality` |
| 深度精度 | `directional_shadow/16_bits` 与 `positional_shadow/atlas_16_bits` 默认 16 位 32 位贵且差别小 |
| 定位灯图集 | `positional_shadow/atlas_size` 加四个象限的 `atlas_quadrant_N_subdiv` 默认最多 88 盏有阴影的灯 同尺寸灯多的场景把四个象限设成一样 |

定位灯阴影的画质可在运行时改根视口，方向光阴影质量通过 `RenderingServer` 改。

## GI 与烘焙

### 网格与灯的 GI 模式

| 对象 | Disabled | Static | Dynamic |
|---|---|---|---|
| `MeshInstance3D` 的 `gi_mode` 默认 Static | 接收间接光 不贡献 | 参与 SDFGI VoxelGI LightmapGI 烘焙 | 不参与烘焙 光照图下用 LightmapProbe 接收 VoxelGI 下可发光 |
| `Light3D` 的 `light_bake_mode` 默认 Dynamic | 烘焙忽略 | 直接光与间接光都烘进光照图 实时灯对烘焙面不再有效 | 只烘间接光 直接光与阴影仍实时 可小幅改颜色与位置 |

- 小型动态物体和角色用 Disabled 或 Dynamic
- 静态关卡用 Static
- 方向光 Dynamic 加定位灯 Static 是常见混合方案

### LightmapGI

1. 导入面板 Light Baking 设为 Static Lightmaps 并设 Lightmap Texel Size，导入默认值 0.2。CSG 与程序化基础网格不能烘，CSG 先 Bake Mesh Instance 再 Unwrap UV2
2. 场景里放 `LightmapGI`，它只烘兄弟节点与子节点
3. `quality` `bounces` 默认 3 最多 16，`directional` 加方向信息得到模糊高光，`use_denoiser` 默认开，去噪器在项目设置 `rendering/lightmapping/denoising/denoiser`
4. 动态物体用 `LightmapProbe`，`generate_probes_subdiv` 可自动生成
5. 同一网格以相差一倍以上的缩放复用时，用 `GeometryInstance3D.gi_lightmap_texel_scale` 调整，只能提高精度 4.4+
6. 网页编辑器不能烘焙，已烘的在网页可渲染
7. 显存大纹理可能崩溃 先放大 texel size

### VoxelGI

- `size` 要罩住区域，`subdiv` 越高越细
- 数据存 `.res`
- 静态网格的自定义 `ShaderMaterial` 烘焙时被当作纯黑，要自发光就用 Dynamic
- 墙比体素薄会漏光，旋转节点再烘可缓解条纹
- 画质在项目设置，`rendering/global_illumination/gi/use_half_resolution` 可降成半分辨率

### SDFGI

- 环境里开 `sdfgi_enabled`，不需要摆节点，跟随相机
- `sdfgi_use_occlusion` 减少漏光 `sdfgi_read_sky_light` 室外开 室内关
- `sdfgi_cascades` 默认 4，相机快速移动或小场景再降低
- `sdfgi_y_scale` 默认 75%，平坦场景降到 50% 可提升质量且不增加开销
- `sdfgi_bounce_feedback` 默认 0.5，超过 0.5 在亮材质场景可能越来越亮
- `rendering/global_illumination/sdfgi/probe_ray_count` 控制每帧射线数

### ReflectionProbe

- `update_mode` 默认 Once，Always 很贵
- `size` 不必是正方形 可以旋转贴合房间
- `box_projection` 室内房间更准 `interior` 标记室内
- `ambient_mode` 默认 Environment 即可作局部环境光
- 单独使用可当没有 GI 时的反射来源

## 环境

`Environment` 资源的生效顺序：`Camera3D.environment`，`WorldEnvironment`，编辑器预览环境（只在编辑器里）。

| 项 | 要点 |
|---|---|
| 背景 | Clear Color Custom Color Sky Canvas Keep Camera Feed。背景为 Sky 时天空也提供环境光与反射 |
| 色调映射 | 默认 Linear 亮部截断 Filmic ACES AgX(4.4+) 可选 `tonemap_white` 写实场景至少 6.0，AgX 用 `tonemap_agx_white`，Mobile 的 `tonemap_white` 要 2.0 以下 |
| 泛光 | `glow_hdr_threshold` 默认 1.0 `glow_bloom` 默认 0.0 只有超过阈值的亮部发光 Mobile 阈值降到 0.9。`glow_blend_mode` 默认 Screen Compatibility 固定用 Screen |
| SSAO SSR SSIL | 昂贵 低端关 质量在项目设置 `rendering/environment/ssao/quality` 等 |
| 雾 | `fog_mode` 深度或指数 体积雾仅 Forward+ |
| 调整 | `adjustment_enabled` 亮度 对比度 饱和度 |

## 相机属性

`CameraAttributesPractical` 用任意单位，含自动曝光与景深。`CameraAttributesPhysical` 用真实单位，焦距毫米，放到相机上时会覆盖 `fov` `near` `far` `keep_aspect`。自动曝光只有 Forward+ 支持。`Camera3D.attributes` 覆盖 `WorldEnvironment` 的设置。放在相机上景深不会在编辑器视口里显示，除非预览该相机。

## 参考

- https://docs.godotengine.org/en/stable/tutorials/3d/lights_and_shadows.html
- https://docs.godotengine.org/en/stable/tutorials/3d/global_illumination/introduction_to_global_illumination.html
- https://docs.godotengine.org/en/stable/tutorials/3d/environment_and_post_processing.html
