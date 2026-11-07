# 场景导入与关卡构建

格式选择、导入面板、名字后缀、高级导入设置、继承场景与导入脚本、运行时加载 glTF、GridMap、CSG。

## 格式

| 格式 | 结论 |
|---|---|
| glTF 2.0 `.glb` `.gltf` | 首选。`.glb` 单文件，`.gltf` 加 `.bin` 加贴图适合版本管理或要独立贴图 |
| `.blend` | 编辑器调用 Blender 导出 glTF。要求团队每个人装 Blender 3.0 以上 推荐 3.5 以上。网页与安卓编辑器不可用 |
| FBX | 默认走 ufbx 库。FBX2glTF 要装外部程序 不推荐 |
| DAE | 老格式 复杂场景和动画用 glTF |
| OBJ | 没有骨骼 动画 UV2 PBR 材质 默认只导成单个网格资源 |

Blender 导出 glTF：

- 含混合形状的模型开 Data > Armature > Export Deformation Bones Only，否则着色错误
- Blender 材质默认关背面剔除，导出后 Godot 材质剔除为 Disabled
- 在 Blender 材质页勾 Backface Culling 再导，免得多画背面

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
| `materials/extract` | 材质提取模式 0 保持内嵌 1 提取一次 2 每次导入覆盖 格式由 `materials/extract_format` 定 默认 `.tres` |
| `import_script/path` | 导入后处理脚本 |
| `nodes/root_script` | 给根节点挂脚本 类型不兼容时根节点会换成兼容类型 |
| `nodes/use_node_type_suffixes` | 关掉后决定节点类型的后缀失效 `-noimp` `-alpha` `-vcol` `-loop` 仍有效 |
| `nodes/use_name_suffixes` | 关掉后通用导入代码不再看后缀 glTF 导入器自己检查的 `-loop` 仍可能有效 |

| glTF Embedded Texture Handling | 结果 |
|---|---|
| Discard All Textures | 丢弃，自己配材质 |
| Extract Textures | 抽成图片，可改压缩 |
| Embed as Basis Universal、Embed as Uncompressed | 保持内嵌 |

## 名字后缀

建模软件里的对象名带后缀，导入时自动处理。连接符可以是 `-` `$` `_`，大小写不敏感。

| 后缀 | 作用 |
|---|---|
| `-col` | 加三角网碰撞子节点 静态关卡用 |
| `-convcol` | 加凸包碰撞 简单或动态物体 |
| `-colonly` | 删掉网格 只留 `StaticBody3D` 碰撞 可用单独的简模当碰撞 |
| `-convcolonly` | 同上 用凸分解 |
| `-occ` `-occonly` | 生成 `Occluder3D` 保留或不保留网格 |
| `-navmesh` | 转成导航网格 原网格删除 |
| `-rigid` | 导入为 `RigidBody3D` 碰撞形状为凸包 |
| `-vehicle` `-wheel` | `VehicleBody3D` 与 `VehicleWheel3D` |
| `-noimp` | 节点或动画不导入 |
| `-alpha` | 材质用 Alpha 透明 |
| `-vcol` | 材质用顶点色作反照率 |
| `loop` `cycle` | 动画名以此词开头或结尾则循环 不需要连接符 |

- 多个节点引用同一网格时，碰撞形状按网格共享
- 第一个带碰撞后缀的节点决定全部节点的形状类型，4.7.2 实测
- 要不同形状就用不同网格
- 能用少量基本形状就别用三角网或凸包

## 高级导入设置

双击场景文件，或导入面板点 Advanced。

| 页 | 可做 |
|---|---|
| 场景页选中节点 | Skip Import、Generate Physics、Generate NavMesh、Generate Occluder |
| 网格页 | Save to File 存成网格资源，推荐 `.res`；逐网格覆盖 Shadow Meshes、Lightmap UV、LODs |
| 材质页 | Use External；Actions 里 Extract Materials 一次提取全部 |

- Generate Physics 选 Static、Dynamic 或 Area
- Trimesh 形状只给静态，动态物体用基本形状或凸分解
- 存成的网格资源可给 `MultiMeshInstance3D` 或粒子用
- 提取后场景指向外部 `.tres`，重导入不覆盖你改的材质
- 源文件里材质改名会断开链接
- 用外部材质后对话框预览仍显示原材质，到别的场景里看

## 继承场景与导入脚本

导入的场景不能直接保存修改，重导入会整个覆盖。

| 做法 | 用于 |
|---|---|
| 直接实例化到自己的场景，开 Editable Children 改子节点属性 | 摆放道具 改个别节点的变换或材质 |
| 在编辑器里打开导入场景时选新建继承场景 | 给导入模型加脚本 碰撞 粒子 子节点 基础场景的节点不能删 子资源不能直接改 需先存成外部文件 |
| 导入脚本 `EditorScenePostImport` | 批量规则 例如统一改材质 命名 加碰撞层 |

- 继承场景里基础场景的节点不能删，子资源要先存成外部文件再改
- 能在源文件或导入设置里解决的不放到导入后处理
- 几十万顶点的自定义网格数据在导入阶段烘成 `.res`，运行时直接 `load()`

```gdscript
@tool
extends EditorScenePostImport

func _post_import(scene: Node) -> Object:
	for body: Node in scene.find_children("*", "StaticBody3D"):
		(body as StaticBody3D).collision_layer = 1 << 1
	return scene
```

```csharp
[Tool]
public partial class SetBodyLayer : EditorScenePostImport
{
    public override GodotObject _PostImport(Node scene)
    {
        foreach (Node body in scene.FindChildren("*", "StaticBody3D"))
        {
            ((StaticBody3D)body).CollisionLayer = 1u << 1;
        }
        return scene;
    }
}
```

- 脚本不挂在节点上，路径填进导入面板 Import Script 的 Path
- 必须返回场景

## 动画库导入

- 导入类型改为 Animation Library，glTF 只作为 `AnimationLibrary` 导入
- 放进 `AnimationPlayer`，一套动作多个角色共用
- 切换导入类型要重启编辑器

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

```csharp
public partial class ModelLoader : Node3D
{
    public Node LoadModel(string path)
    {
        var document = new GltfDocument();
        var state = new GltfState();
        if (document.AppendFromFile(path, state) != Error.Ok)
        {
            return null;
        }
        return document.GenerateScene(state);
    }
}
```

- 用于玩家自带模型或 mod，得到的节点 `add_child()` 加入场景
- 编辑器导入设置与后缀在运行时加载里不生效
- C# 类名是 GltfDocument、GltfState

## GridMap 与 MeshLibrary

MeshLibrary 场景格式：

| 节点 | 规则 |
|---|---|
| 根 | `Node3D` |
| 每个子节点 | 一个 `MeshInstance3D`，成为一个库条目 |
| 材质 | 放在网格的材质槽，节点上的材质被忽略 |
| 碰撞 | 条目下最多一个 `StaticBody3D`，下面放 `CollisionShape3D` |
| 导航 | 条目下最多一个 `NavigationRegion3D`，其下网格只用于烘焙 |
| 其他节点 | 不识别 |

- 菜单 Scene > Export As > MeshLibrary 存成资源，赋给 `GridMap.mesh_library`
- `GridMap` 只能放网格加碰撞加导航，不能放任意节点

```gdscript
extends GridMap

func place(world_position: Vector3, item: int) -> void:
	var cell: Vector3i = local_to_map(to_local(world_position))
	set_cell_item(cell, item)
```

```csharp
public partial class LevelGrid : GridMap
{
    public void Place(Vector3 worldPosition, int item)
    {
        Vector3I cell = LocalToMap(ToLocal(worldPosition));
        SetCellItem(cell, item);
    }
}
```

| 属性 | 说明 |
|---|---|
| `cell_size` | 默认 `Vector3(2, 2, 2)` |
| `cell_scale` | 只缩放格内条目，不改格距 |
| `cell_octant_size` | 默认 8，八叉块每轴格数 |
| `bake_navigation` | 默认关，开了才为每格建导航区域 |

- 空格返回 `GridMap.INVALID_CELL_ITEM`
- UV2 精度在转 MeshLibrary 之前设好，之后改不影响已有的库
- 没有 UV2 时烘焙自动生成，精度 0.1
- 导航烘焙的 `cell_size` 与导航地图一致，否则格子间接不上
- 小格距时调小 `NavigationMesh.agent_radius` 与 `region_min_size`
- 导入时 `mesh_library/use_node_names_as_mesh_names` 默认关

## CSG

只用于灰盒，没有 UV 编辑。节点有 `CSGBox3D` `CSGSphere3D` `CSGCylinder3D` `CSGTorus3D` `CSGPolygon3D` `CSGMesh3D` `CSGCombiner3D`，操作有 Union、Intersection、Subtraction。

- 根 CSG 节点才产生网格和碰撞
- `CSGShape3D.use_collision` 默认关，开启后隐藏节点的碰撞仍有效
- 4.4+ CSG 菜单 Bake Mesh Instance 得到 `MeshInstance3D`，之后才能烘遮挡
- 烘光照图还要对它执行 Mesh 菜单的 Unwrap UV2
- 烘完不自动隐藏原 CSG 节点
- 4.4+ Bake Collision Shape 生成三角网碰撞，须放在 `StaticBody3D` 或 `AnimatableBody3D` 下
- 脚本里用 `CSGShape3D.bake_static_mesh()` 与 `CSGShape3D.bake_collision_shape()` 4.4+
- CSG 网格延迟一帧更新，`_ready()` 里先 `await get_tree().process_frame`
- 正式关卡用 Blender 建模，或 FuncGodot 一类的关卡插件
