---
name: godot-shaders-vfx
description: 做受击闪白 受伤变白 命中闪烁 溶解 描边，或从 GDScript 与 C# 改 .gdshader 的 shader 参数 SetInstanceShaderParameter set_shader_parameter 时先用，多个敌人共用一份材质各自闪白也归这里。先用内置材质 StandardMaterial3D CanvasItemMaterial 再写 shader 的判断, shader_type 与 render_mode, uniform instance uniform global uniform 的选择, hint_screen_texture hint_depth_texture 屏幕与深度纹理, VisualShader 何时用, shader include gdshaderinc, GPUParticles2D GPUParticles3D 与 CPUParticles 选择, ParticleProcessMaterial 子发射器 拖尾 碰撞, 后处理顺序 Environment glow tonemap fog 再 CompositorEffect 再全屏 shader, 2D glow 与 HDR 2D, StringName 缓存, local_to_scene 材质共享问题. Use when writing shaders, hit flash, tuning materials, building particle effects or post-processing.
---

# Godot 着色器与特效

先判断内置功能够不够，不够再写 shader。管 shader 语言用法，材质选择，粒子，后处理，屏幕与深度采样。3D 光照 GI 阴影环境选型转 `godot-3d`。Tween 与动画转 `godot-animation`。C# 通用规则转 `godot-csharp`。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 边缘光 自发光 清漆 次表面 折射 | `StandardMaterial3D` 的 `rim_enabled` `emission_enabled` `clearcoat_enabled` `subsurf_scatter_enabled` `refraction_enabled` | 同功能的 spatial shader |
| 公告牌 近距离淡出 贴地软边 | `billboard_mode` `distance_fade_mode` `proximity_fade_enabled` | 顶点着色器转向 深度比较 |
| 三平面贴图 顶点色 高度视差 | `uv1_triplanar` `vertex_color_use_as_albedo` `heightmap_enabled` | 手写采样 |
| 3D 描边 | `next_pass` 材质开 `grow`，`cull_mode` 设为剔除正面 | 后处理边缘检测 |
| 2D 加色 减色 乘色 | `CanvasItemMaterial.blend_mode` | `canvas_item` shader 里的 `blend_add` |
| 2D 不受光 只受光 | `CanvasItemMaterial.light_mode` | shader 里的 `unshaded` `light_only` |
| 整体着色与淡出 | `modulate` `self_modulate` | 为单个颜色写 shader |
| 2D 灯光与环境色 | `PointLight2D` `CanvasModulate` | 多个 `SubViewport` 模拟光照 |
| 泛光 色调映射 亮度对比度 雾 景深 | `Environment` 与 `CameraAttributes` | `SubViewport` 链堆 bloom 与模糊 |
| 粒子运动 颜色曲线 碰撞 子发射器 | `GPUParticles3D` 加 `ParticleProcessMaterial` | 脚本逐帧移动一堆节点 |
| 子弹拖尾 刀光 | 粒子拖尾 `RibbonTrailMesh` 或 `Line2D` | 手拼网格 |
| 弹孔 污渍 假阴影 | `Decal` | 运行时生成网格 |
| 多个精灵合成后加描边与特效 | `CanvasGroup` 加材质 | 每个精灵各写一份 |
| 屏幕模糊 菜单背景 | `hint_screen_texture` 配 `textureLod`，3D 场景也可用 `Environment` 的 glow 模糊 | 额外相机加 `SubViewport` |
| 动态噪声 渐变 曲线贴图 | `NoiseTexture2D` `GradientTexture1D` `CurveTexture` 传给 uniform | 在脚本里逐像素生成 |
| 在 GPU 上往贴图里画 涂抹 轨迹图 4.7+ | `DrawableTexture2D` 的 `blit_rect()`，可配 `texture_blit` shader，类参考标为实验性 | 每帧 `Image.set_pixel` 再更新 `ImageTexture` |
| 天空 全景背景 | `Environment` 的 `sky` 配 `ProceduralSkyMaterial` `PhysicalSkyMaterial` `PanoramaSkyMaterial` | 包住场景的大球加贴图 |
| 受击闪白 | shader uniform 加 `Tween` | `modulate` 超过 1 |

## 做法

### 什么时候写 shader

内置属性组合不出来才写：逐像素动态效果（溶解 描边 扭曲），读屏幕或深度，顶点形变（风摇 水波），程序化纹理，自定义混合。只是改颜色 透明 亮度，先用 `modulate` 与材质属性。

### shader 类型

| `shader_type` | 用于 | 入口 | 常用 `render_mode` |
|---|---|---|---|
| `spatial` | 3D 网格 | `vertex` `fragment` `light` | `unshaded` `cull_disabled` `blend_add` `depth_draw_never` `fog_disabled` |
| `canvas_item` | 2D 节点与 UI | `vertex` `fragment` `light` | `blend_add` `unshaded` `light_only` |
| `particles` | GPU 粒子的运动 | `start` `process` | `keep_data` `disable_velocity` |
| `sky` | 天空 | `sky` | |
| `fog` | `FogVolume` 体积雾 仅 Forward+ | `fog` | |
| `texture_blit` 4.7+ | `DrawableTexture2D.blit_rect()` 的绘制规则 | `blit` | `blend_disabled`（默认） `blend_mix` `blend_add` `blend_sub` `blend_mul` |

`spatial` 另有 `blend_mul` `diffuse_toon` `specular_disabled` `shadows_disabled` `vertex_lighting` `ambient_light_disabled` 等，完整表见 [references/shader-language.md](references/shader-language.md)。`BaseMaterial3D.stencil_mode` 与 stencil 相关 render_mode 是 4.5+。

### 三种参数

| 种类 | 声明 | 作用域 | 设置方式 |
|---|---|---|---|
| uniform | `uniform float x;` | 每个 `ShaderMaterial` | `material.set_shader_parameter(&"x", v)` |
| instance uniform | `instance uniform float x;` | 每个节点 | `node.set_instance_shader_parameter(&"x", v)` |
| global uniform | `global uniform float x;` | 整个项目 | `RenderingServer.global_shader_parameter_set(&"x", v)` |

- 多个节点共用一个材质但各自状态不同（闪白 颜色变体 溶解进度）：用 instance uniform，不复制材质
- instance uniform 只用于 `spatial` 与 `canvas_item` shader，`particles` `sky` `fog` 不支持。3D 在 `GeometryInstance3D` 上设置，`CanvasItem.set_instance_shader_parameter()` 是 4.4+
- instance uniform 不支持纹理与数组，每个 shader 最多 16 个，同一网格多个材质时靠 `instance_index` 提示避免冲突
- global uniform 必须先在项目设置的 Shader Globals 页创建（写入 `shader_globals/<名字>`），否则编辑器里保存 shader 时编译失败，运行时只有警告且取值不对。适合风力 昼夜 玩家位置，设置很便宜，游戏里读不了：`global_shader_parameter_get()` 在编辑器之外报错并返回 `null`，数值自己记一份
- 颜色 uniform 加 `source_color`，贴图 uniform 作反照率时也加

### 命中闪白

```glsl
shader_type canvas_item;

instance uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0);

void fragment() {
	COLOR.rgb = mix(COLOR.rgb, flash_color.rgb, flash);
}
```

```gdscript
extends Sprite2D

var _tween: Tween

func hit() -> void:
	if _tween != null:
		_tween.kill()
	set_instance_shader_parameter(&"flash", 1.0)
	_tween = create_tween()
	_tween.tween_property(self, "instance_shader_parameters/flash", 0.0, 0.15)
```

`modulate` 是乘法，黑色和暗部乘多大都到不了白，且不开 HDR 2D 时超过 1 的值会被截断。闪白要用 `mix` 到目标色。材质上有普通 uniform 时，可 `tween_property(material, "shader_parameter/flash", ...)`，前提是先 `set_shader_parameter()` 写过初值。同一份材质被多个实例共享会一起闪，需要把材质的 `resource_local_to_scene` 打开，或改用 instance uniform。

### 从 C# 设置

```csharp
using Godot;

public partial class HitFlash : Sprite2D
{
    private static readonly StringName s_flash = "flash";
    private static readonly NodePath s_flashPath = "instance_shader_parameters/flash";
    private Tween _tween;

    public void Play()
    {
        _tween?.Kill();
        SetInstanceShaderParameter(s_flash, 1.0f);
        _tween = CreateTween();
        _tween.TweenProperty(this, s_flashPath, 0.0f, 0.15);
    }
}
```

字符串字面量每次都会转成新的 `StringName` 或 `NodePath`。每帧调用的路径上缓存成 `static readonly`。

### 屏幕与深度纹理

```glsl
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear_mipmap;
uniform float blur : hint_range(0.0, 5.0) = 2.0;

void fragment() {
	COLOR = textureLod(screen_texture, SCREEN_UV, blur);
}
```

- 读模糊版本需要 `filter_*_mipmap` 且 LOD 大于 0，否则和 LOD 0 一样
- 2D 里第一个用到 `hint_screen_texture` 的节点触发整屏拷贝，后面的不再拷，重叠时靠 `BackBufferCopy` 节点分段
- 3D 里屏幕纹理在不透明物体之后、透明物体之前截取，透明物体看不到，用了屏幕纹理的材质自己被当作透明
- 深度纹理 `hint_depth_texture` 非线性，用 `INV_PROJECTION_MATRIX` 还原。Forward+ 与 Mobile 的 NDC 是 `vec3(SCREEN_UV * 2.0 - 1.0, depth)`，Compatibility 是 `vec3(SCREEN_UV, depth) * 2.0 - 1.0`，用 `#if CURRENT_RENDERER == RENDERER_COMPATIBILITY` 区分，4.4+
- `hint_normal_roughness_texture` 仅 Forward+
- 配方见 [references/shader-recipes.md](references/shader-recipes.md)

### 后处理顺序

按这个顺序选，前一级够用就停：

1. `Environment`：glow tonemap adjustments fog ssao 一类。放在 `WorldEnvironment`，每个场景树一个。画质项在项目设置
2. `CompositorEffect`（4.3+，仅 Forward+ 与 Mobile，类参考标为实验性）：要在 HDR 线性数据上、内置后处理之前插自己的计算，或需要运动矢量 法线粗糙度。跑在渲染线程
3. 全屏 shader：`CanvasLayer` 下 `ColorRect` 铺满，材质读 `hint_screen_texture`。读到的是已渲染好的帧，没有深度，所有渲染器可用
4. 3D 全屏四边形：要深度又不能用 `CompositorEffect` 时，`QuadMesh` 加顶点着色器 `POSITION = vec4(VERTEX.xy, 1.0, 1.0)`，并设大 `extra_cull_margin`，否则被视锥剔除

不要用一串平级 `SubViewport` 手搓 bloom，先开 `Environment.glow_enabled`。

### 2D 的 glow

`WorldEnvironment` 的 `Environment` 必须把 `background_mode` 设为 `Environment.BG_CANVAS`，否则 2D 内容不进环境效果。Compatibility 下实测：背景为 Clear Color 时没有 glow，改 Canvas 后出现。

```gdscript
extends Node2D

func _ready() -> void:
	var env: Environment = Environment.new()
	env.background_mode = Environment.BG_CANVAS
	env.background_canvas_max_layer = 0
	env.glow_enabled = true
	env.glow_hdr_threshold = 0.8
	var world_env: WorldEnvironment = WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)
```

- 没有 HDR 2D：2D 是 SDR，必须把 `glow_hdr_threshold` 调到 1.0 以下，不发光的物体与发光的物体靠亮度区分，控制力弱
- 有 HDR 2D（`rendering/viewport/hdr_2d`，仅 Forward+ 与 Mobile，启动时读取，运行时改根视口的 `use_hdr_2d`）：用 `modulate` 或 `self_modulate` 的强度超过 1 选择谁发光。副作用：2D 改在线性空间混合，半透明更显眼，字体变粗，canvas shader 的颜色采样器必须有 `source_color`
- UI 不要发光：放在 `CanvasLayer` 上，层号大于 `background_canvas_max_layer`
- `glow_bloom` 大于 0 会让整个画面变亮，不只是高亮区域
- Compatibility 的 glow 是简化实现，没有 `glow_blend_mode` `glow_levels/*` `glow_map`

### 粒子

| 需求 | 选择 |
|---|---|
| 默认 | `GPUParticles3D` `GPUParticles2D` |
| 低端设备 GPU 吃紧 少量粒子 | `CPUParticles3D` `CPUParticles2D`，功能比 GPU 版少，不再加新功能 |
| 多个绘制通道 拖尾 子发射器 吸引器 碰撞 湍流 | 只有 GPU 版 |
| 完全自定义运动 | `process_material` 换成 `shader_type particles` 的 `ShaderMaterial` |

- 材质：`process_material` 用 `ParticleProcessMaterial`，粒子外观用绘制通道网格上的材质，`BaseMaterial3D.billboard_mode` 选 `BILLBOARD_PARTICLES` 并设帧数可播放序列帧
- 子发射器：父节点 `sub_emitter` 指向子节点，父级材质的 `sub_emitter_mode` 选 `SUB_EMITTER_AT_END` `SUB_EMITTER_AT_COLLISION` 等（`SUB_EMITTER_AT_START` 是 4.4+）。子节点总数受它自己的 `amount` 限制
- 拖尾：`trail_enabled`，绘制通道用 `RibbonTrailMesh` 或 `TubeTrailMesh`，材质开 `use_particle_trails`。Compatibility 不支持
- 碰撞：3D 只与 `GPUParticlesCollision3D` 派生节点碰撞，2D 只与 `LightOccluder2D` 碰撞，都不与物理体碰撞
- 一次性特效：`one_shot` 加 `finished` 信号

```gdscript
extends GPUParticles3D

func _ready() -> void:
	one_shot = true
	finished.connect(queue_free)
	restart()
```

细节与吸引器 湍流 序列帧见 [references/particles.md](references/particles.md)。

### VisualShader

用于美术在图里试效果，预览直观。要预处理器 `#include` 或复杂逻辑就用文本 shader。VisualShader 工具栏的显示生成代码按钮能看到等价文本，资源检查器的 Convert to Shader 转成文本 shader，单向不可逆。

### 复用代码

`.gdshaderinc` 放函数库，用 `#include "res://shaders/lib.gdshaderinc"` 引入。只有 `.gdshaderinc` 能被包含，不能循环包含，深度最多 25。包含文件里一般不写 `shader_type`。

## 陷阱

- `COLOR = texture(TEXTURE, UV)` 丢掉 `modulate`。`fragment()` 里的 `COLOR` 本来就是纹理乘顶点色，直接改它
- 浮点 GDScript 参数是 64 位，shader 是 32 位。类型不对不报错，表现未定义，`hint_enum` 要传整数不传字符串
- 参数名要和 shader 完全一致，区分大小写
- `ShaderMaterial` 共享于场景的所有实例。给一个实例改参数会连带所有实例。用 instance uniform 或 `resource_local_to_scene`
- 不要每次受击 `duplicate()` 或 `new` 材质，会造成内存开销和材质管理混乱
- 没调用过 `set_shader_parameter()` 的 uniform 在 `ShaderMaterial` 上读出 `null`，shader 里的默认值不会回填。对它 `tween_property` 报 `does not exist`，tween 里没有 tweener，`await tween.finished` 永远不返回。先写初值再 tween，有无渲染都一样（实测 4.7.2 的 headless 与 Compatibility）
- `TIME` 3600 秒回绕（`rendering/limits/time/time_rollover_secs`），受 `Engine.time_scale` 影响，不受暂停影响
- 贴图当颜色必须 `source_color`，法线与数据贴图不要
- uniform 总大小有上限，桌面 65536 字节，手机 16384 字节。大数组打包进贴图
- `Environment.glow_enabled` 默认几乎看不见，调 `glow_hdr_threshold` 或 `glow_bloom`
- 全屏四边形 4.3 起深度反向，旧写法 `POSITION = vec4(VERTEX, 1.0)` 不再可用
- 在 `ColorRect` 上叠多个全屏 shader，顺序由 `CanvasLayer` 的 `layer` 决定，大的在上
- GPU 粒子在可见框外会整体消失，用编辑器 Generate Visibility Rect 或 AABB 工具，或设大 `visibility_aabb` `visibility_rect`
- 运行时改 `GPUParticles3D.amount` 会重启粒子，要连续调数量用 `amount_ratio`
- 一次性粒子再次播放用 `restart()`，只设 `emitting` 可能在内部还有粒子时无效。`restart()` 会清掉现有粒子，同一节点反复触发时等 `finished` 再调，否则画面里的粒子突然消失
- 被指定为子发射器的节点会停止自身发射，`emitting` 也改不回来，且不能自己做自己的子发射器
- Compatibility 渲染器不支持 `CompositorEffect` 粒子拖尾 粒子 SDF 碰撞 `emit_particle()`
- `CompositorEffect` 的回调在渲染线程，不要从那里碰场景树
- `DrawableTexture2D.setup()` 4.7+ 的第 4 个参数是 `color`，`use_mipmaps` 在第 5 位。官方教程示例 `setup(500, 500, DrawableTexture2D.DRAWABLE_FORMAT_RGBA8, false)` 在 4.7.2 报解析错误

## 参考

- [references/shader-language.md](references/shader-language.md) render_mode 表 内置变量 uniform 提示 类型对照 预处理
- [references/shader-recipes.md](references/shader-recipes.md) 溶解 描边 深度淡出 全屏雾 风摇 灰度 include
- [references/particles.md](references/particles.md) 粒子细节
- [references/post-processing.md](references/post-processing.md) Environment 项 glow CompositorEffect 全屏方案
- https://docs.godotengine.org/en/stable/tutorials/shaders/index.html
- https://docs.godotengine.org/en/stable/tutorials/3d/particles/index.html
- https://docs.godotengine.org/en/stable/tutorials/rendering/compositor.html
