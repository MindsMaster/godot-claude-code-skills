# 3D 物理细节

CharacterBody3D 属性、形状选择、Jolt 差异、范围检测、ShapeCast3D、Area3D 分层、物理插值。

## CharacterBody3D 属性

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

## 形状选择

| 物体 | 形状 | 备注 |
|---|---|---|
| 角色 刚体 | `CapsuleShape3D` `BoxShape3D` `SphereShape3D` `CylinderShape3D` | 行为最稳 性能最好。大量角色挤在一起时圆柱最贵，见 godot-performance 的 crowd-characters.md |
| 简单动态物体 | `ConvexPolygonShape3D` | 编辑器 Mesh 菜单生成 单个用 Quickhull 多个用 V-HACD |
| 静态关卡 | `ConcavePolygonShape3D` | 只能放 `StaticBody3D` 或 `AnimatableBody3D` 没有体积 内外都能放东西 |
| 地形 | `HeightMapShape3D` | |
| 无限地面 | `WorldBoundaryShape3D` | Jolt 下有效尺寸更小 由 `physics/jolt_physics_3d/limits/world_boundary_shape_size` 控制 |

- 静态体只放一个未变换的形状时，粗检测可直接丢弃不活动物体
- 形状多或带旋转缩放会走更慢的细检测

## Jolt 与 GodotPhysics3D 差异

`physics/3d/physics_engine` 设为 `Jolt Physics`，`DEFAULT` 在 4.7 仍等于 GodotPhysics3D。

| 项 | Jolt 行为 | 设置 |
|---|---|---|
| 关节软限制 | `PinJoint3D` 的 `bias` `damping` `impulse_clamp` 等软限制类属性不支持，设非默认值警告 | |
| 只设一个物体的关节 | 默认当 `node_b`，`node_a` 为世界 | `physics/jolt_physics_3d/joints/world_node` |
| 形状边距 | `Shape3D.margin` 是上限，实际按最小 AABB 轴长乘比例 | `physics/jolt_physics_3d/collisions/collision_margin_fraction` |
| 穿插恢复 | Baumgarte 稳定只作用于位置，不弹飞，解开更慢 | `physics/jolt_physics_3d/simulation/baumgarte_stabilization_factor` |
| 射线 `face_index` | 默认 -1，开启后三角网碰撞内存多约 25% | `physics/jolt_physics_3d/queries/enable_ray_cast_face_index` |
| kinematic 刚体接触 | 默认不报与 kinematic 和静态体的接触 | `physics/jolt_physics_3d/simulation/generate_all_kinematic_contacts` |
| 休眠 | | `physics/jolt_physics_3d/simulation/allow_sleep` |
| 无限地面 | `WorldBoundaryShape3D` 有效尺寸更小 | `physics/jolt_physics_3d/limits/world_boundary_shape_size` |

- `HingeJoint3D`、`SliderJoint3D`、`ConeTwistJoint3D`、`Generic6DOFJoint3D` 的软限制同样不支持
- 老项目兼容关节：`world_node` 改成 `node_b` 代表世界
- 小物体碰撞法线怪异时先调边距比例
- `PhysicsDirectBodyState3D.get_contact_impulse()` 是预估值
- 预估值只在两个物体不与别的物体接触时准确
- `physics/3d/run_on_separate_thread` 在 Jolt 下线程安全，标为实验性
- 开启后错误信息里节点显示为 `<unknown>`
- 它只挪走物理步，`move_and_slide()` 与空间查询仍在主线程调
- 大量角色拥挤见 godot-performance 的 crowd-characters.md
- 旧 Godot Jolt 扩展的设置搬到 `physics/jolt_physics_3d/` 下
- 扩展里的 Jolt 关节节点没有进入内置版本

## 范围检测

```gdscript
extends Node3D

func bodies_in_radius(center: Vector3, radius: float, mask: int) -> Array[Node3D]:
	var shape: SphereShape3D = SphereShape3D.new()
	shape.radius = radius
	var query: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()
	query.shape = shape
	query.transform = Transform3D(Basis.IDENTITY, center)
	query.collision_mask = mask
	var found: Array[Node3D] = []
	for hit: Dictionary in get_world_3d().direct_space_state.intersect_shape(query, 32):
		var body: Node3D = hit.collider as Node3D
		if body != null:
			found.append(body)
	return found
```

```csharp
public partial class AreaQuery : Node3D
{
    public List<Node3D> BodiesInRadius(Vector3 center, float radius, uint mask)
    {
        var shape = new SphereShape3D { Radius = radius };
        var query = new PhysicsShapeQueryParameters3D
        {
            Shape = shape,
            Transform = new Transform3D(Basis.Identity, center),
            CollisionMask = mask,
        };
        var found = new List<Node3D>();
        foreach (Godot.Collections.Dictionary hit in GetWorld3D().DirectSpaceState.IntersectShape(query, 32))
        {
            if (hit["collider"].AsGodotObject() is Node3D body)
            {
                found.Add(body);
            }
        }
        return found;
    }
}
```

- `intersect_shape()` 第二个参数是最大结果数，默认 32
- 只问有没有，用 `ShapeCast3D` 或 `Area3D` 的重叠查询

## ShapeCast3D

台阶与悬崖检测：

```gdscript
extends Node3D

@onready var _ground_probe: ShapeCast3D = $GroundProbe

func has_ground_ahead() -> bool:
	_ground_probe.force_shapecast_update()
	return _ground_probe.is_colliding()
```

```csharp
public partial class LedgeCheck : Node3D
{
    private ShapeCast3D _groundProbe;

    public override void _Ready()
    {
        _groundProbe = GetNode<ShapeCast3D>("GroundProbe");
    }

    public bool HasGroundAhead()
    {
        _groundProbe.ForceShapecastUpdate();
        return _groundProbe.IsColliding();
    }
}
```

- `collision_mask` 默认只有第 1 层，`max_results` 默认 32
- 结果用 `get_collision_count()` 与 `get_collider()` 取
- `margin` 越大检测越稳，精度越低

## Area3D 分层

- 判定盒：layer 放自己的类别层，mask 勾要命中的身体层
- 拾取与触发：触发器只勾 mask，被检测者的 layer 要在其中
- `body_entered` 对 `PhysicsBody3D` `SoftBody3D` `GridMap` 发
- `GridMap` 的 `MeshLibrary` 要有碰撞形状
- `area_entered` 对别的 `Area3D` 发
- 开关 `CollisionShape3D.disabled` 用 `set_deferred`

## 物理插值

| 项 | 说明 |
|---|---|
| `physics/common/physics_interpolation` | 两个物理帧之间插值画面，只在启动时读取 |
| `SceneTree.physics_interpolation` | 运行时开关 |
| `reset_physics_interpolation()` | 瞬移后调，否则出现拖影 |
| `Node.physics_interpolation_mode` | 对单个子树关闭，如鼠标驱动的相机枢轴 |

- 移动和游戏逻辑都要在 `_physics_process()`
