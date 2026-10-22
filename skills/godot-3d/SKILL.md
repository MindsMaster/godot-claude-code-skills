---
name: godot-3d
description: Godot 3D 场景搭建与选型 用于 CharacterBody3D 角色移动 floor slope 参数, Jolt 与 GodotPhysics3D 物理引擎选择, 碰撞层规划, RayCast3D ShapeCast3D 与 PhysicsDirectSpaceState3D 查询, SpringArm3D 第三人称相机, Forward+ Mobile Compatibility 渲染器选择, 光照与全局光照选型 SDFGI VoxelGI LightmapGI ReflectionProbe, WorldEnvironment Environment CameraAttributes, 阴影参数, glTF 场景导入与 -col -rigid 后缀, GridMap MeshLibrary, CSG 原型, mesh LOD visibility_range OccluderInstance3D 遮挡剔除, MultiMeshInstance3D, Decal, NavigationAgent3D 寻路, LookAtModifier3D SpringBoneSimulator3D TwoBoneIK3D 骨骼修改器. Use when building or debugging 3D scenes, character controllers, lighting, level import, culling and 3D navigation.
---

# Godot 3D

3D 场景用哪个节点、哪个资源、哪个项目设置，以及照直觉会写错的地方。着色器、粒子、后处理转 `godot-shaders-vfx`。动画状态机转 `godot-animation`。2D 精灵放进 3D 转 `godot-2d-in-3d`。帧率剖析转 `godot-performance`。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 角色走跑跳 | `CharacterBody3D` + `move_and_slide()` | 手算坡度和地面检测 |
| 第三人称相机不穿墙 | `SpringArm3D` | 每帧射线加手动拉近 |
| 点选 狙击 视线 | `PhysicsRayQueryParameters3D` + `intersect_ray()` | 遍历所有物体算相交 |
| 前方探测 持续检测 | `RayCast3D` `ShapeCast3D` | 每帧 new 查询参数 |
| 敌人寻路与避让 | `NavigationRegion3D` + `NavigationAgent3D` | 手写 A* 和路点 |
| 大量相同网格 草 石头 | `MultiMeshInstance3D` | 几千个 `MeshInstance3D` |
| 远处降面 | 导入时自动 mesh LOD | 脚本按距离换网格 |
| 远处整组替换 淡出标签 | `GeometryInstance3D.visibility_range_end` | 脚本逐帧算距离 |
| 室内遮挡 | `OccluderInstance3D` | 手动隐藏房间 |
| 弹孔 污渍 假阴影 | `Decal` | 运行时拼贴图网格 |
| 灰盒关卡 | CSG 节点 后转 `MeshInstance3D` | 把 CSG 带进发布版 |
| 网格拼装关卡 | `GridMap` + `MeshLibrary` | 脚本循环摆几百个实例 |
| 头部看向 尾巴发丝摆动 腿部 IK | 骨骼修改器 见下文版本表 | 每帧手改 `Skeleton3D` 骨骼姿态 |
| 天空 雾 泛光 色调映射 | `WorldEnvironment` + `Environment` | 多个 `SubViewport` 堆后处理 |
| 曝光 景深 | `CameraAttributesPractical` | 脚本改亮度 |
| 间接光 | SDFGI VoxelGI LightmapGI | 到处摆补光灯 |
| 导入后加碰撞 | 名字后缀 `-col` 或高级导入设置 | 导入后脚本遍历加 `CollisionShape3D` |
| 高刷新率下相机抖动 | `physics/common/physics_interpolation` | 自己在 `_process` 里插值 |

## 做法

### 角色移动

```gdscript
extends CharacterBody3D

@export var speed: float = 5.0
@export var jump_velocity: float = 4.5

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity += get_gravity() * delta
	elif Input.is_action_just_pressed("jump"):
		velocity.y = jump_velocity

	var input: Vector2 = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction: Vector3 = (global_basis * Vector3(input.x, 0.0, input.y)).normalized()
	velocity.x = direction.x * speed
	velocity.z = direction.z * speed
	move_and_slide()
```

`velocity` 是每秒速度，不乘 `delta`。`is_on_floor()` 读的是上一次 `move_and_slide()` 的结果。相机相对移动时用相机的 yaw 基底代替 `global_basis`。

| 属性 | 默认 | 说明 |
|---|---|---|
| `floor_max_angle` | 0.7853982 | 弧度 45 度 超过算墙 |
| `floor_snap_length` | 0.1 | 下坡贴地 上升速度大于 0 时不吸附 |
| `floor_stop_on_slope` | true | 站着不下滑 |
| `floor_constant_speed` | false | 上下坡速度一致 需配合 `floor_snap_length` |
| `floor_block_on_wall` | true | 只在地面上移动 不能爬墙 但会沿墙下滑 |
| `wall_min_slide_angle` | 0.2617994 | 弧度 15 度 撞墙角度小于此值不滑 Grounded 下需 `floor_block_on_wall` 为 true 才生效 |
| `max_slides` | 6 | 一次 `move_and_slide()` 最多换向次数 |
| `safe_margin` | 0.001 | 碰撞恢复余量 大了更稳地识别墙和地面 小了更精确 极小缩放或叠放多个角色时用小值 |
| `motion_mode` | 0 | `MOTION_MODE_GROUNDED` 平台类 `MOTION_MODE_FLOATING` 太空与俯视 |
| `platform_on_leave` | 0 | `PLATFORM_ON_LEAVE_ADD_VELOCITY` 离开移动平台时带上平台速度 另有 `ADD_UPWARD_VELOCITY` `DO_NOTHING` |

没有内置台阶。需要上台阶时用斜面碰撞体，或用 `ShapeCast3D` 自己做台阶检测。重力方向不是 Y 轴时改 `up_direction`。

### 物理引擎

| 引擎 | 状态 |
|---|---|
| GodotPhysics3D | 设置值 `DEFAULT` 在 4.7 仍等于它 老项目升级后保持 |
| Jolt Physics | 4.4 起内置模块 4.6 起新建项目默认选用 通常更快更稳 |

```ini
[physics]

3d/physics_engine="Jolt Physics"
```

新建项目默认就是它。从 4.5 及更早升级的项目手动改，改完重启编辑器。切换后关节软限制属性不支持，只设一个物体的关节默认把它当 `node_b`，射线 `face_index` 默认 -1，其余差异见 [references/physics-3d.md](references/physics-3d.md)。

### 碰撞层

先列碰撞对再分层，在 `layer_names/3d_physics/layer_1` 到 `layer_32` 里起名。

| 层 | 内容 | 它的 mask 勾选 |
|---|---|---|
| 1 world | 静态关卡 | 无 |
| 2 player | 玩家身体 | 1 3 |
| 3 enemy | 敌人身体 | 1 2 3 |
| 4 player_hit | 玩家子弹与近战判定 `Area3D` | 3 |
| 5 enemy_hit | 敌人攻击判定 `Area3D` | 2 |
| 6 pickup | 拾取物 `Area3D` | 无 玩家的 `Area3D` 勾 6 |
| 7 camera_block | 只给 `SpringArm3D` 用的墙体 | 无 |

```gdscript
extends CharacterBody3D

const LAYER_WORLD: int = 1 << 0
const LAYER_PLAYER: int = 1 << 1
const LAYER_ENEMY: int = 1 << 2

@export_flags_3d_physics var hit_mask: int = LAYER_ENEMY

func _ready() -> void:
	collision_layer = LAYER_PLAYER
	collision_mask = LAYER_WORLD | LAYER_ENEMY
```

`collision_layer` 是我在哪层，`collision_mask` 是我扫描哪层，`set_collision_mask_value(n, true)` 按层号开关单层。位掩码第 n 层是 `1 << (n - 1)`。`Area3D` 检测不到谁，先查对方的 layer 是否在自己的 mask 里。

### 空间查询

| 需求 | 用这个 |
|---|---|
| 固定方向持续探测 地面 前方墙 | `RayCast3D` 节点 每物理帧自动更新 |
| 同一物理帧改参数后立刻读 | `RayCast3D.force_raycast_update()` |
| 点选 hitscan 一次性射线 | `intersect_ray()` |
| 有厚度的探测 扫过一个形状 | `ShapeCast3D` 或 `cast_motion()` |
| 某位置的范围内有谁 | `intersect_shape()` |
| 两个形状是否相交与接触点 | `collide_shape()` 与 `get_rest_info()` |

```gdscript
extends Camera3D

const RAY_LENGTH: float = 1000.0

func pick(mouse_position: Vector2) -> Dictionary:
	var space: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	var from: Vector3 = project_ray_origin(mouse_position)
	var to: Vector3 = from + project_ray_normal(mouse_position) * RAY_LENGTH
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(from, to, 1 << 2)
	query.collide_with_areas = true
	return space.intersect_ray(query)
```

结果是字典，没命中为空，命中有 `position` `normal` `collider` `rid` `shape`。

C# 版本和 `Dictionary` 取值写法见 [references/physics-3d.md](references/physics-3d.md)。

`direct_space_state` 只能在 `_physics_process()` 里访问，其他时机可能报 space 被锁。在 `_input()` 里记下鼠标位置，下一个物理帧再查询。

### 第三人称相机

节点结构：`Node3D` 枢轴，下面 `SpringArm3D`，下面 `Camera3D`。`spring_length` 默认 1.0，按需要的臂长改。`SpringArm3D.shape` 留空且相机是直接子节点时，用相机近平面做形状；留空但相机不是直接子节点会退成射线，不推荐。给了形状就一直用该形状，球形最顺滑。

```gdscript
extends Node3D

@export var mouse_sensitivity: float = 0.003

@onready var _arm: SpringArm3D = $SpringArm3D

func _ready() -> void:
	var body: CollisionObject3D = get_parent() as CollisionObject3D
	if body != null:
		_arm.add_excluded_object(body.get_rid())

func _unhandled_input(event: InputEvent) -> void:
	var motion: InputEventMouseMotion = event as InputEventMouseMotion
	if motion == null or Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		return
	rotate_y(-motion.screen_relative.x * mouse_sensitivity)
	_arm.rotation.x = clampf(_arm.rotation.x - motion.screen_relative.y * mouse_sensitivity, -1.2, 1.2)
```

弹簧臂 `collision_mask` 默认只有第 1 层。玩家碰撞层落在它的 mask 里又没排除时，起点在玩家碰撞体外、朝玩家扫去的弹簧臂会被自己顶短，如枢轴高过头顶再仰视。起点已在碰撞体内的重叠会被忽略。上面的层表里玩家在第 2 层，保持 mask 只勾 world 层也能避开。

### 渲染器

| 选这个 | 条件 |
|---|---|
| Forward+ | 桌面 3D 要 SDFGI VoxelGI SSR SSIL 体积雾 |
| Mobile | 手机 一体机 XR 要 `CompositorEffect` 要光照投影 |
| Compatibility | 网页 老硬件 简单 3D 与 2D |

能力差异表见 [references/rendering-lighting.md](references/rendering-lighting.md)。导出到网页只能用 Compatibility。切换渲染器后场景和环境要重新调。

### 光照与 GI 选型

| 技术 | 渲染器 | 实时性 | 动态物体 | 工作量 |
|---|---|---|---|---|
| 无 GI 加环境光 | 全部 | 是 | 是 | 无 |
| `ReflectionProbe` | 全部 | 更新模式 Once 或 Always | 接收 | 手摆 |
| `LightmapGI` | 全部渲染 烘焙需 RenderingDevice | 否 | 靠 `LightmapProbe` | UV2 加烘焙 |
| `VoxelGI` | 仅 Forward+ | 是 动态物体可发光 | 是 | 摆节点加烘焙 几秒 |
| SDFGI | 仅 Forward+ | 半实时 | 只接收 | 环境里开关 |
| SSIL | 仅 Forward+ | 是 | 是 | 环境里开关 只当补充 |

桌面项目先开 SDFGI，不够再换。手机只能 `LightmapGI` 加 `ReflectionProbe`。性能从快到慢：`ReflectionProbe`，`LightmapGI`，`VoxelGI`，SSIL，SDFGI。网格的 `gi_mode` 默认 Static，会参与 SDFGI 与光照图。小型动态物体设 Disabled，大型动态物体如移动的列车设 Dynamic，Dynamic 只对 VoxelGI 有效。灯的烘焙模式细节见参考文件。

### 环境与相机属性

- `WorldEnvironment` 每个场景树只放一个。`Camera3D.environment` 优先级更高
- `Environment.tonemap_mode` 默认 Linear，亮部直接截断。换 Filmic 或 ACES，4.4+ 有 AgX。写实场景 `tonemap_white` 至少 6.0，AgX 改用 `tonemap_agx_white`，Mobile 的 `tonemap_white` 要 2.0 以下
- `Camera3D.attributes` 优先于 `WorldEnvironment` 上的 `CameraAttributes`。拿不准用 `CameraAttributesPractical`，`CameraAttributesPhysical` 会覆盖相机的 `fov` `near` `far` `keep_aspect`

### 场景导入

glTF 2.0 优先，`.glb` 是单文件。`.blend` 直接导入要求每个人装 Blender。OBJ 没有骨骼动画 PBR UV2。

- 在 Blender 里给对象改名带后缀：`-col` 三角网碰撞，`-convcol` 凸包，`-colonly` `-convcolonly` 只留碰撞，`-rigid` 刚体，`-navmesh`，`-occ` `-occonly`，`-noimp` 跳过，完整清单含 `-vehicle` `-wheel` `-alpha` `-vcol`。后缀大小写不敏感，连接符可以是 `-` `$` `_`
- 动画片段名以 `loop` 或 `cycle` 开头或结尾，导入时自动循环，不需要连接符
- 改材质：高级导入设置 Actions 里 Extract Materials，之后改外部 `.tres`，重导入不覆盖
- 加节点：新建继承场景，基础场景的节点不能删。只挂根脚本用导入选项 `nodes/root_script`
- 要碰撞：优先用后缀，其次高级导入设置的 Generate Physics，静态关卡 Trimesh，动态物体用基本形状

详细流程见 [references/import-and-levels.md](references/import-and-levels.md)。

### 关卡构建

- `GridMap` 需要 `MeshLibrary`。根节点 `Node3D`，每个子节点是 `MeshInstance3D`，材质放在网格里不放在节点上，碰撞放在子 `StaticBody3D`。用 Scene 菜单 Export As MeshLibrary 导出
- CSG 只做灰盒。要光照图或遮挡烘焙时先转成 `MeshInstance3D`，CSG 菜单里 Bake Mesh Instance，4.4+。`CSGShape3D.use_collision` 默认关

### 剔除与 LOD

- 导入的 glTF 默认生成 mesh LOD，OBJ 要先把导入类型改为 Scene
- 手做的多级模型用 `visibility_range_begin` `visibility_range_end` 与 `visibility_range_end_margin`。`visibility_range_fade_mode` 选 Disabled 性能最好，Self 与 Dependencies 用透明渲染做淡入淡出且只在 Forward+ 有效
- 遮挡剔除先开 `rendering/occlusion_culling/use_occlusion_culling`（默认关，网页导出模板不支持），加 `OccluderInstance3D` 烘焙。只烘 `MeshInstance3D`，动态物体放到别的可见层并在烘焙剔除掩码里去掉
- `MultiMeshInstance3D`：`transform_format` `use_colors` `use_custom_data` 必须先于 `instance_count` 设置，整个节点是一个剔除单位，实例散得太开要拆成多个节点
- `Decal` 的 `size` 里 Y 是投影深度，越短越利于剔除

LOD、遮挡剔除、`MultiMesh`、`Decal` 的完整做法见 [references/culling-and-instancing.md](references/culling-and-instancing.md)。

### 导航

```gdscript
extends CharacterBody3D

@export var speed: float = 4.0

@onready var _agent: NavigationAgent3D = $NavigationAgent3D

func go_to(target: Vector3) -> void:
	_agent.target_position = target

func _physics_process(_delta: float) -> void:
	if NavigationServer3D.map_get_iteration_id(_agent.get_navigation_map()) == 0:
		return
	if _agent.is_navigation_finished():
		return
	var next: Vector3 = _agent.get_next_path_position()
	velocity = global_position.direction_to(next) * speed
	move_and_slide()
```

场景里放 `NavigationRegion3D`，给它 `NavigationMesh`，下面放参与烘焙的网格，编辑器里点 Bake。`NavigationMesh.cell_size` 要与 `navigation/3d/default_cell_size` 一致。运行时烘焙用 `bake_navigation_mesh(true)`。`get_next_path_position()` 每物理帧只调一次，到达后不要再调。避让要开 `avoidance_enabled`、连 `velocity_computed`、给 `velocity` 赋值，并且必须设过 `target_position`。

### 骨骼修改器

作为 `Skeleton3D` 的子节点，在动画之后运行。`influence` 做淡入淡出，`active` 开关。

| 需求 | 节点 | 版本 |
|---|---|---|
| 头 炮塔看向目标 | `LookAtModifier3D` | 4.4+ |
| 头发 布料 尾巴 | `SpringBoneSimulator3D` 加 `SpringBoneCollision3D` | 4.4+ |
| 跨骨架重定向 | `RetargetModifier3D` | 4.4+ |
| 复制 转换 对齐某骨骼 | `CopyTransformModifier3D` `ConvertTransformModifier3D` `AimModifier3D` | 4.5+ |
| 手臂 腿两段 IK | `TwoBoneIK3D` | 4.6+ |
| 任意长度链 IK | `FABRIK3D` `CCDIK3D` `JacobianIK3D` | 4.6+ |
| 沿路径摆骨 | `SplineIK3D` | 4.6+ |

`SkeletonIK3D` 已弃用，新项目用上表。详细见 [references/skeleton-modifiers.md](references/skeleton-modifiers.md)。

## 陷阱

- `RayCast3D` 的 `collision_mask` 默认只有第 1 层，`PhysicsRayQueryParameters3D` 默认全部层
- 射线默认不打 `Area3D`，要设 `collide_with_areas`。射线从碰撞体内部出发默认不命中该体，要 `hit_from_inside`
- `RayCast3D` 默认 `exclude_parent` 为 true，会排除父级碰撞体。`PhysicsRayQueryParameters3D` 要自己填 `exclude`
- 不要平移 旋转 缩放 `CollisionShape3D`，会失去物理引擎的内部优化，改形状本身的尺寸
- 三角网碰撞 `ConcavePolygonShape3D` 只能用在静态体，角色与刚体用基本形状或凸包
- `PhysicsBody3D` 只认直接子级的 `CollisionShape3D`
- 角色在斜坡抖动或飞出：先看 `floor_snap_length`，再看是否在 `_process` 里移动
- 高刷新率下物理对象的画面抖动：开 `physics/common/physics_interpolation`，瞬移后调 `reset_physics_interpolation()`
- 阴影缺失或漂浮：`Light3D.shadow_normal_bias` 先于 `shadow_bias` 调。`DirectionalLight3D.directional_shadow_max_distance` 设成场景需要的值，越小越清晰越快
- 薄面片不投影或漏光：`GeometryInstance3D.cast_shadow` 选双面
- 灯上不勾 `shadow_enabled` 默认没有阴影。定位灯阴影共用一张图集，数量多时按 `rendering/lights_and_shadows/positional_shadow/atlas_quadrant_0_subdiv` 等分配
- 光照图烘焙时隐藏灯无效，要把灯的 `light_bake_mode` 设为 Disabled
- 导入场景用菜单生成的 UV2 会在重载后丢失，在导入面板里设 Light Baking 为 Static Lightmaps
- SDFGI 对已烘的静态网格修改后要相机走远再走近才刷新
- `Environment.glow_enabled` 只对亮度超过 `glow_hdr_threshold`（默认 1.0）的像素生效，暗部要加 `glow_bloom`，Mobile 把阈值降到 0.9
- 在 `_ready()` 里立刻取导航路径可能为空，等地图第一次同步

## 参考

- [references/rendering-lighting.md](references/rendering-lighting.md) 渲染器差异 灯 阴影 GI 烘焙
- [references/import-and-levels.md](references/import-and-levels.md) 导入 GridMap CSG 继承场景
- [references/culling-and-instancing.md](references/culling-and-instancing.md) LOD 遮挡 MultiMesh Decal
- [references/skeleton-modifiers.md](references/skeleton-modifiers.md) 骨骼修改器与版本
- https://docs.godotengine.org/en/stable/tutorials/3d/index.html
- https://docs.godotengine.org/en/stable/tutorials/physics/using_jolt_physics.html
- https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html
