# shader 配方

每段都在 Compatibility 渲染器下编译通过。含 `hint_screen_texture` `hint_depth_texture` 的 Forward+ 分支按文档写，未在本地运行。

## 3D 受击闪白

```glsl
shader_type spatial;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
instance uniform float flash : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	ALBEDO = texture(albedo_tex, UV).rgb;
	EMISSION = vec3(flash) * 2.0;
}
```

```gdscript
extends MeshInstance3D

var _tween: Tween

func hit() -> void:
	if _tween != null:
		_tween.kill()
	set_instance_shader_parameter(&"flash", 1.0)
	_tween = create_tween()
	_tween.tween_property(self, "instance_shader_parameters/flash", 0.0, 0.2)
```

不想写 shader 时，给 `StandardMaterial3D` 开 `emission_enabled`，再 `tween_property` 它的 `emission_energy_multiplier`。但材质被多个实例共享时会一起亮，要复制材质或开 `resource_local_to_scene`。

## 溶解

```glsl
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D albedo_tex : source_color;
uniform sampler2D noise_tex : hint_default_white;
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform float edge_width : hint_range(0.0, 0.2) = 0.05;
uniform vec3 edge_color : source_color = vec3(1.0, 0.5, 0.1);

void fragment() {
	float n = texture(noise_tex, UV).r;
	if (n < progress) {
		discard;
	}
	float edge = smoothstep(progress, progress + edge_width, n);
	ALBEDO = mix(edge_color, texture(albedo_tex, UV).rgb, edge);
	EMISSION = edge_color * (1.0 - edge) * 3.0;
}
```

噪声贴图用 `NoiseTexture2D` 配 `FastNoiseLite`，不用手写。`progress` 用 `Tween` 从 0 到 1。多个物体各自进度时用 `instance uniform`。

## 2D 描边

```glsl
shader_type canvas_item;

uniform vec4 outline_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float width : hint_range(0.0, 8.0) = 1.0;

void fragment() {
	vec2 step_uv = TEXTURE_PIXEL_SIZE * width;
	float a = texture(TEXTURE, UV + vec2(step_uv.x, 0.0)).a;
	a = max(a, texture(TEXTURE, UV + vec2(-step_uv.x, 0.0)).a);
	a = max(a, texture(TEXTURE, UV + vec2(0.0, step_uv.y)).a);
	a = max(a, texture(TEXTURE, UV + vec2(0.0, -step_uv.y)).a);
	vec4 base = texture(TEXTURE, UV);
	COLOR = mix(vec4(outline_color.rgb, a * outline_color.a), base, base.a);
}
```

- 描边画在纹理矩形之外的像素被裁掉，图集或精灵边缘要留够透明像素
- 多个子节点合成的角色，把它们放进 `CanvasGroup`，材质挂在 `CanvasGroup` 上，描边是整体轮廓。`CanvasGroup.fit_margin` 为描边留出空间

## 屏幕背景模糊

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear_mipmap;
uniform float blur : hint_range(0.0, 5.0) = 2.0;

void fragment() {
	COLOR = textureLod(screen_texture, SCREEN_UV, blur);
}
```

挂在铺满的 `ColorRect` 上，放在暂停菜单底部。节点只覆盖局部时只模糊该区域。

## 全屏亮度对比度饱和度

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform float brightness = 1.0;
uniform float contrast = 1.0;
uniform float saturation = 1.0;

void fragment() {
	vec3 c = textureLod(screen_texture, SCREEN_UV, 0.0).rgb;
	c = mix(vec3(0.0), c, brightness);
	c = mix(vec3(0.5), c, contrast);
	c = mix(vec3(dot(vec3(1.0), c) * 0.33333), c, saturation);
	COLOR.rgb = c;
}
```

这三项 `Environment` 里有 `adjustment_brightness` `adjustment_contrast` `adjustment_saturation`，先用那个。

## 深度淡出（水岸 软粒子）

```glsl
shader_type spatial;
render_mode unshaded, depth_draw_never;

uniform sampler2D depth_texture : hint_depth_texture, repeat_disable, filter_nearest;
uniform vec4 tint : source_color = vec4(0.2, 0.6, 1.0, 1.0);
uniform float fade_distance = 0.5;

void fragment() {
	float depth = texture(depth_texture, SCREEN_UV).r;
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	vec3 ndc = vec3(SCREEN_UV, depth) * 2.0 - 1.0;
#else
	vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, depth);
#endif
	vec4 view = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
	view.xyz /= view.w;
	float gap = -view.z + VERTEX.z;
	ALBEDO = tint.rgb;
	ALPHA = clamp(gap / fade_distance, 0.0, 1.0) * tint.a;
}
```

`gap` 是背后场景与本表面在相机前方向的距离差。粒子软边直接开 `BaseMaterial3D` 的 `proximity_fade_enabled`，不用写这个。

## 3D 全屏四边形与深度雾

```glsl
shader_type spatial;
render_mode unshaded, fog_disabled;

uniform sampler2D depth_texture : hint_depth_texture, repeat_disable, filter_nearest;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform vec3 fog_color : source_color = vec3(0.6, 0.7, 0.8);
uniform float fog_density = 0.03;

void vertex() {
	POSITION = vec4(VERTEX.xy, 1.0, 1.0);
}

void fragment() {
	float depth = texture(depth_texture, SCREEN_UV).x;
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	vec3 ndc = vec3(SCREEN_UV, depth) * 2.0 - 1.0;
#else
	vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, depth);
#endif
	vec4 view = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
	view.xyz /= view.w;
	float dist = length(view.xyz);
	vec3 scene = textureLod(screen_texture, SCREEN_UV, 0.0).rgb;
	ALBEDO = mix(scene, fog_color, 1.0 - exp(-dist * fog_density));
}
```

节点设置：`MeshInstance3D` 的网格用 `QuadMesh`，`size` 为 2 乘 2，开 `flip_faces`，作为相机的子节点，或把 `extra_cull_margin` 设到最大。顶点着色器绕过变换直接写裁剪空间，CPU 看不见这点，所以会被视锥剔除。这种雾只是示例，真要雾先用 `Environment` 的 fog 与 `FogVolume`。

## 风摇 global uniform

```glsl
shader_type spatial;

global uniform float wind_strength;
uniform float sway_height = 1.0;

void vertex() {
	float h = clamp(VERTEX.y / sway_height, 0.0, 1.0);
	VERTEX.x += sin(TIME * 2.0 + NODE_POSITION_WORLD.x) * wind_strength * h * h;
}
```

先在项目设置 Shader Globals 页创建 `wind_strength`，类型 float，对应 `project.godot` 的 `shader_globals`：

```ini
[shader_globals]

wind_strength={
"type": "float",
"value": 0.5
}
```

运行时 `RenderingServer.global_shader_parameter_set(&"wind_strength", 1.2)`，改动立刻影响所有用到它的 shader。在 autoload 里记下数值，不要回读。

## 灰度与 include

```glsl
float luma(vec3 c) {
	return dot(c, vec3(0.299, 0.587, 0.114));
}
```

保存为 `res://shaders/lib.gdshaderinc`，包含文件里一般没有 `shader_type`：

```glsl
shader_type canvas_item;

#include "res://shaders/lib.gdshaderinc"

void fragment() {
	COLOR.rgb = luma(COLOR.rgb) * vec3(1.0);
}
```

## 在节点上挂 ShaderMaterial

```gdscript
extends Sprite2D

@export var flash_shader: Shader

func _ready() -> void:
	var mat: ShaderMaterial = ShaderMaterial.new()
	mat.shader = flash_shader
	material = mat
	mat.set_shader_parameter(&"flash_color", Color.WHITE)
```

场景里已有的实例共享材质资源，运行时改参数会影响全部。每个实例要独立状态时打开材质的 `resource_local_to_scene`，或用 `instance uniform`。

## 参考

- https://docs.godotengine.org/en/stable/tutorials/shaders/screen-reading_shaders.html
- https://docs.godotengine.org/en/stable/tutorials/shaders/advanced_postprocessing.html
- https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/shading_language.html
