# shader 语言速查

内容取自 4.7 的着色器参考页。写之前确认节点能用哪种 `shader_type`。

## spatial 的 render_mode

| 类别 | 值 |
|---|---|
| 混合 | `blend_mix`（默认） `blend_add` `blend_sub` `blend_mul` `blend_premul_alpha` |
| 深度写入 | `depth_draw_opaque`（默认） `depth_draw_always` `depth_draw_never` `depth_prepass_alpha` |
| 深度测试 | `depth_test_default` `depth_test_disabled` `depth_test_inverted` |
| 剔除 | `cull_back`（默认） `cull_front` `cull_disabled` |
| 漫反射 | `diffuse_burley`（默认） `diffuse_lambert` `diffuse_lambert_wrap` `diffuse_toon` |
| 高光 | `specular_schlick_ggx`（默认） `specular_toon` `specular_disabled` |
| 光照 | `unshaded` `vertex_lighting` `shadows_disabled` `ambient_light_disabled` `shadow_to_opacity` `fog_disabled` |
| 变换 | `skip_vertex_transform` `world_vertex_coords` |
| 其他 | `wireframe` `particle_trails` `sss_mode_skin` `alpha_to_coverage` `alpha_to_coverage_and_one` `debug_shadow_splits` |
| stencil 4.5+ | `read` `write` `write_if_depth_fail` `compare_always` 等 配合 `BaseMaterial3D.stencil_mode` |

- `fog_disabled` 给 `blend_add` 的粒子与特效用，避免被雾吃掉
- `unshaded` 只输出反照率，不算光照，也更便宜
- `ensure_correct_normals` 在文档里标为未实现
- 多个 `render_mode` 用逗号分隔写在同一行

## canvas_item 的 render_mode

`blend_mix`（默认） `blend_add` `blend_sub` `blend_mul` `blend_premul_alpha` `blend_disabled` `unshaded` `light_only` `skip_vertex_transform` `world_vertex_coords`

## particles 与 sky

| 类型 | render_mode |
|---|---|
| `particles` | `keep_data` 重启不清数据 `disable_force` 忽略吸引器 `disable_velocity` 忽略 `VELOCITY` `collision_use_scale` 碰撞时用粒子缩放 |
| `sky` | `use_half_res_pass` `use_quarter_res_pass` `disable_fog` |

粒子 shader 有 `start()` 与 `process()` 两个函数，数据在帧间保留，输出由使用该粒子的 spatial 或 canvas_item 材质绘制。只有 GPU 粒子节点能用，CPU 粒子节点只能换绘制用的材质。

## spatial 内置变量

| 变量 | 说明 |
|---|---|
| `VERTEX` | `vertex()` 里是模型空间可写，`fragment()` 里是视图空间只读 |
| `NORMAL` `TANGENT` `BINORMAL` | 同上 |
| `UV` `UV2` `COLOR` | 顶点输入 |
| `POSITION` | 写了就覆盖最终裁剪空间位置，全屏四边形用 |
| `Z_CLIP_SCALE` | 对应 `BaseMaterial3D.use_z_clip_scale`，4.5+ |
| `SCREEN_UV` `FRAGCOORD` `VIEWPORT_SIZE` | 屏幕坐标 |
| `VIEW` | 片元指向相机的单位向量 视图空间 |
| `MODEL_MATRIX` `VIEW_MATRIX` `INV_VIEW_MATRIX` `PROJECTION_MATRIX` `INV_PROJECTION_MATRIX` | 变换 |
| `NODE_POSITION_WORLD` `CAMERA_POSITION_WORLD` `CAMERA_DIRECTION_WORLD` | 节点与相机位置 |
| `INSTANCE_ID` `INSTANCE_CUSTOM` | 实例化，`INSTANCE_CUSTOM` 在 `MultiMesh` 与粒子里是逐实例数据 |
| `FRONT_FACING` | 是否正面 |
| `DEPTH` | 写了就自定义深度 |
| `ALBEDO` `ALPHA` `METALLIC` `ROUGHNESS` `SPECULAR` `EMISSION` `AO` `NORMAL_MAP` `RIM` `CLEARCOAT` `SSS_STRENGTH` | `fragment()` 的输出 |
| `ALPHA_SCISSOR_THRESHOLD` `ALPHA_HASH_SCALE` `ALPHA_ANTIALIASING_EDGE` | 透明裁剪 |
| `TIME` `PI` `TAU` `E` | 全局 |

## canvas_item 内置变量

| 变量 | 说明 |
|---|---|
| `COLOR` | `vertex()` 里是顶点色乘 `modulate` 乘 `self_modulate`，`fragment()` 里再乘默认 `TEXTURE`，也是最终输出 |
| `TEXTURE` `TEXTURE_PIXEL_SIZE` | 节点默认纹理，纹理像素大小的归一化值，描边与平移采样用 |
| `UV` `VERTEX` | |
| `SCREEN_UV` `SCREEN_PIXEL_SIZE` `FRAGCOORD` | 屏幕坐标 |
| `REGION_RECT` | 精灵区域 |
| `INSTANCE_CUSTOM` | 逐实例数据 |
| `NORMAL_MAP` `NORMAL_MAP_DEPTH` | 让 2D 精灵用 3D 法线贴图 |
| `LIGHT` 系列 | `light()` 里的 2D 灯数据 |
| `AT_LIGHT_PASS` | 恒为 false |
| `TIME` | 全局 |

只读顶点色 忽略纹理时，要在 `vertex()` 里存进 `varying` 再在 `fragment()` 里用。

## uniform 提示

| 类型 | 提示 | 说明 |
|---|---|---|
| vec3 vec4 | `source_color` | 颜色，编辑器用取色器，并做 sRGB 转线性 |
| int | `hint_enum("A", "B")` | 下拉，可写 `"A:30"` 指定值 |
| int float | `hint_range(min, max[, step])` | 范围 |
| sampler2D | `source_color` | 颜色贴图，Forward+ 与 Mobile 必须。2D 开 HDR 2D 时 canvas shader 也必须 |
| sampler2D | `hint_normal` | 法线贴图 |
| sampler2D | `hint_default_white` `hint_default_black` `hint_default_transparent` | 未指定时的默认 |
| sampler2D | `hint_anisotropy` | 流向图 |
| sampler2D | `hint_roughness_r` 等 | 导入时粗糙度限制 |
| sampler2D | `filter_nearest` `filter_linear` `filter_nearest_mipmap` `filter_linear_mipmap` 及 `_anisotropic` | 过滤 |
| sampler2D | `repeat_enable` `repeat_disable` | 重复 |
| sampler2D | `hint_screen_texture` | 屏幕纹理 |
| sampler2D | `hint_depth_texture` | 深度纹理 |
| sampler2D | `hint_normal_roughness_texture` | 法线与粗糙度 仅 Forward+ |
| 任意 | `no_storage` | 不存进材质资源，运行时设置的值用 |
| 任意 | `no_editor` | 不显示在检查器 |
| 任意 | `instance_index(n)` | instance uniform 的槽位 0 到 15 |

- 默认值写在提示之后：`uniform vec4 c : source_color = vec4(1.0);`
- 同一个屏幕类提示可以声明多个 uniform，换不同的过滤与重复
- 用 `group_uniforms 组名;` 开始分组，`group_uniforms;` 结束，`组名.子组名` 表示子组
- `source_color` 没写时贴图在 Forward+ 与 Mobile 里会显得发白

## GDScript 与 GLSL 类型

| GLSL | GDScript | 备注 |
|---|---|---|
| bool | bool | |
| int uint | int | 64 位转 32 位 |
| float | float | 64 位转 32 位 |
| ivec2 uvec2 | Vector2i | |
| vec2 | Vector2 | |
| vec3 | Vector3 Color | Color 取 rgb |
| vec4 | Vector4 Color Rect2 Plane Quaternion | Rect2 为 位置 x y 大小 x y |
| mat2 | Transform2D | |
| mat3 | Basis | |
| mat4 | Projection Transform3D | |
| sampler2D | Texture2D | |
| sampler2DArray | Texture2DArray | |
| sampler3D | Texture3D | |
| samplerCube | Cubemap | |
| samplerCubeArray | CubemapArray | Compatibility 不支持 |
| bvec2 bvec3 bvec4 | int | 位打包 最低位对应 x |

类型不匹配不报错，行为未定义。

## 限制

- 单个 shader 的 uniform 总大小：桌面常见 65536 字节，手机常见 16384 字节。vec2 与 vec3 按 vec4 补齐，标量不补，bool 按 int 补齐。大数组改存贴图
- 逐实例 uniform 每个 shader 最多 16 个
- `varying` 不能在自定义函数和 `light()` 里赋值
- Compatibility 的 GLSL 3.3 下不能用逐实例 uniform 直接索引采样器数组，改用 `switch` 选择
- Compatibility 的深度范围是 `[-1, 1]`，Forward+ 与 Mobile 是 `[0, 1]` 且反向 Z

## 预处理器

支持 `#define` `#undef` `#if` `#ifdef` `#ifndef` `#elif` `#else` `#endif` `#error` `#include` `#pragma`。`#if` 也能用 `defined()`。VisualShader 不支持预处理器。

```glsl
shader_type spatial;

#define USE_RIM
#include "res://shaders/lib.gdshaderinc"

#ifdef USE_RIM
const float RIM_POWER = 3.0;
#endif

void fragment() {
	ALBEDO = vec3(1.0);
}
```

- `#include` 路径可以是 `res://` 绝对路径或相对当前文件的路径，相对路径只在保存为文件的 shader 里可用
- 只能包含 `.gdshaderinc`，可以嵌套，禁止循环，深度最多 25
- 在文件顶部 `shader_type` 之后写 `#include`
- 4.4+ 内置宏 `CURRENT_RENDERER` 取 0 1 2，对应 `RENDERER_COMPATIBILITY` `RENDERER_MOBILE` `RENDERER_FORWARD_PLUS`
- `#pragma disable_preprocessor` 跳过预处理加快编译

## 编辑器里的辅助

- 文件菜单 Create Shader Include 新建包含文件，也可在文件系统里新建 `ShaderInclude` 资源
- VisualShader 工具栏的显示生成代码按钮看等价文本，资源下拉菜单的 Convert to Shader 转文本 shader，单向
- 项目设置 `debug/shader_language/warnings/unused_uniform` 一类开关控制警告

## 参考

- https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/shading_language.html
- https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/spatial_shader.html
- https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/canvas_item_shader.html
- https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/shader_preprocessor.html
