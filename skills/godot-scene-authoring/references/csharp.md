# C# 自绘节点

项目用 C# 写 `[Tool]` 显示节点时读这一篇。通用的 C# 热重载规则见 godot-csharp。

类声明写成 `[Tool] public partial class FrameStrip : Node2D, ISerializationListener`，成员如下：

<!-- check: extends Node2D -->
```csharp
private readonly System.Collections.Generic.List<Rect2> _frames = new();
private Texture2D? _sheet;

[Export]
public Texture2D? Sheet
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

public override void _ValidateProperty(Godot.Collections.Dictionary property)
{
    if (property["name"].AsStringName() == CanvasItem.PropertyName.Material)
    {
        property["usage"] = (int)(property["usage"].As<PropertyUsageFlags>() & ~PropertyUsageFlags.Storage);
    }
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
```

- `_frames` 是 `List<Rect2>`，不能转成 Variant，程序集重载后回到空列表，`_Ready` 也不重跑。`OnAfterDeserialize()` 里按导出的贴图重建
- 导出的贴图是 `Texture2D`，重载时会恢复，不用自己存
- 用 `RenderingServer` 建的 canvas item、自己 `AddChild()` 的内部节点，在 `OnBeforeSerialize()` 里释放，`OnAfterDeserialize()` 里重建。重载时会跳过已经释放的对象
- tool 代码 `new` 出来的非 `[Tool]` 嵌套类节点，编辑器里 `_Ready` `_Draw` `_Process` 照常调用，重载后重建成真实例，状态同样只剩 Variant 字段
- 切换场景标签页会触发 `_ExitTree` `_EnterTree`，不触发 `_Ready`。在 `_ExitTree` 里释放的 RID 要在 `_EnterTree` 里补回
