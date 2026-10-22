# LOD 剔除 实例化 贴花

## 选哪个

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

- glTF 与 `.blend` 默认生成，OBJ 要把导入类型改为 Scene 再重导入并重启编辑器
- `rendering/mesh_lod/lod_change/threshold_pixels` 默认 1 像素，调大切换更早 画质更低
- 运行时改根视口的 `mesh_lod_threshold`，每个视口独立
- 单个对象调 `GeometryInstance3D.lod_bias`，大于 1 切换更晚
- `ReflectionProbe.mesh_lod_threshold` 对 Always 更新的探针有用
- 选级用节点 AABB 离相机最近的点，`MultiMeshInstance3D` 与粒子的所有实例同一级。GPU 粒子 LOD 不对时用 Generate AABB 设好可见框
- 蒙皮网格偶有渲染问题，在导入设置里关该网格的 LOD
- 在编辑器视口菜单里有 Disable Mesh LOD 调试模式可对比

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

- `visibility_range_begin` 与 `visibility_range_end` 默认 0 即不做范围检查
- `visibility_range_fade_mode`：Disabled 用滞回瞬间切换 最快。Self 用 alpha 淡入淡出 Dependencies 配合 `Node3D.visibility_parent` 做 HLOD。淡出时对象被强制透明渲染
- 淡出模式只在 margin 大于 0 时才可见，且只在 Forward+ 有效，Mobile 与 Compatibility 下等同 Disabled 且没有滞回
- HLOD：一组房子的合并大网格设 `visibility_range_begin`，每个房子的 `visibility_parent` 指向合并网格，无需再设房子的 end
- `visibility_parent` 目标必须是 `GeometryInstance3D`，可以不是父节点，不能指向子节点
- `visible` 为 false 的节点退出依赖树，`visibility_parent` 目标被隐藏时子节点不再按它的 `visibility_range_begin` 隐藏
- 自动 LOD 与 visibility range 可以同时用在同一个网格上

## 遮挡剔除

1. 打开 `rendering/occlusion_culling/use_occlusion_culling`，默认关，即时生效，网页导出模板不支持。也可运行时设根视口 `use_occlusion_culling`
2. 场景里放 `OccluderInstance3D`，点 Bake Occluders。只烘 `MeshInstance3D`，不含 `MultiMeshInstance3D` 粒子和 CSG，CSG 先转成 `MeshInstance3D`
3. 动态物体被烘进去时：把它们放到其他可见层，并在烘焙掩码 `bake_mask` 去掉那一层，重烘
4. 手摆遮挡体：`QuadOccluder3D` `BoxOccluder3D` `SphereOccluder3D` `PolygonOccluder3D`，过程化用 `ArrayOccluder3D`

要点：

- 被遮挡物的 AABB 必须被完全遮住才剔除，大遮挡体如墙比小摆设有效，小物体比大物体容易被剔除
- 室内多小房间、室外金字塔形地形效果好。几乎没有遮挡机会的场景反而多花 CPU
- 不要在游戏中移动 `OccluderInstance3D` 或它的父级，会重建 BVH。门开启时隐藏遮挡体比移动便宜
- 遮挡体越简单越好，调大 `bake_simplification_distance` 后重烘。过大会误剔除
- 项目设置 `rendering/occlusion_culling/bvh_build_quality` 与 `occlusion_rays_per_thread` 调 CPU 负载
- Mobile 渲染器没有深度预通道，遮挡剔除对它收益最大
- `GeometryInstance3D.ignore_occlusion_culling` 可让个别对象跳过

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

- `use_colors` `use_custom_data` `transform_format` 必须在 `instance_count` 之前设，或先把 `instance_count` 设回 0。`instance_count` 大于 0 时改它们会报错且不生效。设 `instance_count` 会清空并重设缓冲
- 改数量用 `visible_instance_count`，默认 -1 全画
- 大量更新用 `buffer` 一次写入，比逐个 `set_instance_transform()` 快
- 逐实例颜色要材质读顶点色：`StandardMaterial3D` 的 `vertex_color_use_as_albedo`，自写 shader 读 `COLOR` 与 `INSTANCE_CUSTOM`
- 一个 `MultiMesh` 是一个剔除对象，实例相距很远时拆成多个节点，视锥与遮挡剔除才能剔除各节点
- 实例没有物理碰撞，要碰撞另放静态体
- 混合形状被忽略
- 共享同一个对象的光源数量上限，用尽后其余实例不受光
- 编辑器里 MultiMesh 菜单的 Populate surface 可按目标表面撒点
- 逐实例的 shader 参数用 `instance uniform` 对 `MultiMeshInstance3D` 是整体一份，逐实例变化用 `COLOR` 与 `INSTANCE_CUSTOM`

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

- `size` 的 Y 轴是投影深度，尽量短以便剔除。贴花沿自己的 Y 轴向下投射。硬表面贴花把 `upper_fade` 与 `lower_fade` 设 0 再压低 Y，外观不变而 AABB 更小
- 有法线或 ORM 贴图时必须有 `texture_albedo` 提供 alpha 作遮罩。只想改法线或粗糙度，`albedo_mix` 设 0
- 贴花看起来镜像就绕投影轴转 180 度。`normal_fade` 设 0.5 可确认朝向
- 排序用 `VisualInstance3D.sorting_offset`，仅作指引，不保证严格优先级。要永远在上，设成大于重叠中最大贴花 AABB 长度的正数
- `cull_mask` 配合可见层，避免贴到动态物体上
- 贴花不能用自定义 shader。被投影表面的 shader 能读到贴花改写的粗糙度与金属度
- Forward+ 贴花数量不限，但与灯 反射探针共用 512 个簇元素上限，调 `rendering/limits/cluster_builder/max_clustered_elements`。Mobile 每个网格资源最多 8 个，超出会闪烁。Compatibility 在 4.7 不渲染贴花
- 过滤方式 `rendering/textures/decals/filter`，像素风选 Nearest
- Blob shadow：烘焙光照图后动态物体没有阴影，在脚下放朝下的贴花，长度拉长可提示落点
- 在世界里写任意文字用 `Label3D`，不用贴花

## 参考

- https://docs.godotengine.org/en/stable/tutorials/3d/mesh_lod.html
- https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html
- https://docs.godotengine.org/en/stable/tutorials/3d/occlusion_culling.html
- https://docs.godotengine.org/en/stable/tutorials/3d/using_decals.html
