# C# 对照

SKILL.md 各节示例的 C# 写法，以及 `[Tool]` 节点的热重载。通用的 C# 热重载规则见 godot-csharp。

## 新做场景

生成场景文件的一次性脚本用 GDScript，.NET 版 Godot 同样能跑。

```csharp
public partial class Level : Node2D
{
    [Export] public PackedScene EnemyScene { get; set; }

    private Node2D _spawnPoints;

    public override void _Ready()
    {
        _spawnPoints = GetNode<Node2D>("SpawnPoints");
    }

    public void SpawnWave()
    {
        foreach (Node2D point in _spawnPoints.GetChildren())
        {
            var enemy = EnemyScene.Instantiate<Node2D>();
            enemy.Position = point.Position;
            AddChild(enemy);
        }
    }
}
```

## 自绘节点

```csharp
[Tool]
public partial class GroundProp : Node2D
{
    private Texture2D _texture;
    private float _height = 64.0f;

    [Export]
    public Texture2D Texture
    {
        get => _texture;
        set
        {
            _texture = value;
            QueueRedraw();
        }
    }

    [Export]
    public float Height
    {
        get => _height;
        set
        {
            _height = value;
            QueueRedraw();
        }
    }

    public override void _Draw()
    {
        if (_texture == null)
        {
            return;
        }
        Vector2 size = _texture.GetSize() * (_height / _texture.GetHeight());
        DrawTextureRect(_texture, new Rect2(new Vector2(-size.X / 2.0f, -size.Y), size), false);
    }
}
```

- 类加 `[Tool]`，改完点 Build 才生效
- tool 代码 `new` 出的非 `[Tool]` C# 节点，编辑器里 `_Ready` `_Draw` 照常调用

热重载时 `_Ready` 不重跑，只恢复能转成 Variant 的字段和属性。不能转的状态实现 `ISerializationListener` 重建：

```csharp
[Tool]
public partial class FrameStrip : Node2D, ISerializationListener
{
    private readonly List<Rect2> _frames = new();
    private Texture2D _sheet;

    [Export]
    public Texture2D Sheet
    {
        get => _sheet;
        set
        {
            _sheet = value;
            Rebuild();
        }
    }

    public override void _Ready()
    {
        Rebuild();
    }

    public void OnBeforeSerialize()
    {
    }

    public void OnAfterDeserialize()
    {
        Rebuild();
    }

    private void Rebuild()
    {
        _frames.Clear();
        if (_sheet != null)
        {
            _frames.Add(new Rect2(Vector2.Zero, _sheet.GetSize() / 4f));
        }
        QueueRedraw();
    }
}
```

| 状态 | 重载后 |
|---|---|
| `List<Rect2>` 这类非 Variant 字段 | 回到初值，在 `OnAfterDeserialize()` 里重建 |
| 导出的 `Texture2D` | 自动恢复 |
| `RenderingServer` 建的 RID、自己 `AddChild()` 的内部节点 | 在 `OnBeforeSerialize()` 里释放，`OnAfterDeserialize()` 里重建 |
| tool 代码 `new` 出的非 `[Tool]` 节点 | 重建成真实例，只剩 Variant 字段 |

- 切换场景标签页触发 `_ExitTree` `_EnterTree`，不触发 `_Ready`
- `_ExitTree` 里释放的 RID 在 `_EnterTree` 里补回

## 派生属性

```csharp
[Tool]
public partial class DepthProp : Node2D
{
    private float _depth;

    [Export]
    public float Depth
    {
        get => _depth;
        set
        {
            _depth = value;
            ZIndex = _depth > 0.0f ? -10 : 10;
        }
    }

    public override void _ValidateProperty(Godot.Collections.Dictionary property)
    {
        if (property["name"].AsStringName() == CanvasItem.PropertyName.ZIndex)
        {
            property["usage"] = (int)(property["usage"].As<PropertyUsageFlags>() & ~PropertyUsageFlags.Storage);
        }
    }
}

[Tool]
public partial class ShadowedProp : Node2D
{
    private Sprite2D _shadow;

    public override void _Ready()
    {
        _shadow = new Sprite2D();
        _shadow.Modulate = new Color(0.0f, 0.0f, 0.0f, 0.4f);
        AddChild(_shadow, false, InternalMode.Back);
    }
}
```

- `property["name"]` 是 `StringName`，和 `PropertyName` 常量比较

## 存盘导出

```csharp
[Tool]
public partial class RoomPoints : Node2D
{
    [Export(PropertyHint.File, "*.json")] public string ExportPath { get; set; } = "res://room_points.json";

    public override void _Notification(int what)
    {
        if (what == NotificationEditorPreSave)
        {
            ExportPoints();
        }
    }

    public void ExportPoints()
    {
        var points = new Godot.Collections.Array();
        foreach (Node child in GetChildren())
        {
            if (child is Marker2D marker)
            {
                points.Add(new Godot.Collections.Dictionary
                {
                    { "name", marker.Name.ToString() },
                    { "x", marker.Position.X },
                    { "y", marker.Position.Y },
                });
            }
        }
        using var file = FileAccess.Open(ExportPath, FileAccess.ModeFlags.Write);
        file.StoreString(Json.Stringify(new Godot.Collections.Dictionary { { "points", points } }, "\t"));
    }
}
```
