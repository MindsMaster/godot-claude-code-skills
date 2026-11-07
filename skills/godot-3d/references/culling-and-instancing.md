# LOD、剔除、实例化、贴花

自动 mesh LOD、visibility range 与 HLOD、遮挡剔除、MultiMesh、Decal。

## 选择

| 手段 | 解决 | 注意 |
|---|---|---|
| 自动 mesh LOD | 远处面数 | 导入时生成 对 `MeshInstance3D` `MultiMeshInstance3D` 粒子都有效 |
| `visibility_range_*` | 手做的多级模型 整组替换 距离淡出 | 按节点 AABB 中心的距离 |
| 遮挡剔除 | 室内被墙挡住的物体 | CPU 光栅化遮挡体 烘焙静态网格 |
| 视锥剔除 | 屏幕外 | 自动 `extra_cull_margin` 可放大 |
| `MultiMeshInstance3D` | 大量相同网格的绘制调用 | 整体一个剔除单位 |
| `VisibleOnScreenNotifier3D` `VisibleOnScreenEnabler3D` | 屏幕外的逻辑暂停 | 不是渲染剔除 |
| 灯的距离淡出 | 灯数量 | 见 rendering-lighting.md |

## 自动 mesh LOD

- glTF 与 `.blend` 默认生成
- OBJ 要把导入类型改为 Scene，重导入并重启编辑器
- `rendering/mesh_lod/lod_change/threshold_pixels` 默认 1 像素，调大切换更早
- 运行时改根视口的 `mesh_lod_threshold`，每个视口独立
- 单个对象调 `GeometryInstance3D.lod_bias`，大于 1 切换更晚
- `ReflectionProbe.mesh_lod_threshold` 对 Always 更新的探针有用
- 选级用 AABB 离相机最近的点
- `MultiMeshInstance3D` 与粒子的所有实例同一级
- GPU 粒子 LOD 不对时用 Generate AABB 设好可见框
- 蒙皮网格偶有渲染问题，导入设置里关该网格的 LOD
- 编辑器视口菜单 Disable Mesh LOD 可对比

## visibility range

可用于任何 `GeometryInstance3D`，包括 `Label3D` `Sprite3D` `AnimatedSprite3D` 粒子 CSG。

```gdscript
extends Node3D

@onready var _near: MeshInstance3D = $Near
@onready var _far: MeshInstance3D = $Far

func _ready() -> void:
	_near.visibility_range_end = 10.0
	_near.visibility_range_end_margin = 1.0
	_far.visibility_range_begin = 10.0
	_far.visibility_range_begin_margin = 1.0
```

```csharp
public partial class LodPair : Node3D
{
    public override void _Ready()
    {
        var near = GetNode<MeshInstance3D>("Near");
        var far = GetNode<MeshInstance3D>("Far");
        near.VisibilityRangeEnd = 10.0f;
        near.VisibilityRangeEndMargin = 1.0f;
        far.VisibilityRangeBegin = 10.0f;
        far.VisibilityRangeBeginMargin = 1.0f;
    }
}
```

- `visibility_range_begin` 与 `visibility_range_end` 默认 0，不做范围检查
- 自动 LOD 与 visibility range 可同时用在同一网格

| `visibility_range_fade_mode` | 行为 |
|---|---|
| Disabled | 滞回瞬间切换，最快 |
| Self | alpha 淡入淡出 |
| Dependencies | 配合 `Node3D.visibility_parent` 做 HLOD |

- 淡出时对象被强制透明渲染
- 淡出只在 margin 大于 0 时可见，且只在 Forward+ 有效
- Mobile 与 Compatibility 下等同 Disabled，且没有滞回

HLOD：

- 一组房子的合并大网格设 `visibility_range_begin`
- 每个房子的 `visibility_parent` 指向合并网格，不必再设 end
- `visibility_parent` 目标须是 `GeometryInstance3D`，不能指向子节点
- `visible` 为 false 的节点退出依赖树，子节点不再按它隐藏

## 遮挡剔除

1. 开 `rendering/occlusion_culling/use_occlusion_culling`，默认关，即时生效
2. 放 `OccluderInstance3D`，点 Bake Occluders
3. 动态物体放到其他可见层，并在 `bake_mask` 去掉那一层，重烘
4. 手摆遮挡体用 `QuadOccluder3D` `BoxOccluder3D` `SphereOccluder3D` `PolygonOccluder3D`
5. 过程化遮挡体用 `ArrayOccluder3D`

- 网页导出模板不支持；运行时也可设根视口 `use_occlusion_culling`
- 只烘 `MeshInstance3D`，不含 `MultiMeshInstance3D`、粒子、CSG
- 被遮挡物的 AABB 须被完全遮住才剔除
- 大遮挡体如墙更有效，小物体更容易被剔除
- 室内多小房间、室外金字塔形地形效果好
- 几乎没有遮挡机会的场景反而多花 CPU
- 不在游戏中移动 `OccluderInstance3D` 或其父级，会重建 BVH
- 门开启时隐藏遮挡体，比移动便宜
- 遮挡体越简单越好，调大 `bake_simplification_distance` 后重烘，过大误剔除
- CPU 负载：`rendering/occlusion_culling/bvh_build_quality` 与 `occlusion_rays_per_thread`
- Mobile 没有深度预通道，遮挡剔除收益最大
- `GeometryInstance3D.ignore_occlusion_culling` 让个别对象跳过

## MultiMesh

```gdscript
extends MultiMeshInstance3D

func build(mesh_to_draw: Mesh, count: int, area: float) -> void:
	var mm: MultiMesh = MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = mesh_to_draw
	mm.instance_count = count
	for i: int in count:
		var origin: Vector3 = Vector3(randf_range(-area, area), 0.0, randf_range(-area, area))
		mm.set_instance_transform(i, Transform3D(Basis.from_euler(Vector3(0.0, randf() * TAU, 0.0)), origin))
		mm.set_instance_custom_data(i, Color(randf(), 0.0, 0.0, 0.0))
	mm.custom_aabb = AABB(Vector3(-area, -1.0, -area), Vector3(area * 2.0, 10.0, area * 2.0))
	multimesh = mm
```

```csharp
public partial class Scatter : MultiMeshInstance3D
{
    public void Build(Mesh meshToDraw, int count, float area)
    {
        var mm = new MultiMesh();
        mm.TransformFormat = MultiMesh.TransformFormatEnum.Transform3D;
        mm.UseCustomData = true;
        mm.Mesh = meshToDraw;
        mm.InstanceCount = count;
        for (int i = 0; i < count; i++)
        {
            var origin = new Vector3((float)GD.RandRange(-area, area), 0.0f, (float)GD.RandRange(-area, area));
            mm.SetInstanceTransform(i, new Transform3D(Basis.FromEuler(new Vector3(0.0f, GD.Randf() * Mathf.Tau, 0.0f)), origin));
            mm.SetInstanceCustomData(i, new Color(GD.Randf(), 0.0f, 0.0f, 0.0f));
        }
        mm.CustomAabb = new Aabb(new Vector3(-area, -1.0f, -area), new Vector3(area * 2.0f, 10.0f, area * 2.0f));
        Multimesh = mm;
    }
}
```

- `use_colors` `use_custom_data` `transform_format` 先于 `instance_count` 设
- 或先把 `instance_count` 设回 0；大于 0 时改它们报错且不生效
- 设 `instance_count` 会清空并重设缓冲
- 改数量用 `visible_instance_count`，默认 -1 全画
- 大量更新用 `buffer` 一次写入，比逐个 `set_instance_transform()` 快
- 逐实例颜色要材质读顶点色，`StandardMaterial3D` 开 `vertex_color_use_as_albedo`
- 自写 shader 读 `COLOR` 与 `INSTANCE_CUSTOM`
- `instance uniform` 对 `MultiMeshInstance3D` 是整体一份
- 一个 `MultiMesh` 是一个剔除对象，实例相距远时拆成多个节点
- 实例没有物理碰撞，要碰撞另放静态体
- 混合形状被忽略
- 共享对象的光源数量有上限，用尽后其余实例不受光
- MultiMesh 菜单的 Populate surface 按目标表面撒点

## Decal

```gdscript
extends Node3D

func spawn(texture: Texture2D, point: Vector3, normal: Vector3) -> void:
	var decal: Decal = Decal.new()
	decal.texture_albedo = texture
	decal.size = Vector3(0.6, 0.4, 0.6)
	decal.normal_fade = 0.5
	decal.distance_fade_enabled = true
	add_child(decal)
	var side: Vector3 = normal.cross(Vector3.FORWARD if absf(normal.dot(Vector3.FORWARD)) < 0.9 else Vector3.RIGHT).normalized()
	decal.global_position = point
	decal.global_basis = Basis(side, normal, side.cross(normal))
	decal.rotate_object_local(Vector3.UP, randf() * TAU)
	var tween: Tween = create_tween()
	tween.tween_interval(8.0)
	tween.tween_property(decal, "modulate:a", 0.0, 1.0)
	tween.tween_callback(decal.queue_free)
```

```csharp
public partial class DecalSpawner : Node3D
{
    public void Spawn(Texture2D texture, Vector3 point, Vector3 normal)
    {
        var decal = new Decal
        {
            TextureAlbedo = texture,
            Size = new Vector3(0.6f, 0.4f, 0.6f),
            NormalFade = 0.5f,
            DistanceFadeEnabled = true,
        };
        AddChild(decal);
        Vector3 reference = Mathf.Abs(normal.Dot(Vector3.Forward)) < 0.9f ? Vector3.Forward : Vector3.Right;
        Vector3 side = normal.Cross(reference).Normalized();
        decal.GlobalPosition = point;
        decal.GlobalBasis = new Basis(side, normal, side.Cross(normal));
        decal.RotateObjectLocal(Vector3.Up, GD.Randf() * Mathf.Tau);
        Tween tween = CreateTween();
        tween.TweenInterval(8.0);
        tween.TweenProperty(decal, "modulate:a", 0.0f, 1.0);
        tween.TweenCallback(Callable.From(decal.QueueFree));
    }
}
```

- 贴花沿自己的 Y 轴向下投射，`size` 的 Y 是投影深度，尽量短
- 硬表面贴花 `upper_fade` `lower_fade` 设 0 再压低 Y，AABB 更小
- 有法线或 ORM 贴图时须有 `texture_albedo` 的 alpha 作遮罩
- 只改法线或粗糙度：`albedo_mix` 设 0
- 看起来镜像就绕投影轴转 180 度，`normal_fade` 设 0.5 可确认朝向
- 排序用 `VisualInstance3D.sorting_offset`，不保证严格优先级
- 永远在上：设成大于重叠中最大贴花 AABB 长度的正数
- `cull_mask` 配合可见层，避免贴到动态物体
- 贴花不能用自定义 shader
- 过滤 `rendering/textures/decals/filter`，像素风选 Nearest
- 烘光照图后动态物体没阴影，脚下放朝下贴花当 blob shadow
- 世界里写文字用 `Label3D`，不用贴花

| 渲染器 | 贴花数量 |
|---|---|
| Forward+ | 不限，与灯、反射探针共用 512 个簇元素，调 `rendering/limits/cluster_builder/max_clustered_elements` |
| Mobile | 每个网格资源最多 8 个，超出闪烁 |
| Compatibility | 4.7 不渲染 |
