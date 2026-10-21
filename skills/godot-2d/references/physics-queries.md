# 2D 物理查询细节

SKILL.md 里的 `RayCast2D` 与 `intersect_ray` 不够用时读这里：范围与点查询、`ShapeCast2D`、C# 写法、结果字段。

## 节点探测

| 属性 | 默认 | 说明 |
|---|---|---|
| `enabled` | true | false 时不自动更新，`force_raycast_update` 仍然有效 |
| `target_position` | `Vector2(0, 50)` | 相对节点自身位置 |
| `collision_mask` | 1 | 只扫第 1 层 |
| `collide_with_areas` | false | 要打 `Area2D` 必须开 |
| `collide_with_bodies` | true | |
| `exclude_parent` | true | 只对父节点是 `CollisionObject2D` 时有效 |
| `hit_from_inside` | false | 只有 `RayCast2D` 有，起点在形状内时命中，法线为零向量 |

其他要排除的对象用 `add_exception(node)`，`clear_exceptions` 清空。

`ShapeCast2D` 多了 `shape`、`max_results`（默认 32）、`margin`。结果用 `get_collision_count`、`get_collider(i)`、`get_collision_point(i)`、`get_closest_collision_safe_fraction`。

<!-- check: extends CharacterBody2D -->
```gdscript
@onready var _ledge: ShapeCast2D = $LedgeProbe

func has_ground_ahead(direction: float) -> bool:
	_ledge.position.x = absf(_ledge.position.x) * direction
	_ledge.force_shapecast_update()
	return _ledge.is_colliding()
```

`target_position` 设为 `Vector2(0, 0)` 再 `force_shapecast_update` 就是当场的重叠检测，不必等 `Area2D` 的下一个物理步。

## 范围与点查询

<!-- check: extends Node2D -->
```gdscript
func enemies_in_radius(center: Vector2, radius: float, mask: int) -> Array[Node2D]:
	var circle := CircleShape2D.new()
	circle.radius = radius
	var query := PhysicsShapeQueryParameters2D.new()
	query.shape = circle
	query.transform = Transform2D(0.0, center)
	query.collision_mask = mask
	query.collide_with_areas = true
	var found: Array[Node2D] = []
	for hit: Dictionary in get_world_2d().direct_space_state.intersect_shape(query, 16):
		var node := hit.collider as Node2D
		if node != null:
			found.append(node)
	return found
```

<!-- check: extends Node2D -->
```gdscript
func clickable_at(point: Vector2) -> Array[Dictionary]:
	var query := PhysicsPointQueryParameters2D.new()
	query.position = point
	query.collide_with_areas = true
	return get_world_2d().direct_space_state.intersect_point(query)
```

- `transform` 与 `position` 都是全局坐标。
- `intersect_point` 不碰 `ConcavePolygonShape2D` 和 Segments 模式的 `CollisionPolygon2D`，它们不是实心形状。
- `canvas_instance_id` 为 0 时点查询只查 Viewport 默认画布层，放在 `CanvasLayer` 里的物理对象要填该层的 `get_instance_id()`。
- `intersect_shape` 带 `motion` 与 `margin`；要沿方向扫过去取最近距离用 `cast_motion`，要两个形状的接触点用 `collide_shape` 与 `get_rest_info`。
- 只想知道某个 `Area2D` 里有谁，直接用它的 `get_overlapping_bodies` 和信号，不必再查空间。

## 结果字段

| 方法 | 返回 | 字段 |
|---|---|---|
| `intersect_ray` | `Dictionary`，未命中为空 | `position` `normal` `collider` `collider_id` `rid` `shape` |
| `intersect_point` | `Array[Dictionary]` | `collider` `collider_id` `rid` `shape` |
| `intersect_shape` | `Array[Dictionary]` | `collider` `collider_id` `rid` `shape` |

## C#

```csharp
using Godot;
using Godot.Collections;

public partial class Shooter : CharacterBody2D
{
    private const uint Mask = (1u << 0) | (1u << 2);

    public override void _PhysicsProcess(double delta)
    {
        if (!Input.IsActionJustPressed("fire"))
        {
            return;
        }

        PhysicsDirectSpaceState2D space = GetWorld2D().DirectSpaceState;
        PhysicsRayQueryParameters2D query = PhysicsRayQueryParameters2D.Create(
            GlobalPosition, GetGlobalMousePosition(), Mask, new Array<Rid> { GetRid() });
        Dictionary hit = space.IntersectRay(query);
        if (hit.Count > 0)
        {
            Vector2 point = (Vector2)hit["position"];
            GD.Print(point, hit["collider"]);
        }
    }
}
```

`intersect_shape` 与 `intersect_point` 在 C# 返回 `Array<Dictionary>`。mask 参数是 `uint`，第 n 层是 `1u << (n - 1)`。
