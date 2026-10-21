# GDScript 与 C# 对照

左列 GDScript，右列 C#。引擎 API 的名字转换规则见 SKILL.md 的命名映射一节。

## 语法

| GDScript | C# |
|---|---|
| `var hp := 10` | `int hp = 10;` 或 `var hp = 10;` |
| `var items: Array[int] = []` | `List<int> items = new();` 传给引擎时用 `Godot.Collections.Array<int>` |
| `var d: Dictionary[String, int] = {}` | `Dictionary<string, int> d = new();` 传给引擎时用 `Godot.Collections.Dictionary<string, int>` |
| `const MAX := 10` | `private const int Max = 10;` 只有基本类型能 `const` |
| `static var count := 0` | `private static int s_count;` |
| `func f(x: int) -> bool:` | `public bool F(int x)` |
| `signal hit(damage: int)` | `[Signal] public delegate void HitEventHandler(int damage);` |
| `hit.emit(3)` | `EmitSignal(SignalName.Hit, 3);` |
| `button.pressed.connect(_on_pressed)` | `button.Pressed += OnPressed;` |
| `button.pressed.disconnect(_on_pressed)` | `button.Pressed -= OnPressed;` |
| `cb.bind(x)` | `() => Cb(x)` 包进 `Callable` |
| `await sig` | `await ToSignal(source, SignalName.Xxx);` |
| `await get_tree().create_timer(1.0).timeout` | `await ToSignal(GetTree().CreateTimer(1.0), SceneTreeTimer.SignalName.Timeout);` |
| `@export var speed := 1.0` | `[Export] public float Speed { get; set; } = 1.0f;` |
| `@export_range(0, 10, 0.1)` | `[Export(PropertyHint.Range, "0,10,0.1")]` |
| `@export_enum("A", "B") var m: int` | `[Export(PropertyHint.Enum, "A,B")]` |
| `@export_group("G")` | `[ExportGroup("G")]` |
| `@export_file("*.tscn")` | `[Export(PropertyHint.File, "*.tscn")]` |
| `@onready var l: Label = $L` | 字段加 `_Ready()` 里 `_l = GetNode<Label>("L");` |
| `@tool` | `[Tool]` |
| `class_name Foo` | `[GlobalClass]` 加 `partial class Foo` |
| `@icon("res://x.svg")` | `[Icon("res://x.svg")]` |
| `extends Node2D` | `public partial class Foo : Node2D` |
| `super()` | `base._Ready();` |
| `x is Foo` | `x is Foo` |
| `x as Foo` | `x as Foo` |
| `match x:` | `switch (x)` 与模式匹配 |
| `for i in range(n):` | `for (int i = 0; i < n; i++)` |
| `lambda := func(a): return a` | `Func<int, int> lambda = a => a;` |
| `$Path` | `GetNode<T>("Path")` |
| `%Name` | `GetNode<T>("%Name")` |
| `preload("res://x.tscn")` | `GD.Load<PackedScene>("res://x.tscn")` |
| `x.instantiate()` | `scene.Instantiate<Foo>()` |
| `assert(c)` | `System.Diagnostics.Debug.Assert(c)` |
| `print(a, b)` | `GD.Print(a, b)` |
| `push_error(m)` | `GD.PushError(m)` |
| `is_instance_valid(o)` | `GodotObject.IsInstanceValid(o)` |
| `call_deferred("f")` | `CallDeferred(MethodName.F)` |
| `NodePath("a/b")`、`^"a/b"` | `new NodePath("a/b")` 或字符串隐式转换 |
| `&"name"` | `new StringName("name")` 或隐式转换，热路径放 `static readonly` |
| `x.set_name("a")` | `x.Name = "a";` |
| `Vector2.RIGHT` | `Vector2.Right` |
| `PI` | `Mathf.Pi` |

## 全局函数

| GDScript | C# |
|---|---|
| `abs` `absf` `absi` | `Mathf.Abs` |
| `clamp` `clampf` `clampi` | `Mathf.Clamp` |
| `lerp` `lerpf` | `Mathf.Lerp` |
| `lerp_angle` | `Mathf.LerpAngle` |
| `move_toward` | `Mathf.MoveToward` |
| `snapped` | `Mathf.Snapped` |
| `remap` | `Mathf.Remap` |
| `wrap` `wrapf` `wrapi` | `Mathf.Wrap` |
| `posmod` `fposmod` | `Mathf.PosMod` |
| `deg_to_rad` `rad_to_deg` | `Mathf.DegToRad` `Mathf.RadToDeg` |
| `is_equal_approx` `is_zero_approx` | `Mathf.IsEqualApprox` `Mathf.IsZeroApprox` |
| `floori` `ceili` `roundi` | `Mathf.FloorToInt` `Mathf.CeilToInt` `Mathf.RoundToInt` |
| `smoothstep` | `Mathf.SmoothStep` |
| `randf` | `GD.Randf` |
| `randi` | `GD.Randi` |
| `randf_range` `randi_range` | `GD.RandRange` |
| `randomize` `seed` | `GD.Randomize` `GD.Seed` |
| `load` | `GD.Load<T>` |
| `str` | `$"{x}"` 字符串插值 |
| `type_exists` | `ClassDB.ClassExists` |
| `weakref` | `GodotObject.WeakRef` |
| `var_to_str` `str_to_var` | `GD.VarToStr` `GD.StrToVar` |
| `len` `range` | `.Length` 或 `.Count`，`GD.Range` 或 `Enumerable.Range` |
| `print_debug` | 没有 |
| `print_stack` | `GD.Print(System.Environment.StackTrace)` |
| `push_warning` | `GD.PushWarning` |
| `printerr` | `GD.PrintErr` |
| `print_rich` | `GD.PrintRich` |

## 容器

| GDScript | C# |
|---|---|
| `Array` | `Godot.Collections.Array` |
| `Array[T]` | `Godot.Collections.Array<T>` |
| `Dictionary` | `Godot.Collections.Dictionary` |
| `Dictionary[K, V]` | `Godot.Collections.Dictionary<K, V>` |
| `PackedByteArray` | `byte[]` |
| `PackedInt32Array` `PackedInt64Array` | `int[]` `long[]` |
| `PackedFloat32Array` `PackedFloat64Array` | `float[]` `double[]` |
| `PackedStringArray` | `string[]` |
| `PackedVector2Array` `PackedVector3Array` | `Vector2[]` `Vector3[]` |
| `PackedColorArray` | `Color[]` |
| `arr.append(x)` | `arr.Add(x)` |
| `arr.append_array(o)` | `arr.AddRange(o)` |
| `arr.push_back(x)` | `arr.Insert(arr.Count, x)` 或 `Add()` |
| `arr.pop_back()` | 取 `arr[^1]` 再 `RemoveAt(arr.Count - 1)` |
| `arr.size()` | `arr.Count` |
| `arr.is_empty()` | `arr.Count == 0` |
| `arr.has(x)` | `arr.Contains(x)` |
| `arr.find(x)` | `arr.IndexOf(x)` |
| `arr.erase(x)` | `arr.Remove(x)` |
| `arr.duplicate()` | `arr.Duplicate()` |
| `arr.filter(f)` `arr.map(f)` | LINQ 的 `Where()` 与 `Select()`，在 Godot 集合上逐元素互操作 |
| `arr.sort_custom(f)` | `OrderBy()`，或转成 `List<T>` 后 `Sort()` |
| `arr.pick_random()` | `PickRandom()` |
| `dict.has(k)` | `dict.ContainsKey(k)` |
| `dict.get(k, d)` | `dict.TryGetValue(k, out var v)` |
| `dict.keys()` | `dict.Keys` |

## 字符串

多数方法有 .NET 等价物，没有的在 `StringExtensions` 里，作为扩展方法直接用。

| GDScript | C# |
|---|---|
| `s.begins_with("a")` | `s.StartsWith("a")` |
| `s.ends_with("a")` | `s.EndsWith("a")` |
| `s.is_empty()` | `string.IsNullOrEmpty(s)` |
| `s.to_lower()` | `s.ToLower()` |
| `s.split(",")` | `s.Split(",")` |
| `s.strip_edges()` | `s.Trim()` |
| `s.replace("a", "b")` | `s.Replace("a", "b")` |
| `s.to_int()` | `int.TryParse(s, out var n)` |
| `s.to_float()` | `float.TryParse(s, out var f)` |
| `s.to_snake_case()` | `s.ToSnakeCase()` |
| `s.get_extension()` | `s.GetExtension()` |
| `s.path_join("x")` | `s.PathJoin("x")` |
| `"%d/%d" % [a, b]` | `$"{a}/{b}"` |

C# 字符串是 UTF-16 且不可变，循环里拼接用 `StringBuilder`。

## 与 GDScript 互相调用

```csharp
using Godot;

public partial class Bridge : Node
{
    public override void _Ready()
    {
        var script = GD.Load<GDScript>("res://enemy.gd");
        var enemy = (GodotObject)script.New();
        enemy.Set("health", 5);
        GD.Print(enemy.Get("health"));
        enemy.Call("take_damage", 2);
        enemy.Connect("died", Callable.From(OnDied));
    }

    private void OnDied()
    {
        GD.Print("died");
    }
}
```

- 从 C# 访问 GDScript 成员只能用 `Get()` `Set()` `Call()` `Connect()`，名字是 GDScript 里的 `snake_case`。传错参数个数时 `Call()` 静默失败
- GDScript 脚本里的信号不会生成 C# 事件，用 `Connect()`
- GDScript 与 C# 脚本不能互相继承
- 从 GDScript 访问 C# 成员用 C# 里的名字，`node.MyProperty`、`node.PrintNodeName(self)`
- GDScript 里实例化 C# 脚本：`load("res://MyNode.cs").new()`。类名必须与 `.cs` 文件名一致，文件要在 `.csproj` 里被包含，类要派生自 Godot 类，否则报 `Invalid call. Nonexistent function 'new' in base`

## 其他差异

- `Callable` 的 `bind`、`unbind` 没有，C# 创建的 `Callable` 才能被 C# 调用，GDScript 里带 `bind` 的 `Callable` 在 C# 里无法使用
- `Signal` 的 `get_name()` 与 `get_object()` 变成属性 Name 与 Owner
- `NodePath.is_empty()` 变成属性 IsEmpty
- `Transform3D` 的 `new Transform3D()` 全部分量是零，要单位变换写 `Transform3D.Identity`
- `Input`、`OS` 等单例是静态类。需要 `GodotObject` 成员（如 `Connect()`）时用它们的 Singleton 属性
- `EditorInterface` 在 C# 里不是静态类，用它的 Singleton 属性
- 条件编译：`GODOT`、`TOOLS`（Debug 配置）、`GODOT_REAL_T_IS_DOUBLE`，平台宏 `GODOT_WINDOWS` `GODOT_LINUXBSD` `GODOT_MACOS` `GODOT_ANDROID` `GODOT_IOS` `GODOT_WEB`，类别宏 `GODOT_PC` `GODOT_MOBILE`，版本宏 `GODOT4_4_OR_GREATER` 这一类。官方文档说类别宏只在导出时有，Godot.NET.Sdk 的 Sdk.props 按构建目标平台定义，Linux Debug 构建实测已有 `GODOT_LINUXBSD` 与 `GODOT_PC`
