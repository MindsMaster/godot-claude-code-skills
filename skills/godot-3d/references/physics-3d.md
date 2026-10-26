# 3D 物理细节

SKILL.md 里的角色移动与查询的补充：形状选择，Jolt 差异，C# 查询，范围检测。

## 形状选择

| 物体 | 形状 | 备注 |
|---|---|---|
| 角色 刚体 | `CapsuleShape3D` `BoxShape3D` `SphereShape3D` `CylinderShape3D` | 行为最稳 性能最好。大量角色挤在一起时圆柱最贵，见 godot-performance 的 crowd-characters.md |
| 简单动态物体 | `ConvexPolygonShape3D` | 编辑器 Mesh 菜单生成 单个用 Quickhull 多个用 V-HACD |
| 静态关卡 | `ConcavePolygonShape3D` | 只能放 `StaticBody3D` 或 `AnimatableBody3D` 没有体积 内外都能放东西 |
| 地形 | `HeightMapShape3D` | |
| 无限地面 | `WorldBoundaryShape3D` | Jolt 下有效尺寸更小 由 `physics/jolt_physics_3d/limits/world_boundary_shape_size` 控制 |

一个静态体只放一个未变换的形状时，粗检测阶段可以直接丢弃不活动的物体。形状多或带旋转缩放会走更慢的细检测。

## Jolt 与 GodotPhysics3D 差异

Jolt 通过 `physics/3d/physics_engine` 选择，值为 `Jolt Physics`。`DEFAULT` 在 4.7 仍等于 GodotPhysics3D。

- 关节：`PinJoint3D` 的 `bias` `damping` `impulse_clamp`，`HingeJoint3D` 的 `bias` `softness` `relaxation`，`SliderJoint3D` 与 `ConeTwistJoint3D` `Generic6DOFJoint3D` 的软限制类属性不支持，设非默认值会警告
- 只设一个物体的关节：Godot Physics 把物体当 `node_a`，Jolt 默认当 `node_b`，`node_a` 为世界。老项目要兼容时把 `physics/jolt_physics_3d/joints/world_node` 改成 `node_b` 代表世界
- 形状边距：`Shape3D.margin` 在 Jolt 里是上限，实际值是最小 AABB 轴长乘 `physics/jolt_physics_3d/collisions/collision_margin_fraction`。小物体的碰撞法线怪异时先调这项
- 穿插恢复：Baumgarte 稳定只作用于位置，不会弹飞，但解开穿插更慢 `physics/jolt_physics_3d/simulation/baumgarte_stabilization_factor`
- 射线 `face_index` 默认 -1，开 `physics/jolt_physics_3d/queries/enable_ray_cast_face_index` 后三角网碰撞内存多约 25%
- 冻结为 kinematic 的 `RigidBody3D` 默认不报与其他 kinematic 和静态体的接触，开 `physics/jolt_physics_3d/simulation/generate_all_kinematic_contacts`，大量或大形状叠在复杂静态几何上时开销大
- `PhysicsDirectBodyState3D.get_contact_impulse()` 是预估值，只在两个物体不与别的物体接触时准确
- 休眠：`physics/jolt_physics_3d/simulation/allow_sleep`
- 线程：`physics/3d/run_on_separate_thread` 在 Jolt 下有线程安全 但标为实验性，开启后错误信息里的节点显示为 `<unknown>`。它只把物理步挪走，`move_and_slide()` 与空间查询仍只能在主线程调，大量角色拥挤见 godot-performance 的 crowd-characters.md
- 旧 Godot Jolt 扩展的设置路径已搬家 `physics/jolt_physics_3d/` 下，扩展里的 Jolt 关节节点没有进入内置版本

## C# 查询

```csharp
using Godot;

public partial class Picker : Camera3D
{
    private const float RayLength = 1000.0f;

    public Godot.Collections.Dictionary Pick(Vector2 mousePosition)
    {
        PhysicsDirectSpaceState3D space = GetWorld3D().DirectSpaceState;
        Vector3 from = ProjectRayOrigin(mousePosition);
        Vector3 to = from + ProjectRayNormal(mousePosition) * RayLength;
        PhysicsRayQueryParameters3D query = PhysicsRayQueryParameters3D.Create(from, to, 1u << 2);
        query.CollideWithAreas = true;
        return space.IntersectRay(query);
    }
}
```

`PhysicsRayQueryParameters3D.Create` 的第三个参数是 `uint` 位掩码，第 n 层是 `1u << (n - 1)`。结果字典的键是小写字符串，如 `result["position"]`。没命中时字典为空。

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

`intersect_shape()` 第二个参数是最大结果数，默认 32。只想知道有没有，用 `ShapeCast3D` 或 `Area3D` 的重叠查询。

## ShapeCast3D 台阶与悬崖检测

```gdscript
extends Node3D

@onready var _ground_probe: ShapeCast3D = $GroundProbe

func has_ground_ahead() -> bool:
	_ground_probe.force_shapecast_update()
	return _ground_probe.is_colliding()
```

`ShapeCast3D` 的 `collision_mask` 默认只有第 1 层，`max_results` 默认 32，结果用 `get_collision_count()` 与 `get_collider()` 取。`margin` 越大碰撞检测越稳，精度越低。

## 碰撞层的 Area3D 用法

- 判定盒类 `Area3D`：layer 放自己的类别层，mask 勾要命中的身体层
- 拾取与触发：触发器的 layer 不勾，只勾 mask；被检测者的 layer 要在触发器 mask 里
- `body_entered` 对 `PhysicsBody3D` `SoftBody3D` `GridMap` 发，`GridMap` 的 `MeshLibrary` 要有碰撞形状。`area_entered` 对别的 `Area3D` 发
- 开关 `CollisionShape3D.disabled` 用 `set_deferred("disabled", true)`，在物理回调里直接改不安全

## 物理插值

`physics/common/physics_interpolation` 开启后，画面在两个物理帧之间插值。该设置只在启动时读取，运行时开关用 `SceneTree.physics_interpolation`。要求移动和游戏逻辑都在 `_physics_process()`。瞬移节点后调 `reset_physics_interpolation()`，否则出现拖影。`Node.physics_interpolation_mode` 可对单个子树关闭，例如鼠标直接驱动的相机枢轴。

## 参考

- https://docs.godotengine.org/en/stable/tutorials/physics/using_jolt_physics.html
- https://docs.godotengine.org/en/stable/tutorials/physics/collision_shapes_3d.html
- https://docs.godotengine.org/en/stable/tutorials/physics/ray-casting.html
- https://docs.godotengine.org/en/stable/tutorials/physics/interpolation/physics_interpolation_quick_start_guide.html
