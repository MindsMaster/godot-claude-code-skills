---
name: godot-csharp
description: 在 Godot 里写 C# 时用。partial class 与源码生成器、[Export] [Signal] [GlobalClass] [Tool]、信号连接与断开、SignalName PropertyName 与 StringName 缓存、Variant 与 Godot.Collections、IsInstanceValid、async ToSignal、每帧分配。C# scripting in Godot.
---

# Godot C# 写法

C# 脚本的通用规则：命名映射、源码生成器、导出、信号、StringName、集合、生命周期、async。GDScript 通用写法去 godot-gdscript，GDScript 与 C# 对照表在 [references/gdscript-csharp.md](references/gdscript-csharp.md)，卡顿排查去 godot-performance。

其他 skill 里的 C# 只给与 GDScript 不同的部分，通用规则以本文件为准。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 数学与随机 | `Mathf.Lerp`、`Mathf.MoveToward`、`GD.Randf`、`GD.RandRange` | 来回转 `double` 的 `System.Math` 调用 |
| 取节点 | `GetNode<T>("%Name")`、`[Export]` 引用、`GetNodeOrNull<T>` | 属性里每次 `GetNode()`，`_Process` 里 `GetNode()` |
| 信号 | 生成的事件 `Pressed += OnPressed`，自定义用 `[Signal]` | `Connect("pressed", ...)` 字符串 |
| 名字常量 | `Node2D.PropertyName.Position`、`SignalName.Xxx`、`MethodName.Xxx` | 每次调用传字符串字面量 |
| 等信号与延时 | `await ToSignal(GetTree().CreateTimer(1.0), SceneTreeTimer.SignalName.Timeout)` | `Task.Delay`，它不跟 `Engine.TimeScale`，也不跟节点生命周期 |
| 帧末调用 | `CallDeferred(MethodName.Foo)`，lambda 包成 `Callable` 再 `CallDeferred()` | 自建消息队列 |
| 后台计算 | `WorkerThreadPool.AddTask`、`Task.Run` 加 `CallDeferred()` 回主线程 | 自建 `Thread` 池 |
| 数据对象 | `[GlobalClass] partial class X : Resource` 加 `[Export]` | JSON 加手写解析 |
| 输入判断 | 事件模式匹配、`Input.GetVector` | 手写正负键相减 |
| 日志 | `GD.Print`、`GD.PushError`、`GD.PushWarning` | `Console.WriteLine` |

## 类与源码生成器

```csharp
using Godot;

[GlobalClass]
public partial class Turret : Node2D
{
    [Export]
    public PackedScene BulletScene { get; set; }

    [Export(PropertyHint.Range, "0,10,0.1,or_greater")]
    public float Cooldown { get; set; } = 0.5f;

    [Export]
    private Marker2D _muzzle;

    private Label _label;
    private float _timer;

    public override void _Ready()
    {
        _label = GetNode<Label>("%Label");
    }

    public override void _Process(double delta)
    {
        _timer -= (float)delta;
    }
}
```

- 派生自 `GodotObject` 的类必须写 `partial`，否则报 `GD0001`。外层类含此类的嵌套类时，外层也要 `partial`，否则 `GD0002`。`[GlobalClass]` 类不能是泛型，报 `GD0402`
- 挂到节点上的脚本，类名要与 `.cs` 文件名一致且区分大小写，一个文件一个脚本类
- 生成器给每个类补 `PropertyName`、`MethodName`、`SignalName` 嵌套类，并生成属性与方法的注册、导出默认值、热重载的保存与恢复代码
- 自定义类的 `PropertyName` 含非静态且 Variant 兼容的字段与属性，含 private 与只读。`MethodName` 含 Variant 兼容签名的方法，含 private、static 与 `_Ready` 这类重写，重载共用一个名字，泛型方法没有。值是 C# 原名，引擎类的值是 snake_case，所以 `Node.MethodName.AddChild` 可以传给 `CallDeferred()`。嵌套类继承基类的同名嵌套类，`Hud.PropertyName.Position` 也能用
- 新增或修改 `[Export]`、`[Signal]`、`[Tool]` 后必须点编辑器右上角 Build 重新构建，Inspector 与信号面板才会更新
- 引擎用无参构造创建脚本实例，没有无参构造报错。构造函数里不调依赖场景树的 API
- `[GlobalClass]` 让类出现在 Add Node 与 Create Resource 对话框，也限制 `[Export]` 的赋值类型，图标用 `[Icon("res://x.svg")]`。`[Tool]` 让脚本在编辑器里运行，用 `Engine.IsEditorHint()` 区分

## 命名映射

- 方法与属性 `snake_case` 转大驼峰：`move_and_slide` 对应 `MoveAndSlide()`。getter 与 setter 合并成属性：`x.set_name("a")` 写成 `x.Name = "a"`
- `Object` 对应 `GodotObject`，`RID` 对应 `Rid`，`AABB` 对应 `Aabb`
- 全局枚举独立成型：`KEY_ESCAPE` 对应 `Key.Escape`，`ERR_*` 对应 `Error`。类内枚举与属性同名时枚举名加 Enum 后缀：`MultiMesh.TransformFormatEnum.Transform3D`
- `Vector2.RIGHT` 变成只读属性 `Vector2.Right`，不能用在 `case` 里。`PI` 对应 `Mathf.Pi`
- 没有 `preload` 和 `@onready`，用 `GD.Load<T>()` 与 `_Ready()`。`Callable` 没有 `bind`，用 lambda 捕获
- 引擎方法里接收字符串方法名的 API 要传 `snake_case` 名：`CallDeferred("add_child")` 可以，`CallDeferred("AddChild")` 找不到。优先用 `MethodName.AddChild`
- 路径函数用 `StringExtensions` 的 `GetBaseName()`，不用 `System.IO.Path`，后者不认 `res://`

完整对照表在 [references/gdscript-csharp.md](references/gdscript-csharp.md)。

## 导出

```csharp
#nullable enable
using Godot;
using Godot.Collections;

public partial class Spawner : Node
{
    public enum Kind { Small, Big }

    [Export]
    public PackedScene Scene { get; set; } = null!;

    [Export]
    public Marker2D? Optional { get; set; }

    [Export]
    public Kind Size { get; set; } = Kind.Small;

    [ExportGroup("Waves")]
    [Export]
    public Array<PackedScene> Waves { get; set; } = new();

    [Export(PropertyHint.Enum, "Easy,Hard")]
    public string Difficulty { get; set; } = "Easy";
}
```

- 只有 Variant 兼容类型可导出：基本类型、`string`、`GodotObject` 派生类、`Godot.Collections` 的类型、`byte[]` `int[]` `string[]` `Vector2[]` 等紧凑数组。`List<T>`、`System.Collections.Generic.Dictionary` 不行，报 `GD0102`
- 字段与属性都可导出，任意访问级别。只读、只写、静态、索引器不行，分别报 `GD0103` `GD0104` `GD0101` `GD0105`
- 默认值由生成器分析源码里的初始化表达式得到，不会执行 getter。复杂初始化得不到默认值
- 启用 nullable 后，必有的引用写 `= null!`，可选的写 `?`。生成器不会替你检查导出是否已赋值
- 非 `Node` 派生的类导出 `Node` 成员报 `GD0107`，Resource 里不能存节点引用
- 导出的 setter 在场景实例化时先于 `_Ready()` 调用，此时子节点引用还是 `null`
- `[ExportToolButton("Bake")]` 4.4+，属性类型是 `Callable`，必须是表达式体属性，类要 `[Tool]`

## 信号

```csharp
using Godot;

public partial class Health : Node
{
    [Signal]
    public delegate void ChangedEventHandler(int current, int max);

    [Signal]
    public delegate void DiedEventHandler();

    [Export]
    public int Max { get; set; } = 100;

    private int _current = 100;

    public void Damage(int amount)
    {
        _current = Mathf.Max(0, _current - amount);
        EmitSignalChanged(_current, Max);
        if (_current == 0)
        {
            EmitSignalDied();
        }
    }
}

public partial class Hud : Control
{
    [Export]
    public Health Target { get; set; }

    private Label _label;

    public override void _Ready()
    {
        _label = GetNode<Label>("Label");
    }

    public override void _EnterTree()
    {
        Target.Changed += OnChanged;
    }

    public override void _ExitTree()
    {
        Target.Changed -= OnChanged;
    }

    private void OnChanged(int current, int max)
    {
        _label.Text = $"{current}/{max}";
    }
}
```

- 委托名必须以 EventHandler 结尾（`GD0201`），返回 `void`（`GD0203`），参数是 Variant 兼容类型（`GD0202`）。生成的事件名去掉后缀。事件不能 `Invoke()`
- 发射用生成的 `EmitSignalChanged(current, max)`，参数类型同委托，类为 `sealed` 时是 private，否则 protected。`EmitSignal(SignalName.Changed, a, b)` 也可以，但 `params Variant[]` 每次分配数组，写成 `EmitSignal(SignalName.Changed, [a, b])` 走 `ReadOnlySpan<Variant>` 重载不分配
- 引擎信号同样是事件：`button.Pressed += OnPressed`，`timer.Timeout += () => ...`
- 接收者被释放时引擎按 `Delegate.Target` 自动断开连接，但有两种情况不自动断开：连接的是捕获了局部变量的 lambda，或者连接的是自定义信号的 `+=`。之后信号触发时，回调里访问已释放的接收者会抛 `ObjectDisposedException`。这两种在 `_EnterTree()` 连接，在 `_ExitTree()` 用 `-=` 断开，lambda 要保留委托引用才能断开
- 自定义信号的 `+=` 只写进发射者的托管委托，不经过引擎的 `Connect()`。不想手动断开时对自定义信号用 `Connect(SignalName.X, Callable.From(OnX))`，回调是接收者自己的实例方法时随接收者释放自动断开
- OneShot 等标志要用 `Connect()`：`(uint)GodotObject.ConnectFlags.OneShot`。连接 GDScript 里定义的信号也只能用字符串 `Connect("sig", Callable.From(...))`
- 信号参数是自定义数据时，类要继承 `GodotObject`，不能是普通 C# 类

## StringName 缓存

字符串隐式转 `StringName` 等于 `new StringName(string)`，每次新建一个带终结器的托管对象并调一次原生，没有缓存，每帧调用就是每帧分配。官方文档也建议用 `PropertyName`、`MethodName`、`SignalName` 里的 `StringName`。

```csharp
using Godot;

public partial class Flash : Sprite2D
{
    private static readonly StringName s_amount = "flash_amount";
    private ShaderMaterial _material;

    public override void _Ready()
    {
        _material = (ShaderMaterial)Material;
    }

    public override void _Process(double delta)
    {
        _material.SetShaderParameter(s_amount, 0.5f);
        if (Input.IsActionJustPressed(Actions.Jump))
        {
            Modulate = Colors.White;
        }
    }
}

public static class Actions
{
    public static readonly StringName Jump = "jump";
}
```

- 引擎自带的名字用生成常量：`Node2D.PropertyName.Position`、`Button.SignalName.Pressed`、`Node.MethodName.AddChild`，自定义类里是 `PropertyName.MyField` 这类
- 输入动作、着色器参数、动画名、分组名、`Call()` `Get()` `Set()` 的名字，全部放 `static readonly StringName`
- 不要每帧拼接蛇形名字，拼一次存起来。`NodePath` 同理，路径放字段里

## 集合与 Variant

- `Godot.Collections.Array`、`Dictionary` 是 C++ 对象的包装，每次读写都过一次互操作。只在传给引擎 API 或导出时用，内部状态用 `List<T>`、`Dictionary<K, V>`
- 两种集合互转逐元素复制并转换，`ToList()`、`ToArray()`、`new Array<T>(IEnumerable<T>)` 都是 O(n) 加分配。`new Array<T>(untypedArray)` 只包装不复制
- 在 Godot 集合上用 LINQ 每个元素都过一次互操作，用实例方法 `Sort()`、`Reverse()`，热路径用 `for`
- `Variant` 是结构体，不装箱。`Variant.Obj` 返回 `object`，值类型会装箱。转换用 `As<T>()` 或显式转换
- 整数与浮点在 Variant 里是 64 位，反向转换可能丢精度。枚举没有隐式转换，用 `Variant.From(e)` 与 `v.As<MyEnum>()`
- 紧凑数组对应 .NET 数组：`PackedByteArray` 是 `byte[]`，`PackedVector2Array` 是 `Vector2[]`，传给引擎时复制一份

## 对象生命周期

- 节点用 `QueueFree()` 或 `Free()` 释放，不调 `Dispose()`。`Dispose()` 只放掉托管侧，原生节点不会释放，退出时报 ObjectDB 泄漏
- 已释放对象的托管引用不变 `null`，访问成员和 `ToString()` 都抛 `ObjectDisposedException`。判断用 `GodotObject.IsInstanceValid(obj)`，不用 `obj != null`。`QueueFree()` 之后到实际释放之前 `IsInstanceValid()` 仍为 `true`，要排除待删除对象再查 `IsQueuedForDeletion()`
- `RefCounted` 与 `Resource` 派生类如 `Image`、`FileAccess` 靠 GC 终结器释放原生引用，时机不定，大对象用 `using` 提前释放
- 持有可能被释放的对象用 `GodotObject.WeakRef(obj)`

## async 与线程

```csharp
using System.Threading.Tasks;
using Godot;

public partial class Door : Node3D
{
    public override async void _Ready()
    {
        await ToSignal(GetTree().CreateTimer(1.0), SceneTreeTimer.SignalName.Timeout);
        if (!IsInsideTree())
        {
            return;
        }
        Hide();
        int total = await Task.Run(() => 42);
        Name = $"Door{total}";
    }

    public void Attach(Node child)
    {
        Callable.From(() => AddChild(child)).CallDeferred();
    }
}
```

- `await ToSignal(source, SignalName.X)` 的 continuation 由发射信号的线程直接调用，不经 `GodotSynchronizationContext`。引擎信号在主线程发射，所以通常在主线程继续。等待者 `this` 被释放后连接随之断开，continuation 不再执行也不报错，`await` 后面的状态复位不会跑
- `await` 返回时节点可能已离开场景树，`GetTree()` 为 `null`。先检查 `IsInsideTree()`，用到别的对象时检查它的 `IsInstanceValid()`。`source` 在调用 `ToSignal()` 时已释放会抛 `ObjectDisposedException`，等待期间被释放则永远不会返回
- `CreateTimer(1.0)` 的 `processAlways` 默认 `true`，`SceneTree.Paused` 时照常计时，要随暂停传 `false`
- 在主线程发起的 `await Task.Run(...)` 捕获了 `GodotSynchronizationContext`，continuation 排队到下一次帧回调在主线程执行。`ConfigureAwait(false)` 以及线程池线程里发起的 `await` 不带这个上下文，continuation 留在线程池线程，其后的 `await` 同样留在线程池，别在其后碰场景树
- 没人 `await` 的 `Task` 里的异常不会打印，入口 `try/catch` 并 `GD.PushError`。`async void` 方法的异常会在帧回调里被引擎打印
- 线程里碰场景树只能 `CallDeferred()`，物理回调里改 disabled 或 monitoring 用 `SetDeferred()`，名字传 `CollisionShape2D.PropertyName.Disabled` 这类常量

## _Process 里避免分配

- `GetChildren()` 每次新建一个原生数组和托管包装，读元素时每个再过一次互操作，热路径用 `GetChildCount()` 加 `GetChild(i)`，或缓存列表
- 不在每帧用 LINQ、`ToArray()`、`ToList()`、`new List<T>()`、`new Dictionary`、`new float[n]`。缓冲区放字段，`Clear()` 复用
- 每帧捕获变量的 lambda 会分配闭包。需要 `Callable` 时缓存到字段
- `Call("method", a, b)` 和 `EmitSignal(name, a, b)` 的 `params Variant[]` 分配数组，用强类型调用，或写成集合表达式 `Call("method", [a, b])` 走 `ReadOnlySpan<Variant>` 重载
- 原生属性每次读写都过互操作，循环里读到局部变量，最后写回一次
- 文本每帧拼接会分配字符串，数值没变就不更新 `Label.Text`
- 不需要的节点 `SetProcess(false)`，不可见时不要每帧 `QueueRedraw()`

## 陷阱

- `_Process(double delta)`，`Vector2` 分量是 `float`，写 `(float)delta`
- `Position.X = 1` 编译报 `CS1612`，写 `Position = Position with { X = 1 }`
- `GetNode<T>()` 类型不符抛 `InvalidCastException`，可能为空用 `GetNodeOrNull<T>()`，或 `if (GetNode("X") is Sprite2D s)`
- `string` 到 `StringName` 和 `NodePath` 的隐式转换容易漏掉分配
- 热重载保存并恢复可读可写、非静态、Variant 兼容的字段与属性，不要求 `[Export]`，只读、`init`、静态和 `List<T>` 这类成员回到初始值。不可保存的状态实现 `ISerializationListener` 重建
- 静态字段持有 `GodotObject`，节点释放后字段指向已释放对象，热重载后静态字段回到初始值。静态 `Action` 保存实例方法同理。静态字段只放纯 C# 数据与 `StringName`
- 运行中的后台 `Task` 和 `Thread`、字段里存着的 `Callable` 可能让程序集卸载失败，在 `_ExitTree()` 里取消或清理
- `EditorInterface` 在 C# 里不是静态类，访问它的 Singleton 属性
- 输入事件模式匹配、热重载细节、线程、Packed 数组属性每次读都复制等跨界开销在 [references/runtime.md](references/runtime.md)

## 参考

- [references/gdscript-csharp.md](references/gdscript-csharp.md) GDScript 与 C# 常用写法对照
- [references/runtime.md](references/runtime.md) 输入事件、热重载、线程分块、跨界开销
- [C# 基础](https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/c_sharp_basics.html)
- [API 差异](https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/c_sharp_differences.html)
- [信号](https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/c_sharp_signals.html)
- [集合](https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/c_sharp_collections.html)
- [导出](https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/c_sharp_exports.html)
- [跨语言脚本](https://docs.godotengine.org/en/stable/tutorials/scripting/cross_language_scripting.html)
