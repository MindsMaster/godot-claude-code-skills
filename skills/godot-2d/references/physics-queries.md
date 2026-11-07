# 2D 物理查询

RayCast2D 与 ShapeCast2D 节点属性、范围与点查询、结果字段。

## 节点探测

| 属性 | 默认 | 说明 |
|---|---|---|
| `enabled` | true | false 时不自动更新，`force_raycast_update` 仍有效 |
| `target_position` | `Vector2(0, 50)` | 相对节点自身位置 |
| `collision_mask` | 1 | 只扫第 1 层 |
| `collide_with_areas` | false | 要打 `Area2D` 必须开 |
| `collide_with_bodies` | true | |
| `exclude_parent` | true | 只对父节点是 `CollisionObject2D` 时有效 |
| `hit_from_inside` | false | 只有 `RayCast2D` 有，起点在形状内时命中，法线为零向量 |

- 其他要排除的对象用 `add_exception(node)`，`clear_exceptions` 清空
- `ShapeCast2D` 多了 `shape`、`max_results` 默认 32、`margin`
- ShapeCast2D 结果：`get_collision_count`、`get_collider(i)`、`get_collision_point(i)`
- 安全移动比例：`get_closest_collision_safe_fraction`

<!-- check: extends CharacterBody2D -->
```gdscript
@onready var _ledge: ShapeCast2D = $LedgeProbe

func has_ground_ahead(direction: float) -> bool:
	_ledge.position.x = absf(_ledge.position.x) * direction
	_ledge.force_shapecast_update()
	return _ledge.is_colliding()
```

```csharp
public partial class LedgeWalker : CharacterBody2D
{
    private ShapeCast2D _ledge;

    public override void _Ready()
    {
        _ledge = GetNode<ShapeCast2D>("LedgeProbe");
    }

    public bool HasGroundAhead(float direction)
    {
        Vector2 position = _ledge.Position;
        position.X = Mathf.Abs(position.X) * direction;
        _ledge.Position = position;
        _ledge.ForceShapecastUpdate();
        return _ledge.IsColliding();
    }
}
```

- `target_position` 设 `Vector2(0, 0)` 再 `force_shapecast_update` 是当场重叠检测
- 不必等 `Area2D` 的下一个物理步

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

```csharp
public partial class RadiusQuery : Node2D
{
    public List<Node2D> EnemiesInRadius(Vector2 center, float radius, uint mask)
    {
        var circle = new CircleShape2D { Radius = radius };
        var query = new PhysicsShapeQueryParameters2D
        {
            Shape = circle,
            Transform = new Transform2D(0.0f, center),
            CollisionMask = mask,
            CollideWithAreas = true,
        };
        var found = new List<Node2D>();
        foreach (Godot.Collections.Dictionary hit in GetWorld2D().DirectSpaceState.IntersectShape(query, 16))
        {
            if (hit["collider"].AsGodotObject() is Node2D node)
            {
                found.Add(node);
            }
        }
        return found;
    }
}
```

<!-- check: extends Node2D -->
```gdscript
func clickable_at(point: Vector2) -> Array[Dictionary]:
	var query := PhysicsPointQueryParameters2D.new()
	query.position = point
	query.collide_with_areas = true
	return get_world_2d().direct_space_state.intersect_point(query)
```

```csharp
public partial class PointQuery : Node2D
{
    public Godot.Collections.Array<Godot.Collections.Dictionary> ClickableAt(Vector2 point)
    {
        var query = new PhysicsPointQueryParameters2D { Position = point, CollideWithAreas = true };
        return GetWorld2D().DirectSpaceState.IntersectPoint(query);
    }
}
```

- `transform` 与 `position` 都是全局坐标
- `intersect_point` 不碰 `ConcavePolygonShape2D` 和 Segments 模式的 `CollisionPolygon2D`
- 点查询的 `canvas_instance_id` 为 0 时只查默认画布层
- CanvasLayer 里的物理对象，`canvas_instance_id` 填该层的 `get_instance_id()`
- 只问某个 `Area2D` 里有谁，用它的 `get_overlapping_bodies` 和信号

| 需求 | 方法 |
|---|---|
| 形状带位移重叠 | `intersect_shape` 的 `motion` 与 `margin` |
| 沿方向扫过去取最近距离 | `cast_motion` |
| 两个形状的接触点 | `collide_shape`、`get_rest_info` |

## 结果字段

| 方法 | 返回 | 字段 |
|---|---|---|
| `intersect_ray` | `Dictionary`，未命中为空 | `position` `normal` `collider` `collider_id` `rid` `shape` |
| `intersect_point` | `Array[Dictionary]` | `collider` `collider_id` `rid` `shape` |
| `intersect_shape` | `Array[Dictionary]` | `collider` `collider_id` `rid` `shape` |

- C# 中后两者返回 `Array<Dictionary>`，mask 参数是 `uint`
