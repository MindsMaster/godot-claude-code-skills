# 场景导入与关卡构建

## 格式

| 格式 | 结论 |
|---|---|
| glTF 2.0 `.glb` `.gltf` | 首选。`.glb` 单文件，`.gltf` 加 `.bin` 加贴图适合版本管理或要独立贴图 |
| `.blend` | 编辑器调用 Blender 导出 glTF。要求团队每个人装 Blender 3.0 以上 推荐 3.5 以上。网页与安卓编辑器不可用 |
| FBX | 默认走 ufbx 库。FBX2glTF 要装外部程序 不推荐 |
| DAE | 老格式 复杂场景和动画用 glTF |
| OBJ | 没有骨骼 动画 UV2 PBR 材质 默认只导成单个网格资源 |

Blender 导出 glTF 的两个坑：含混合形状的模型要开 Data > Armature > Export Deformation Bones Only，否则着色错误。Blender 材质默认关背面剔除，导出后 Godot 材质剔除为 Disabled，会多画背面，在 Blender 材质页勾 Backface Culling 再导。

## 导入面板

选中文件后在导入面板改，改完点 Reimport。

| 选项 | 说明 |
|---|---|
| `nodes/root_type` | 用 `Node3D` 派生类型，否则不能在 3D 视口里直接摆放 |
| `nodes/root_scale` 与 `nodes/apply_root_scale` | 默认把缩放烘进网格和动画 子节点不被缩放 |
| `meshes/ensure_tangents` | 默认开 法线贴图需要切线 源文件有切线就关掉省体积 |
| `meshes/generate_lods` | 默认开 自动 mesh LOD 蒙皮网格偶有问题时关 |
| `meshes/create_shadow_meshes` | 默认开 焊接顶点减少阴影带宽 |
| `meshes/light_baking` | 默认 1 即 Static 不生 UV2。2 即 Static Lightmaps 才生 UV2 |
| `meshes/lightmap_texel_size` | 默认 0.2 只在 Static Lightmaps 下有效 |
| animation 分组的 `fps` | 默认 30 烘焙曲线用 与源软件一致 |
| animation 分组的 `trimming` `remove_immutable_tracks` | 减小体积 |
| `materials/extract` | 把内嵌材质提取成 `.tres` |
| `import_script/path` | 导入后处理脚本 |
| `nodes/use_node_type_suffixes` | 关掉后类型后缀失效 `-noimp` 仍有效 |
| `nodes/use_name_suffixes` | 关掉后所有后缀失效 |

glTF 的 Embedded Texture Handling：Discard All Textures 自己配材质，Extract Textures 抽出成图片可改压缩，Embed as Basis Universal 与 Embed as Uncompressed 保持内嵌。

## 名字后缀

对象在建模软件里的名字带这些后缀，导入时自动处理。前面的连接符可以是 `-` `$` `_`，大小写不敏感。

| 后缀 | 作用 |
|---|---|
| `-col` | 加三角网碰撞子节点 静态关卡用 |
| `-convcol` | 加凸包碰撞 简单或动态物体 |
| `-colonly` | 删掉网格 只留 `StaticBody3D` 碰撞 可用单独的简模当碰撞 |
| `-convcolonly` | 同上 用凸分解 |
| `-occ` `-occonly` | 生成 `Occluder3D` 保留或不保留网格 |
| `-navmesh` | 转成导航网格 原网格删除 |
| `-rigid` | 导入为 `RigidBody3D` |
| `-vehicle` `-wheel` | `VehicleBody3D` 与 `VehicleWheel3D` |
| `-noimp` | 节点或动画不导入 |
| `-alpha` | 材质用 Alpha 透明 |
| `-vcol` | 材质用顶点色作反照率 |
| `loop` `cycle` | 动画名含此词则循环 不需要连接符 |

能用少量基本形状就别用三角网或凸包。

## 高级导入设置

双击场景文件，或导入面板点 Advanced。

- 场景页选中节点：Skip Import，Generate Physics（选 Static Dynamic Area，形状选 Trimesh 仅静态用，动态物体用基本形状或凸分解），Generate NavMesh，Generate Occluder
- 网格页：Save to File 存成网格资源 推荐 `.res`，用于 `MultiMeshInstance3D` 或粒子，Generate 里的 Shadow Meshes Lightmap UV LODs 逐网格覆盖
- 材质页：Use External 用外部材质。Actions 里 Extract Materials 一次提取全部，之后场景自动指向外部 `.tres`，源文件重导入不覆盖你改的材质。源文件里材质改名会断开链接
- 用外部材质后，这个对话框预览仍显示原材质，要在别的场景里看

## 继承场景与实例化

导入的场景不能直接保存修改，重导入会整个覆盖。三种做法：

| 做法 | 用于 |
|---|---|
| 直接实例化到自己的场景，开 Editable Children 改子节点属性 | 摆放道具 改个别节点的变换或材质 |
| 在编辑器里打开导入场景时选新建继承场景 | 给导入模型加脚本 碰撞 粒子 子节点 基础场景的节点不能删 子资源不能直接改 需先存成外部文件 |
| 场景树右键 Make Local | 断开实例与导入文件的链接，节点变成当前场景自己的，之后重导入的变化不再同步过来。只在确定不再跟随源文件时用 |
| 导入脚本 `EditorScenePostImport` | 批量规则 例如统一改材质 命名 加碰撞层 |

能在源文件或导入设置里解决的事不要放到导入后处理里。大体量的网格数据（几十万顶点的 JSON 或自定义格式）不要在运行时解析再手建 `ArrayMesh`，在导入阶段烘焙成 `.res` 网格资源，运行时直接 `load()`。

```gdscript
@tool
extends EditorScenePostImport

func _post_import(scene: Node) -> Object:
	for body: Node in scene.find_children("*", "StaticBody3D"):
		(body as StaticBody3D).collision_layer = 1
	return scene
```

脚本不挂在任何节点上，路径填进导入面板 Import Script 的 Path。必须返回场景。

## 动画库导入

导入面板的导入类型改为 Animation Library，glTF 只作为 `AnimationLibrary` 导入，放进 `AnimationPlayer`，一套动作多个角色共用。切换类型要重启编辑器。

## 运行时加载 glTF

```gdscript
extends Node3D

func load_model(path: String) -> Node:
	var document: GLTFDocument = GLTFDocument.new()
	var state: GLTFState = GLTFState.new()
	if document.append_from_file(path, state) != OK:
		return null
	return document.generate_scene(state)
```

用于玩家自带模型或 mod。得到的节点用 `add_child()` 加入场景。编辑器导入设置与后缀行为在运行时加载里不生效。

## GridMap 与 MeshLibrary

MeshLibrary 场景格式：

- 根节点 `Node3D`
- 每个子节点是一个 `MeshInstance3D`，成为一个库条目
- 材质放在网格的材质槽里，节点上的材质被忽略
- 最多一个 `StaticBody3D` 子节点作碰撞，下面放 `CollisionShape3D`
- 最多一个 `NavigationRegion3D` 子节点作导航，它下面的网格不会导出为视觉网格
- 其他节点类型不识别

菜单 Scene > Export As > MeshLibrary 存成资源，赋给 `GridMap.mesh_library`。`GridMap` 不能放任意节点，只能放网格加碰撞加导航。

```gdscript
extends GridMap

func place(world_position: Vector3, item: int) -> void:
	var cell: Vector3i = local_to_map(to_local(world_position))
	set_cell_item(cell, item)
```

- `cell_size` 默认 `Vector3(2, 2, 2)`，`cell_scale` 只缩放格内条目 不改格距
- 空格返回 `GridMap.INVALID_CELL_ITEM`
- 烘焙光照图前，生成 UV2 的精度要在转 MeshLibrary 之前设好，之后改不影响已有的库。没有 UV2 时烘焙自动生成，精度 0.1
- 导航网格烘焙的 `cell_size` 要与导航地图一致，否则格子之间的网格接不上
- 小格距时要调小 `NavigationMesh.agent_radius` 与 `region_min_size`
- 条目带导航网格时，开 `GridMap.bake_navigation` 才为每格创建导航区域，默认关
- `cell_octant_size` 默认 8，是八叉块在三个轴向的格数
- 导入时 `mesh_library/use_node_names_as_mesh_names` 默认关

## CSG

CSG 只用于灰盒。节点有 `CSGBox3D` `CSGSphere3D` `CSGCylinder3D` `CSGTorus3D` `CSGPolygon3D` `CSGMesh3D` `CSGCombiner3D`，操作有 Union Intersection Subtraction，没有 UV 编辑。

- 根 CSG 节点才产生网格和碰撞。`CSGShape3D.use_collision` 默认关
- 4.4+ 菜单 CSG 下 Bake Mesh Instance 得到 `MeshInstance3D`，之后才能烘光照图和遮挡，加载也更快。烘完要隐藏原 CSG 节点
- 4.4+ Bake Collision Shape 生成三角网碰撞，必须放在 `StaticBody3D` 或 `AnimatableBody3D` 下才有效
- 脚本里用 `CSGShape3D.bake_static_mesh()` 与 `CSGShape3D.bake_collision_shape()`，4.4+
- 正式关卡用 Blender 建模，或 FuncGodot 一类的关卡插件

## 参考

- https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/index.html
- https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/node_type_customization.html
- https://docs.godotengine.org/en/stable/tutorials/3d/using_gridmaps.html
- https://docs.godotengine.org/en/stable/tutorials/3d/csg_tools.html
