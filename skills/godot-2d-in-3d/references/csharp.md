# C# 对照

SKILL.md 各节示例的 C# 写法。通用的 C# 规则见 godot-csharp。

## Sprite3D 配置

```csharp
public partial class Character : Sprite3D
{
    public override void _Ready()
    {
        PixelSize = 1.0f / 32.0f;
        Billboard = BaseMaterial3D.BillboardModeEnum.FixedY;
        TextureFilter = BaseMaterial3D.TextureFilterEnum.Nearest;
        AlphaCut = AlphaCutMode.Discard;
        Shaded = true;
        Rect2I used = Texture.GetImage().GetUsedRect();
        Vector2 offset = Offset;
        offset.Y = used.End.Y - Texture.GetHeight() * 0.5f;
        Offset = offset;
    }
}
```

- 枚举类型名带后缀，如 BillboardModeEnum、TextureFilterEnum、AlphaCutMode
- `Sprite3D.Offset` 是结构体属性，取副本改 Y 再赋回

## 朝向翻转

```csharp
public partial class Facing : AnimatedSprite3D
{
    public void Face(float directionX)
    {
        if (directionX != 0.0f)
        {
            FlipH = directionX < 0.0f;
        }
    }
}
```

## 相机

```csharp
public partial class PixelCamera : Camera3D
{
    public override void _Ready()
    {
        Projection = ProjectionType.Orthogonal;
        Size = 360.0f * (1.0f / 32.0f);
    }
}
```

## 地面阴影

```csharp
public partial class BlobShadow : Sprite3D
{
    public override void _Ready()
    {
        var gradient = new Gradient();
        gradient.SetColor(0, new Color(0.0f, 0.0f, 0.0f, 0.8f));
        gradient.SetColor(1, new Color(0.0f, 0.0f, 0.0f, 0.0f));
        Texture = new GradientTexture2D
        {
            Gradient = gradient,
            Fill = GradientTexture2D.FillEnum.Radial,
            FillFrom = new Vector2(0.5f, 0.5f),
            FillTo = new Vector2(1.0f, 0.5f),
            Width = 64,
            Height = 64,
        };
        Axis = Vector3.Axis.Y;
        PixelSize = 0.02f;
        Vector3 position = Position;
        position.Y = 0.01f;
        Position = position;
    }
}
```
