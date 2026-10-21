# 后处理

## 顺序与渲染器支持

| 级 | 手段 | Compatibility | Mobile | Forward+ |
|---|---|---|---|---|
| 1 | `Environment`：glow tonemap adjustments fog ssao 等 | 是 泛光为简化实现 | 无 SSAO SSR SSIL 体积雾 | 全部 |
| 2 | `CompositorEffect`（4.3+） | 否 | 是 | 是 |
| 3 | `CanvasLayer` 加 `ColorRect` 的全屏 shader | 是 | 是 | 是 |
| 4 | 3D 全屏四边形 | 是 | 是 | 是 |

先试 1，不够再 2，只能拿到屏幕颜色就够用选 3，要深度又不能用 2 选 4。`CompositorEffect` 各阶段都早于内置环境后处理。

`CompositorEffect` 的回调阶段：`EFFECT_CALLBACK_TYPE_PRE_OPAQUE` `POST_OPAQUE` `POST_SKY` `PRE_TRANSPARENT` `POST_TRANSPARENT`。`POST_TRANSPARENT` 在内置后处理之前。

## Environment 要点

- 放在 `WorldEnvironment`，每个场景树一个，`Camera3D.environment` 更优先
- 性能与画质项在项目设置，大部分要打开 Advanced 才可见
- `Environment` 作用于 2D 和 3D，2D 要把背景模式设为 Canvas

| 效果 | 属性与说明 |
|---|---|
| 色调映射 | `tonemap_mode` 默认 Linear 会截断亮部。Filmic ACES AgX（4.4+）。`tonemap_exposure` `tonemap_white` |
| 泛光 | `glow_enabled` `glow_intensity` 默认 0.3 `glow_hdr_threshold` 默认 1.0 `glow_bloom` `glow_blend_mode` `glow_levels/1` 到 `glow_levels/7`。放大缩小模式 `rendering/environment/glow/upscale_mode` |
| 调整 | `adjustment_enabled` `adjustment_brightness` `adjustment_contrast` `adjustment_saturation` `adjustment_color_correction`（颜色查找图） |
| 雾 | `fog_enabled` `fog_mode` `fog_density` `fog_light_color` `fog_height` `fog_depth_begin` |
| 体积雾 | `volumetric_fog_enabled`，仅 Forward+，配 `FogVolume` 与 `FogMaterial` 局部加雾 |
| 环境光遮蔽 | `ssao_enabled` `ssao_radius` `ssao_intensity`。Mobile 无 |
| 屏幕空间反射 | `ssr_enabled`，仅 Forward+ |
| 屏幕空间间接光 | `ssil_enabled`，仅 Forward+ |

景深与曝光在 `CameraAttributes` 上：`dof_blur_far_enabled` `dof_blur_far_distance` `dof_blur_amount`（`CameraAttributesPractical`），自动曝光 `auto_exposure_enabled` 仅 Forward+。景深模糊 Compatibility 不支持，且透明背景的视口不支持。

泛光默认几乎看不见：阈值是 1.0 时只有超出色调映射白点的像素才会发光。降 `glow_hdr_threshold`，或设 `glow_bloom` 大于 0，后者会让整屏变亮。Mobile 的动态范围只到 2.0，阈值可降到 0.9，`glow_intensity` 提到 1.5。

## 2D 的 glow

```ini
[rendering]

viewport/hdr_2d=true
```

```gdscript
extends Node2D

func _ready() -> void:
	var env: Environment = Environment.new()
	env.background_mode = Environment.BG_CANVAS
	env.glow_enabled = true
	env.glow_hdr_threshold = 0.8
	var world_env: WorldEnvironment = WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)
```

1. 必须：`Environment.background_mode` 设为 `BG_CANVAS`。2D 画布并入环境效果的管线靠它。Compatibility 下实测 Clear Color 无 glow，Canvas 有 glow
2. 路线 A，不开 HDR 2D，所有渲染器可用：2D 是 SDR，把 `glow_hdr_threshold` 降到 1.0 以下，物体靠亮度区分，控制力弱
3. 路线 B，开 HDR 2D，仅 Forward+ 与 Mobile：`rendering/viewport/hdr_2d`，只在启动时读取，运行时改根视口 `Viewport.use_hdr_2d`。之后用 `modulate` 或 `self_modulate` 的强度大于 1 选择谁发光
4. UI 不发光：UI 放进 `CanvasLayer`，层号大于 `Environment.background_canvas_max_layer`
5. 路线 B 的副作用：2D 在线性空间混合，半透明精灵更显眼，字体变粗，编辑器自身渲染也受影响；canvas shader 里的颜色采样器必须带 `source_color`，关掉 HDR 2D 时它仍然正确，所以总是写上
6. Compatibility 不支持 HDR 2D 与 `glow_blend_mode`，只走路线 A
7. 本地只在 Compatibility 下验证了第 1 点，Forward+ 与 Mobile 按文档写

不要用多个平级 `SubViewport` 手搓 bloom 与多缓冲，更不要为模拟 MRT 复制节点。灯光用 `PointLight2D` 与 `CanvasModulate`。

## 全屏 shader

```gdscript
extends CanvasLayer

func _ready() -> void:
	layer = 10
	var rect: ColorRect = ColorRect.new()
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat: ShaderMaterial = ShaderMaterial.new()
	mat.shader = load("res://shaders/post.gdshader") as Shader
	rect.material = mat
	add_child(rect)
```

- 铺满的 `ColorRect` 默认 `mouse_filter` 是 `MOUSE_FILTER_STOP`，会吞掉所有点击，必须改 `MOUSE_FILTER_IGNORE`
- 多个效果叠加时每个一个 `CanvasLayer`，`layer` 大的在上，后执行
- 只改局部时用 `BackBufferCopy` 复制一块区域，比整屏拷贝便宜
- 想让 UI 不受效果影响，把 UI 放进 `layer` 更大的 `CanvasLayer`
- 读不到深度，在 3D 里需要深度用下一节
- 这种全屏 shader 读到的是已渲染好的画面，每个 `CanvasLayer` 读到的是它下面所有层的结果

## 3D 全屏四边形

用于读深度的后处理，所有渲染器都可用，编辑器里也可见。配方见 [shader-recipes.md](shader-recipes.md)。要点：

- `QuadMesh` 的 `size` 设 `Vector2(2, 2)`，开 `flip_faces`
- 顶点着色器写 `POSITION = vec4(VERTEX.xy, 1.0, 1.0)`，4.3 以前的 `vec4(VERTEX, 1.0)` 不再适用，因为深度反向
- 网格作为相机的子节点，或把 `extra_cull_margin` 设到最大，防止被视锥剔除
- `render_mode unshaded, fog_disabled` 避免光照和雾影响
- 深度纹理只能读当前视口的，不能读别的视口

## CompositorEffect

```gdscript
@tool
class_name InvertEffect
extends CompositorEffect

const SHADER_SOURCE: String = """
#version 450
layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;
layout(rgba16f, set = 0, binding = 0) uniform image2D color_image;
layout(push_constant, std430) uniform Params {
	vec2 raster_size;
	vec2 reserved;
} params;
void main() {
	ivec2 uv = ivec2(gl_GlobalInvocationID.xy);
	ivec2 size = ivec2(params.raster_size);
	if (uv.x >= size.x || uv.y >= size.y) {
		return;
	}
	vec4 color = imageLoad(color_image, uv);
	color.rgb = vec3(1.0) - color.rgb;
	imageStore(color_image, uv, color);
}
"""

var _rd: RenderingDevice
var _shader: RID
var _pipeline: RID

func _init() -> void:
	effect_callback_type = CompositorEffect.EFFECT_CALLBACK_TYPE_POST_TRANSPARENT
	_rd = RenderingServer.get_rendering_device()
	RenderingServer.call_on_render_thread(_initialize_compute)

func _notification(what: int) -> void:
	if what == NOTIFICATION_PREDELETE and _shader.is_valid():
		_rd.free_rid(_shader)

func _initialize_compute() -> void:
	var source: RDShaderSource = RDShaderSource.new()
	source.language = RenderingDevice.SHADER_LANGUAGE_GLSL
	source.source_compute = SHADER_SOURCE
	var spirv: RDShaderSPIRV = _rd.shader_compile_spirv_from_source(source)
	if spirv.compile_error_compute != "":
		push_error(spirv.compile_error_compute)
		return
	_shader = _rd.shader_create_from_spirv(spirv)
	_pipeline = _rd.compute_pipeline_create(_shader)

func _render_callback(_effect_callback_type: int, render_data: RenderData) -> void:
	if _rd == null or not _pipeline.is_valid():
		return
	var buffers: RenderSceneBuffersRD = render_data.get_render_scene_buffers() as RenderSceneBuffersRD
	if buffers == null:
		return
	var size: Vector2i = buffers.get_internal_size()
	var push_constant: PackedFloat32Array = PackedFloat32Array([size.x, size.y, 0.0, 0.0])
	var groups: Vector2i = Vector2i(ceili(size.x / 8.0), ceili(size.y / 8.0))
	for view: int in buffers.get_view_count():
		var uniform: RDUniform = RDUniform.new()
		uniform.uniform_type = RenderingDevice.UNIFORM_TYPE_IMAGE
		uniform.binding = 0
		uniform.add_id(buffers.get_color_layer(view))
		var uniform_set: RID = UniformSetCacheRD.get_cache(_shader, 0, [uniform])
		var compute_list: int = _rd.compute_list_begin()
		_rd.compute_list_bind_compute_pipeline(compute_list, _pipeline)
		_rd.compute_list_bind_uniform_set(compute_list, uniform_set, 0)
		_rd.compute_list_set_push_constant(compute_list, push_constant.to_byte_array(), push_constant.size() * 4)
		_rd.compute_list_dispatch(compute_list, groups.x, groups.y, 1)
		_rd.compute_list_end()
```

使用：在 `WorldEnvironment` 或 `Camera3D` 上新建 `Compositor` 资源，往 `compositor_effects` 里加这个 `CompositorEffect`。放在相机上只影响该相机的视口。

- 类参考标为实验性，接口可能随版本变
- 回调在渲染线程，不能碰场景树，初始化用 `RenderingServer.call_on_render_thread()`，编辑器里改 shader 文本要加互斥锁
- 开 `needs_motion_vectors` `needs_normal_roughness`（仅 Forward+）`access_resolved_color` `access_resolved_depth` 申请额外缓冲
- 本页示例只验证了 GDScript 能解析，没有在 Vulkan 上运行。官方示例项目 `compute/post_shader` 可对照
- 仅 Mobile 与 Forward+，Compatibility 里需要改走第 3 或第 4 级

## 低分辨率渲染

像素风的低分辨率 3D：`SubViewport` 设小尺寸，用 `SubViewportContainer` 或 `TextureRect` 放大，过滤选 Nearest。只想整体降分辨率，用根视口的 `scaling_3d_mode` 与 `scaling_3d_scale`，不需要 `SubViewport`。

## 参考

- https://docs.godotengine.org/en/stable/tutorials/3d/environment_and_post_processing.html
- https://docs.godotengine.org/en/stable/tutorials/shaders/custom_postprocessing.html
- https://docs.godotengine.org/en/stable/tutorials/shaders/advanced_postprocessing.html
- https://docs.godotengine.org/en/stable/tutorials/rendering/compositor.html
