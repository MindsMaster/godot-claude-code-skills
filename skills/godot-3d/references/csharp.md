# C# 对照

SKILL.md 各节示例的 C# 写法。通用的 C# 规则见 godot-csharp。

## 角色移动

```csharp
public partial class Mover3D : CharacterBody3D
{
    [Export] public float Speed { get; set; } = 5.0f;
    [Export] public float JumpVelocity { get; set; } = 4.5f;

    public override void _PhysicsProcess(double delta)
    {
        Vector3 velocity = Velocity;
        if (!IsOnFloor())
        {
            velocity += GetGravity() * (float)delta;
        }
        else if (Input.IsActionJustPressed("jump"))
        {
            velocity.Y = JumpVelocity;
        }
        Vector2 input = Input.GetVector("move_left", "move_right", "move_forward", "move_back");
        Vector3 direction = GlobalBasis * new Vector3(input.X, 0.0f, input.Y);
        velocity.X = direction.X * Speed;
        velocity.Z = direction.Z * Speed;
        Velocity = velocity;
        MoveAndSlide();
    }
}
```

- `CharacterBody3D.Velocity` 是结构体属性，取副本改完整体赋回

## 碰撞层

```csharp
public partial class LayeredBody : CharacterBody3D
{
    private const uint LayerWorld = 1u << 0;
    private const uint LayerPlayer = 1u << 1;
    private const uint LayerEnemy = 1u << 2;

    [Export(PropertyHint.Layers3DPhysics)] public uint HitMask { get; set; } = LayerEnemy;

    public override void _Ready()
    {
        CollisionLayer = LayerPlayer;
        CollisionMask = LayerWorld | LayerEnemy;
    }
}
```

- 层与 mask 是 `uint`，位移写 `1u << n`
- 导出层选择器用 `PropertyHint.Layers3DPhysics`

## 空间查询

```csharp
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

- 结果字典的键是小写字符串，如 `result["position"]`，值用 `AsVector3()` 等转换
- 没命中时字典为空，判断 `Count == 0`

## 第三人称相机

```csharp
public partial class CameraRig : Node3D
{
    [Export] public float MouseSensitivity { get; set; } = 0.003f;

    private SpringArm3D _arm;

    public override void _Ready()
    {
        _arm = GetNode<SpringArm3D>("SpringArm3D");
        if (GetParent() is CollisionObject3D body)
        {
            _arm.AddExcludedObject(body.GetRid());
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event is not InputEventMouseMotion motion || Input.MouseMode != Input.MouseModeEnum.Captured)
        {
            return;
        }
        RotateY(-motion.ScreenRelative.X * MouseSensitivity);
        Vector3 rotation = _arm.Rotation;
        rotation.X = Mathf.Clamp(rotation.X - motion.ScreenRelative.Y * MouseSensitivity, -1.2f, 1.2f);
        _arm.Rotation = rotation;
    }
}
```

## 导航

```csharp
public partial class Chaser : CharacterBody3D
{
    [Export] public float Speed { get; set; } = 4.0f;

    private NavigationAgent3D _agent;

    public override void _Ready()
    {
        _agent = GetNode<NavigationAgent3D>("NavigationAgent3D");
    }

    public void GoTo(Vector3 target)
    {
        _agent.TargetPosition = target;
    }

    public override void _PhysicsProcess(double delta)
    {
        if (NavigationServer3D.MapGetIterationId(_agent.GetNavigationMap()) == 0)
        {
            return;
        }
        if (_agent.IsNavigationFinished())
        {
            return;
        }
        Vector3 next = _agent.GetNextPathPosition();
        Velocity = GlobalPosition.DirectionTo(next) * Speed;
        MoveAndSlide();
    }
}
```
