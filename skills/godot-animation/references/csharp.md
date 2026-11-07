# C# 对照

SKILL.md 各节示例的 C# 写法。通用的 C# 规则见 godot-csharp。

## AnimationPlayer

```csharp
public partial class Attacker : CharacterBody2D
{
    private AnimationPlayer _anim;

    public override void _Ready()
    {
        _anim = GetNode<AnimationPlayer>("AnimationPlayer");
        _anim.AnimationFinished += OnAnimationFinished;
        _anim.Play("attack");
    }

    private void OnAnimationFinished(StringName animName)
    {
        if (animName == "attack")
        {
            _anim.Play("idle");
        }
    }
}
```

- 动画名参数是 `StringName`，`string` 隐式转换，每帧调用时缓存成 `static readonly StringName`

## AnimationTree

```csharp
public partial class Locomotion : CharacterBody2D
{
    private static readonly StringName BlendPath = "parameters/Locomotion/Move/blend_position";
    private static readonly StringName AttackRequest = "parameters/Attack/request";

    private AnimationTree _tree;
    private AnimationNodeStateMachinePlayback _state;

    public override void _Ready()
    {
        _tree = GetNode<AnimationTree>("AnimationTree");
        _state = _tree.Get("parameters/Locomotion/playback").As<AnimationNodeStateMachinePlayback>();
    }

    public override void _PhysicsProcess(double delta)
    {
        _tree.Set(BlendPath, Velocity / 200.0f);
        if (Input.IsActionJustPressed("attack"))
        {
            _tree.Set(AttackRequest, (int)AnimationNodeOneShot.OneShotRequest.Fire);
        }
        if (IsOnFloor())
        {
            _state.Travel("Ground");
        }
    }
}
```

- 参数路径用 Get 与 Set 读写，取值后 `As<T>()` 转类型
- OneShot 请求是枚举，写入前转 `int`

## Tween

```csharp
public partial class PopButton : Control
{
    private Tween _tween;

    public void Pop()
    {
        _tween?.Kill();
        PivotOffset = Size / 2.0f;
        _tween = CreateTween();
        _tween.TweenProperty(this, "scale", Vector2.One * 1.2f, 0.08).SetTrans(Tween.TransitionType.Back).SetEase(Tween.EaseType.Out);
        _tween.TweenProperty(this, "scale", Vector2.One, 0.12);
    }
}

public partial class Cutscene : Node2D
{
    [Signal] public delegate void DialogueClosedEventHandler();

    public void Play()
    {
        Tween tween = CreateTween();
        tween.TweenProperty(this, "position:x", 600.0f, 1.5);
        tween.TweenCallback(Callable.From(() => GD.Print("Hello")));
        tween.TweenAwait(new Signal(this, SignalName.DialogueClosed)).SetTimeout(30.0);
        tween.TweenProperty(this, "position:x", 0.0f, 1.5);
    }
}
```

- 属性路径用 snake_case 字符串，不用 C# 属性名
- 终值与属性类型不同会报 Type mismatch，`int` 与 `float` 自动互转
- 等 Tween 结束：`await ToSignal(tween, Tween.SignalName.Finished)`

## 命中闪白

```csharp
public partial class HitFlash : Sprite2D
{
    private static readonly StringName Flash = "flash";

    private Tween _tween;

    public void Play()
    {
        _tween?.Kill();
        SetInstanceShaderParameter(Flash, 1.0f);
        _tween = CreateTween();
        _tween.TweenProperty(this, "instance_shader_parameters/flash", 0.0f, 0.12);
    }
}
```
