# C# 对照

SKILL.md 各节示例的 C# 写法。通用的 C# 规则见 godot-csharp。

## 数据编辑器

```csharp
[Tool]
[GlobalClass]
public partial class SpawnRule : Resource
{
    public enum SpawnKind
    {
        Once,
        Timed,
    }

    private SpawnKind _kind = SpawnKind.Once;
    private float _interval = 1.0f;

    [Export]
    public SpawnKind Kind
    {
        get => _kind;
        set
        {
            _kind = value;
            NotifyPropertyListChanged();
            EmitChanged();
        }
    }

    [Export]
    public float Interval
    {
        get => _interval;
        set
        {
            _interval = value;
            EmitChanged();
        }
    }

    [Export] public PackedScene Scene { get; set; }

    public override void _ValidateProperty(Godot.Collections.Dictionary property)
    {
        if (property["name"].AsStringName() == PropertyName.Interval && _kind != SpawnKind.Timed)
        {
            property["usage"] = (int)PropertyUsageFlags.NoEditor;
        }
    }
}
```

- 引擎里的属性名是 C# 名 Interval，比较用生成的 PropertyName 类
- 写回 `usage` 时转 `int`
- 嵌套枚举不能与属性同名

## @tool 脚本

```csharp
[Tool]
public partial class RulePreview : Node2D
{
    private SpawnRule _rule;

    [Export]
    public SpawnRule Rule
    {
        get => _rule;
        set
        {
            if (_rule != null)
            {
                _rule.Changed -= QueueRedraw;
            }
            _rule = value;
            if (_rule != null)
            {
                _rule.Changed += QueueRedraw;
            }
            QueueRedraw();
        }
    }

    public override void _ExitTree()
    {
        if (_rule != null)
        {
            _rule.Changed -= QueueRedraw;
        }
    }

    public override void _Draw()
    {
        if (_rule != null && Engine.IsEditorHint())
        {
            DrawCircle(Vector2.Zero, 16.0f, Colors.Red);
        }
    }

    public override void _Process(double delta)
    {
        if (Engine.IsEditorHint())
        {
            return;
        }
        Position += new Vector2(10.0f * (float)delta, 0.0f);
    }
}
```

- 改代码后点 Build，`[Tool]` 脚本才用上新代码
- 新增的导出成员和信号也要先 Build 才出现
- 热重载只保留 `[Export]` 成员的值
- 订阅的事件在 `_ExitTree` 里取消，否则可能挡住程序集卸载
- `[Tool]` 类里少放静态缓存，重载后的行为没有文档保证

## 动态属性

```csharp
[Tool]
[GlobalClass]
public partial class WaveTable : Resource
{
    private int _waveCount = 3;
    private int[] _counts = { 5, 8, 12 };

    [Export]
    public int WaveCount
    {
        get => _waveCount;
        set
        {
            _waveCount = Mathf.Clamp(value, 1, 20);
            Array.Resize(ref _counts, _waveCount);
            NotifyPropertyListChanged();
        }
    }

    public override Godot.Collections.Array<Godot.Collections.Dictionary> _GetPropertyList()
    {
        var props = new Godot.Collections.Array<Godot.Collections.Dictionary>();
        for (int i = 0; i < _waveCount; i++)
        {
            props.Add(new Godot.Collections.Dictionary
            {
                { "name", $"wave_{i}_count" },
                { "type", (int)Variant.Type.Int },
                { "usage", (int)PropertyUsageFlags.Default },
            });
        }
        return props;
    }

    public override Variant _Get(StringName property)
    {
        int index = WaveIndex(property);
        return index >= 0 ? _counts[index] : default;
    }

    public override bool _Set(StringName property, Variant value)
    {
        int index = WaveIndex(property);
        if (index < 0)
        {
            return false;
        }
        _counts[index] = value.AsInt32();
        return true;
    }

    private int WaveIndex(string property)
    {
        if (!property.StartsWith("wave_") || !property.EndsWith("_count"))
        {
            return -1;
        }
        int index = property.Split('_')[1].ToInt();
        return index < _counts.Length ? index : -1;
    }
}
```

- `_Get` 返回 `default` 即 Nil，表示不处理该属性
- `_Set` 返回 `false` 交给默认处理

## Inspector 按钮与校验

```csharp
[Tool]
public partial class SnapTool : Node2D
{
    private Node2D _target;

    [Export]
    public Node2D Target
    {
        get => _target;
        set
        {
            _target = value;
            UpdateConfigurationWarnings();
        }
    }

    [ExportToolButton("Snap To Target", Icon = "Reload")]
    public Callable SnapAction => Callable.From(SnapToTarget);

    public override string[] _GetConfigurationWarnings()
    {
        return _target == null ? new[] { "target 未设置" } : Array.Empty<string>();
    }

    private void SnapToTarget()
    {
#if TOOLS
        EditorUndoRedoManager ur = EditorInterface.Singleton.GetEditorUndoRedo();
        ur.CreateAction("Snap To Target", UndoRedo.MergeMode.Disable, this);
        ur.AddDoProperty(this, Node2D.PropertyName.GlobalPosition, _target.GlobalPosition);
        ur.AddUndoProperty(this, Node2D.PropertyName.GlobalPosition, GlobalPosition);
        ur.CommitAction();
#endif
    }
}
```

- `[ExportToolButton]` 必须是表达式体属性，有后备字段报 GD0111
- 不能与 `[Export]` 同用，类上没有 `[Tool]` 也报错
- 编辑器 API 用 `#if TOOLS` 包住，导出构建不含编辑器程序集

## 插件

- `plugin.cfg` 写 `script="ItemsPlugin.cs"`，插件文件整体包进 `#if TOOLS`
- 编辑器单例经 Singleton 属性访问，如 EditorInterface.Singleton
- C# 的 `EditorScript` 不能从脚本编辑器运行
- 用文件系统右键 Run，或命令面板，后者要求 `[GlobalClass]` 与 `[Tool]`
