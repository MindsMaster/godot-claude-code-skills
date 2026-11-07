# C# 对照

SKILL.md 各节示例的 C# 写法。通用的 C# 规则见 godot-csharp。

## 自定义 Resource

```csharp
[GlobalClass]
public partial class ItemData : Resource
{
    [Export] public StringName Id { get; set; }

    [Export] public string Title { get; set; } = "";

    [Export(PropertyHint.MultilineText)] public string Description { get; set; } = "";

    [Export] public Texture2D Icon { get; set; }

    [Export] public int Price { get; set; } = 10;

    [Export] public Curve PriceCurve { get; set; }

    [Export] public Godot.Collections.Array<StringName> Tags { get; set; } = new();
}
```

- `[GlobalClass]` 才出现在 New Resource 列表
- 类名与文件名一致，类必须 `partial`
- 字段写成带 `{ get; set; }` 的属性
- 改完先构建，Inspector 才认得新字段
- 导出集合用 `Godot.Collections.Array<T>`，不用 `List<T>`
- 无参构造必须存在，否则 Inspector 新建与 `Duplicate()` 失败
- 读取：`GD.Load<ItemData>("res://data/items/sword.tres")`

## 数据库资源

```csharp
[GlobalClass]
public partial class ItemDb : Resource
{
    [Export] public Godot.Collections.Array<ItemData> Items { get; set; } = new();

    private readonly Dictionary<StringName, ItemData> _byId = new();

    public ItemData GetItem(StringName id)
    {
        if (_byId.Count == 0)
        {
            foreach (ItemData item in Items)
            {
                _byId[item.Id] = item;
            }
        }
        return _byId.GetValueOrDefault(id);
    }
}
```

- 运行时索引用 `System.Collections.Generic.Dictionary`，不导出

## 共享与复制

```csharp
[GlobalClass]
public partial class StatBlock : Resource
{
    [Export] public int Hp { get; set; } = 10;

    [Export] public float Speed { get; set; } = 120.0f;
}

public partial class Enemy : CharacterBody2D
{
    [Export] public StatBlock BaseStats { get; set; }

    public StatBlock Stats { get; private set; }

    public override void _Ready()
    {
        Stats = (StatBlock)BaseStats.Duplicate();
    }
}
```

- `Duplicate()` 返回 `Resource`，强转回具体类型
- 深拷贝：`DuplicateDeep(Resource.DeepDuplicateMode.Internal)` 4.5+

## 异步加载

```csharp
public partial class Loader : Control
{
    [Signal] public delegate void FinishedEventHandler(Resource resource);

    [Export] public ProgressBar Bar { get; set; }

    private string _path = "";
    private readonly Godot.Collections.Array _progress = new();

    public override void _Ready()
    {
        SetProcess(false);
    }

    public void Start(string path)
    {
        _path = path;
        ResourceLoader.LoadThreadedRequest(path);
        SetProcess(true);
    }

    public override void _Process(double delta)
    {
        ResourceLoader.ThreadLoadStatus status = ResourceLoader.LoadThreadedGetStatus(_path, _progress);
        switch (status)
        {
            case ResourceLoader.ThreadLoadStatus.InProgress:
                Bar.Value = _progress[0].AsDouble() * 100.0;
                break;
            case ResourceLoader.ThreadLoadStatus.Loaded:
                SetProcess(false);
                EmitSignal(SignalName.Finished, ResourceLoader.LoadThreadedGet(_path));
                break;
            default:
                SetProcess(false);
                GD.PushError("加载失败 " + _path);
                break;
        }
    }
}
```

- 进度参数是 `Godot.Collections.Array`，引擎写入第 0 项
