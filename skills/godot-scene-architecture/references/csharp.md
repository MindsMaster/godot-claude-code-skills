# C# 对照

SKILL.md 各节示例的 C# 写法和 C# 独有的要点。命名映射、枚举 Enum 后缀、源码生成器、`StringName` 缓存见 godot-csharp。

## 实例化

```csharp
public partial class Bullet : Area2D
{
    public Vector2 Direction { get; set; } = Vector2.Right;
    public float Speed { get; set; } = 400.0f;

    public override void _PhysicsProcess(double delta)
    {
        Position += Direction * Speed * (float)delta;
    }
}

public partial class Spawner : Node2D
{
    [Export] public PackedScene BulletScene { get; set; }

    public void Fire(Vector2 dir)
    {
        var bullet = BulletScene.Instantiate<Bullet>();
        bullet.Direction = dir;
        GetParent().AddChild(bullet);
        bullet.GlobalPosition = GlobalPosition;
    }
}
```

- `Instantiate<T>()` 根节点类型不符时抛 `InvalidCastException`

## 节点引用

```csharp
public partial class Turret : Node2D
{
    [Export] public Node2D Target { get; set; }
    [Export(PropertyHint.NodePathValidTypes, "Marker2D")] public NodePath SpawnPath { get; set; }

    private Label _score;
    private Sprite2D _sprite;
    private Marker2D _spawn;

    public override void _Ready()
    {
        _score = GetNode<Label>("%ScoreLabel");
        _sprite = GetNode<Sprite2D>("Sprite2D");
        _spawn = GetNode<Marker2D>(SpawnPath);
    }

    public override void _Process(double delta)
    {
        if (Target != null)
        {
            LookAt(Target.GlobalPosition);
        }
    }
}
```

| GDScript | C# |
|---|---|
| `@onready var x: Label = %X` | `_Ready` 里 `GetNode<Label>("%X")` 存私有字段 |
| `$Sprite2D` | `GetNode<Sprite2D>("Sprite2D")` |
| `@export_node_path("Marker2D")` | `[Export(PropertyHint.NodePathValidTypes, "Marker2D")]` |
| `get_node_or_null` | `GetNodeOrNull<T>` |

- `GetNode<T>` 类型不符抛 `InvalidCastException`

## 通信

```csharp
public partial class Health : Node
{
    [Signal] public delegate void ChangedEventHandler(int current, int maximum);
    [Signal] public delegate void DiedEventHandler();

    [Export] public int Maximum { get; set; } = 100;

    public int Current { get; private set; }

    public override void _Ready()
    {
        Current = Maximum;
    }

    public void Damage(int amount)
    {
        Current = Math.Max(Current - amount, 0);
        EmitSignal(SignalName.Changed, Current, Maximum);
        if (Current == 0)
        {
            EmitSignal(SignalName.Died);
        }
    }
}

public partial class Player : CharacterBody2D
{
    private Health _health;

    public override void _Ready()
    {
        _health = GetNode<Health>("Health");
        _health.Died += QueueFree;
    }
}
```

- 信号委托名以 EventHandler 结尾，生成的事件名去掉后缀
- 字段初始化器读 `[Export]` 属性得到默认值，Inspector 的值在 `_Ready` 里读
- 连接与断开的规则见 godot-csharp

## 分组

```csharp
public partial class Guard : Node2D
{
    public void Alert(Vector2 at)
    {
        LookAt(at);
    }
}

public partial class Alarm : Node2D
{
    public void RaiseAlarm()
    {
        GetTree().CallGroup("guards", Guard.MethodName.Alert, GlobalPosition);
    }
}
```

- `SceneTree.CallGroup` 按注册名找方法，C# 方法注册的是 C# 原名
- 方法名用 `MethodName` 常量，拼错在编译期报

## Autoload

```csharp
public partial class Settings : Node
{
    public static Settings Instance { get; private set; }

    public override void _EnterTree()
    {
        Instance = this;
    }
}
```

- C# 不读 `*` 生成的全局名，用静态 Instance 属性访问
- 仍要在项目设置的 Autoload 页注册，脚本路径指向 `.cs`

## 组合与继承

```csharp
public partial class HurtBox : Area2D
{
    [Export] public Health Health { get; set; }

    public override void _Ready()
    {
        AreaEntered += OnAreaEntered;
    }

    private void OnAreaEntered(Area2D area)
    {
        if (area is HitBox hit)
        {
            Health.Damage(hit.Damage);
        }
    }
}

public partial class HitBox : Area2D
{
    [Export] public int Damage { get; set; } = 1;
}
```

## 暂停

```csharp
public partial class PauseMenu : Control
{
    public override void _Ready()
    {
        ProcessMode = ProcessModeEnum.Always;
        Hide();
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed("pause"))
        {
            GetTree().Paused = !GetTree().Paused;
            Visible = GetTree().Paused;
            GetViewport().SetInputAsHandled();
        }
    }
}
```
