# 渲染提交与动画

同样画面少花 CPU 和带宽的做法。先看引擎已经替你做了什么，免得重复造；再看几处要自己写的：动态网格局部更新、共用蒙皮、`custom_aabb`、2D 断批。着色器写法去 godot-shaders-vfx，LOD 与剔除去 godot-3d。

## 引擎已经做了

| 做了什么 | 条件 |
|---|---|
| 3D 表面绘制数据缓存，只在网格、材质、MultiMesh、骨骼数据变化时重建 | Forward+ |
| 排序键相同的连续实例自动合成一次实例化绘制 | Forward+，蒙皮网格与 MultiMesh 不参与，Mobile 与 Compatibility 没有 |
| `instance_set_transform` 变换相同直接返回，不同只更新包围盒 | 所有渲染器 |
| `set_instance_shader_parameter` 不打断合批，不重建依赖 | 所有渲染器 |
| GPU 蒙皮，姿态没变就不重新蒙皮 | RD 用 compute，Compatibility 用 transform feedback |
| 点光与聚光的阴影只在灯移动、或范围内投影物移动增删时重画 | 方向光每帧重画 |
| 动画轨道路径解析一次进缓存，每帧按索引写 | `AnimationMixer` |
| 一帧里多次改同一节点的变换，物理与渲染通知合并成一次 | 场景树统一刷新 |

所以几百个相同的静态 `MeshInstance3D` 在 Forward+ 下绘制调用不一定多，瓶颈多在节点本身和剔除。先看 Monitors 的绘制调用数再决定是否换 `MultiMesh`。

点光或聚光范围内只要有一个投影物在动，整盏灯的阴影就重画，没有 UE 那样的静态层与动态层分开缓存。动个不停的小物件不需要阴影时关它的 `cast_shadow`。`Light3D.shadow_caster_mask` 4.4+ 只排除本来就看不到阴影的物体，否则画面会变。

## 动态网格：预分配加局部更新

每帧 `clear_surfaces()` 再 `add_surface_from_arrays()` 会释放并新建 GPU 缓冲，在 CPU 上打包顶点、遍历算包围盒，并通知所有用到这个网格的实例重建依赖，资源自己还发 `changed`。`ImmediateMesh` 底层也是清空再新建，代价相同。

每帧形状都变的网格（Spine 与其他 2D 骨骼动画、拖尾、绳子、程序化水面），一次分配最大容量，之后只写变化的区域：

<!-- check: extends MeshInstance3D -->
```gdscript
const MAX_VERTS := 3000
const VERTEX_BYTES := 12
var _mesh := ArrayMesh.new()
var _uploaded: int = 0

func _ready() -> void:
	var verts := PackedVector3Array()
	verts.resize(MAX_VERTS)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	_mesh.custom_aabb = AABB(Vector3(-2.0, 0.0, -2.0), Vector3(4.0, 4.0, 4.0))
	mesh = _mesh

func upload(points: PackedVector3Array) -> void:
	var count := mini(points.size(), MAX_VERTS)
	_mesh.surface_update_vertex_region(0, 0, points.slice(0, count).to_byte_array())
	if count < _uploaded:
		var zeros := PackedByteArray()
		zeros.resize((_uploaded - count) * VERTEX_BYTES)
		_mesh.surface_update_vertex_region(0, count * VERTEX_BYTES, zeros)
	_uploaded = count
```

- 局部更新只是一次缓冲写入，不发依赖通知。缓冲不能变大，越界报错，所以按最大顶点数分配
- 用不到的顶点清零，退化成面积为 0 的三角形，不画
- 顶点缓冲先连续放全部位置，法线与切线在后面另一段。只写位置时偏移从 0 开始，每顶点 12 字节，`ARRAY_FLAG_USE_2D_VERTICES` 时 8 字节。用 `RenderingServer.mesh_surface_get_format_vertex_stride()` 确认
- UV 与颜色在属性缓冲，变了才用 `surface_update_attribute_region()` 写，步长用 `mesh_surface_get_format_attribute_stride()` 算。不要的法线就别带，带了每帧都要写
- 局部更新不重算包围盒，必须设 `custom_aabb`，给够大，否则会被错误剔除
- 索引会变时，按最大索引数分配，用 `RenderingServer.mesh_surface_update_index_region()` 4.5+ 写，多余的索引全指向 0 号顶点。`ArrayMesh` 没有这个方法，用 `_mesh.get_rid()` 调服务器
- `ARRAY_FLAG_USE_DYNAMIC_UPDATE` 只在 Compatibility 渲染器有用，Vulkan 下无效
- `ARRAY_FLAG_COMPRESS_ATTRIBUTES` 把位置压成 16 位，会降精度，动态网格不用
- 顶点计算本身可以在 `WorkerThreadPool` 里按块并行，上传留在主线程，各个网格依次调

C# 里复用一个托管数组，写好后按字节视图传进去，每帧没有托管分配，只有一次原生拷贝。引擎需是单精度构建：

```csharp
using System;
using System.Runtime.InteropServices;
using Godot;

public partial class DynamicMesh : MeshInstance3D
{
    private const int MaxVerts = 3000;
    private readonly ArrayMesh _mesh = new();
    private readonly Vector3[] _positions = new Vector3[MaxVerts];
    private int _uploaded;

    public Span<Vector3> Positions => _positions;

    public override void _Ready()
    {
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = new Vector3[MaxVerts];
        _mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        _mesh.CustomAabb = new Aabb(new Vector3(-2f, 0f, -2f), new Vector3(4f, 4f, 4f));
        Mesh = _mesh;
    }

    public void Upload(int count)
    {
        int dirty = Math.Max(count, _uploaded);
        Array.Clear(_positions, count, dirty - count);
        _mesh.SurfaceUpdateVertexRegion(0, 0, MemoryMarshal.AsBytes(_positions.AsSpan(0, dirty)));
        _uploaded = count;
    }
}
```

- 4.7.2 的 C# 绑定给 Packed 数组参数生成了 ReadOnlySpan 重载，省掉托管侧分配，原生侧照样拷贝一次。老版本没有就复用一个 `byte[]`，用 `MemoryMarshal.Cast<byte, Vector3>` 写进去
- 不要每帧新建 `Godot.Collections.Array` 再重建表面

## 多个网格共用一套骨骼

UE 的 Leader Pose 让模块化角色的多个网格共用一次姿态计算。Godot 里多个 `MeshInstance3D` 的 `skeleton` 指向同一个 `Skeleton3D`，姿态只算一次。

- 还要共用同一个 `Skin` 资源，骨骼矩阵才只上传一份。没设 `skin` 的网格会各自从静止姿态建一个 Skin，各自逐骨骼上传
- 导入的 glTF 同一套蒙皮的网格通常已共用。代码里换装拼装时显式赋同一个 `skin`
- 不同骨架之间复制姿态用 `RetargetModifier3D` 4.4+

## 蒙皮网格的包围盒

蒙皮网格每次骨骼更新都按骨骼重算包围盒。设 `GeometryInstance3D.custom_aabb` 跳过这一步，给的盒子要包住所有动作的最大范围。数量多的蒙皮角色和每帧自己生成的网格都适用。

## 2D 合批

2D 渲染器把相邻、状态相同的绘制自动合成一批。下面这些会断批：

- 纹理不同，或同一纹理的 filter、repeat 不同
- 材质不同。每个节点 `duplicate()` 一份材质就是各不相同，用 `CanvasItem.set_instance_shader_parameter()` 4.4+ 加 `instance uniform` 代替
- 裁剪区域不同，如 `clip_children` 与 `clip_contents`
- 受光与不受光交替
- 绘制命令类型交替。`Polygon2D`、`MeshInstance2D`、`MultiMeshInstance2D`、粒子各自单独成批

灯光数据按实例传，不断批。精灵用图集、同类节点在树里放在一起、共用材质，批次就少。单批大小由 `rendering/2d/batching/item_buffer_size` 定，默认 16384。

## 动画放进子线程组

UE 的骨骼网格把各角色的动画评估分到工作线程，最后在游戏线程收结果。Godot 里把角色根节点的 `process_thread_group` 设成 `PROCESS_THREAD_GROUP_SUB_THREAD`，组内的 `AnimationPlayer`、`AnimationTree`、`Skeleton3D` 在工作线程里推进。

- `AnimationMixer`、`Skeleton3D`、`MeshInstance3D` 必须在同一个线程组里
- 属性轨道写到组外节点会报线程错误。方法轨道走延迟调用，信号回调在工作线程里执行，回调里只碰本组节点
- 角色的移动仍要在主线程，见 [crowd-characters.md](crowd-characters.md)。动画和移动分开挂：移动体留在主线程组，视觉子树单独设子线程组

## 顶点动画贴图

UE 的 AnimToTexture 把骨骼动画烘成贴图，让大量同网格角色用实例化绘制播动画。Godot 没有内置烘焙器：离线把每帧顶点位置写进 `Image`，shader 里用 `VERTEX_ID` 和 `INSTANCE_CUSTOM` 中的帧号 `texelFetch`，配合 `MultiMesh`。烘焙帧率低于渲染帧率就是降质，按渲染帧率烘或在两帧间插值。
