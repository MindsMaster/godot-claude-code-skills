# C# 对照

SKILL.md 各节示例的 C# 写法。通用的 C# 规则见 godot-csharp。

## CharacterBody2D

```csharp
public partial class Platformer : CharacterBody2D
{
    private const float Speed = 160.0f;
    private const float Jump = -320.0f;

    public override void _PhysicsProcess(double delta)
    {
        Vector2 velocity = Velocity;
        if (!IsOnFloor())
        {
            velocity += GetGravity() * (float)delta;
        }
        else if (Input.IsActionJustPressed("jump"))
        {
            velocity.Y = Jump;
        }
        velocity.X = Input.GetAxis("left", "right") * Speed;
        Velocity = velocity;
        MoveAndSlide();
    }
}

public partial class TopDown : CharacterBody2D
{
    public override void _PhysicsProcess(double delta)
    {
        Velocity = Input.GetVector("left", "right", "up", "down") * 120.0f;
        MoveAndSlide();
    }
}
```

- `CharacterBody2D.Velocity` 是结构体属性，不能直接改 X，取副本改完整体赋回
- `delta` 是 double，与 float 相乘先转换

## Area2D

```csharp
public partial class Pickup : Area2D
{
    [Signal] public delegate void CollectedEventHandler(Node2D by);

    private CollisionShape2D _shape;

    public override void _Ready()
    {
        _shape = GetNode<CollisionShape2D>("CollisionShape2D");
        BodyEntered += OnBodyEntered;
    }

    private void OnBodyEntered(Node2D body)
    {
        EmitSignal(SignalName.Collected, body);
        _shape.SetDeferred(CollisionShape2D.PropertyName.Disabled, true);
    }
}
```

- SetDeferred 的属性名用 `PropertyName` 常量，不手写字符串

## 射线与空间查询

```csharp
public partial class GroundCheck : CharacterBody2D
{
    private RayCast2D _ground;

    public override void _Ready()
    {
        _ground = GetNode<RayCast2D>("GroundProbe");
    }

    public override void _PhysicsProcess(double delta)
    {
        if (_ground.IsColliding())
        {
            Vector2 point = _ground.GetCollisionPoint();
            GD.Print(point, _ground.GetCollider());
        }
    }
}

public partial class Shooter : CharacterBody2D
{
    private const uint Mask = (1u << 0) | (1u << 2);

    public override void _PhysicsProcess(double delta)
    {
        if (!Input.IsActionJustPressed("fire"))
        {
            return;
        }
        var query = PhysicsRayQueryParameters2D.Create(
            GlobalPosition, GetGlobalMousePosition(), Mask, new Godot.Collections.Array<Rid> { GetRid() });
        Godot.Collections.Dictionary hit = GetWorld2D().DirectSpaceState.IntersectRay(query);
        if (hit.Count > 0)
        {
            Vector2 point = hit["position"].AsVector2();
            GD.Print(point, hit["collider"]);
        }
    }
}
```

- mask 参数是 `uint`，第 n 层是 `1u << (n - 1)`
- `exclude` 是 `Array<Rid>`
- 结果字典的值是 Variant，用 `AsVector2()` 等转换
