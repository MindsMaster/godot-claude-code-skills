# C# 对照

SKILL.md 各节示例的 C# 写法和 C# 独有的要点。动作名缓存为 `StringName` 的规则见 godot-csharp。

## 定义动作

```csharp
public partial class Mover : CharacterBody2D
{
    private const float Speed = 220.0f;
    private static readonly StringName MoveLeft = "move_left";
    private static readonly StringName MoveRight = "move_right";
    private static readonly StringName MoveUp = "move_up";
    private static readonly StringName MoveDown = "move_down";

    public override void _PhysicsProcess(double delta)
    {
        Velocity = Input.GetVector(MoveLeft, MoveRight, MoveUp, MoveDown) * Speed;
        MoveAndSlide();
    }
}
```

## 输入缓冲

```csharp
public partial class Jumper : CharacterBody2D
{
    private const long BufferTicks = 6;
    private const float JumpSpeed = -420.0f;
    private static readonly StringName Jump = "jump";

    private long _jumpPressedTick = -1000;

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed(Jump))
        {
            _jumpPressedTick = (long)Engine.GetPhysicsFrames();
        }
    }

    public override void _PhysicsProcess(double delta)
    {
        Vector2 velocity = Velocity;
        if (!IsOnFloor())
        {
            velocity += GetGravity() * (float)delta;
        }
        else if ((long)Engine.GetPhysicsFrames() - _jumpPressedTick <= BufferTicks)
        {
            velocity.Y = JumpSpeed;
            _jumpPressedTick = -1000;
        }
        Velocity = velocity;
        MoveAndSlide();
    }
}
```

- `Engine.GetPhysicsFrames()` 返回 `ulong`，和负初值相减前转 `long`

## 改键

```csharp
public partial class Keybinds : Node
{
    private const string SavePath = "user://keybinds.cfg";

    public void Rebind(StringName action, InputEventKey key)
    {
        Apply(action, key);
        var cfg = new ConfigFile();
        cfg.Load(SavePath);
        cfg.SetValue("keys", action.ToString(), (long)key.PhysicalKeycode);
        cfg.Save(SavePath);
    }

    public void LoadSaved(IEnumerable<StringName> actions)
    {
        var cfg = new ConfigFile();
        if (cfg.Load(SavePath) != Error.Ok)
        {
            return;
        }
        foreach (StringName action in actions)
        {
            if (cfg.HasSectionKey("keys", action.ToString()))
            {
                var key = new InputEventKey();
                key.PhysicalKeycode = (Key)cfg.GetValue("keys", action.ToString()).AsInt64();
                Apply(action, key);
            }
        }
    }

    private static void Apply(StringName action, InputEventKey key)
    {
        foreach (InputEvent old in InputMap.ActionGetEvents(action))
        {
            if (old is InputEventKey)
            {
                InputMap.ActionEraseEvent(action, old);
            }
        }
        InputMap.ActionAddEvent(action, key);
    }
}
```

- `ConfigFile` 存 `Key` 枚举要先转 `long`，读回用 `AsInt64()` 再转 `Key`
