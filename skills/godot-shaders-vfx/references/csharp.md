# C# 对照

SKILL.md 各节示例的 C# 写法。通用的 C# 规则见 godot-csharp。

## 命中闪白

```csharp
public partial class HitFlash : Sprite2D
{
    private static readonly StringName Flash = "flash";
    private static readonly NodePath FlashPath = "instance_shader_parameters/flash";

    private Tween _tween;

    public void Hit()
    {
        _tween?.Kill();
        SetInstanceShaderParameter(Flash, 1.0f);
        _tween = CreateTween();
        _tween.TweenProperty(this, FlashPath, 0.0f, 0.15);
    }
}
```

- 字符串字面量每次调用都转成新的 `StringName` 或 `NodePath`
- 每帧调用的参数名缓存成 `static readonly`

## 2D 的 glow

```csharp
public partial class GlowSetup : Node2D
{
    public override void _Ready()
    {
        var env = new Godot.Environment
        {
            BackgroundMode = Godot.Environment.BGMode.Canvas,
            BackgroundCanvasMaxLayer = 0,
            GlowEnabled = true,
            GlowHdrThreshold = 0.8f,
        };
        var worldEnv = new WorldEnvironment { Environment = env };
        AddChild(worldEnv);
    }
}
```

- 写 `Godot.Environment`，`using System;` 时 Environment 有歧义

## 粒子

```csharp
public partial class OneShotEffect : GpuParticles3D
{
    public override void _Ready()
    {
        OneShot = true;
        Finished += QueueFree;
        Restart();
    }
}
```

- C# 类名缩写按大驼峰：GpuParticles3D、CpuParticles3D
