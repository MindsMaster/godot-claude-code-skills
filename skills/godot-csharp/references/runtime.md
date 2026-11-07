# C# 运行时细节

集合与 Variant、对象生命周期、async、输入事件匹配、热重载与程序集卸载、线程、跨界开销、每帧分配、已释放对象、调试。

## 集合与 Variant

| 类型 | 规则 |
|---|---|
| `Godot.Collections.Array`、`Dictionary` | 每次读写过一次互操作，只在传给引擎或导出时用 |
| 内部状态 | 用 `List<T>`、`Dictionary<K, V>` |
| 两种集合互转 | `ToList()` `ToArray()` `new Array<T>(IEnumerable<T>)` 逐元素复制 |
| `new Array<T>(untypedArray)` | 只包装不复制 |
| `Variant` | 结构体不装箱，`Variant.Obj` 对值类型装箱，转换用 `As<T>()` |
| 枚举与 Variant | 无隐式转换，用 `Variant.From(e)` 与 `v.As<MyEnum>()` |
| 紧凑数组 | `PackedByteArray` 是 `byte[]`，传给引擎时复制一份 |

- Godot 集合上用 LINQ 每个元素都过互操作，热路径用 `for`
- Variant 里整数与浮点是 64 位，反向转换可能丢精度

## 对象生命周期

| 情况 | 做法 |
|---|---|
| 释放节点 | `QueueFree()` 或 `Free()`。`Dispose()` 只放托管侧，退出时报 ObjectDB 泄漏 |
| 已释放对象的引用 | 不变 `null`，访问抛 `ObjectDisposedException`，用 `GodotObject.IsInstanceValid(obj)` |
| `QueueFree()` 后帧末前 | `IsInstanceValid()` 仍为 `true`，再查 `IsQueuedForDeletion()` |
| `Image` `FileAccess` 这类 `RefCounted` | 靠 GC 终结器释放，大对象用 `using` |
| 持有可能被释放的对象 | `GodotObject.WeakRef(obj)` 或存 `GetInstanceId()` |

- 集合里存着已释放节点会留住它字段里的资源，见下文已释放对象一节

## async

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

| `await` 什么 | continuation 在哪 |
|---|---|
| `GodotObject.ToSignal` | 发射信号的线程，引擎信号在主线程 |
| 主线程发起的 `Task.Run(...)` | 下一次帧回调在主线程 |
| `ConfigureAwait(false)` 或线程池里发起的 | 线程池，其后不碰场景树 |

- `GodotObject.ToSignal` 的等待者被释放后连接断开，continuation 不执行也不报错
- `source` 调用时已释放抛 `ObjectDisposedException`，等待期间被释放则永不返回
- `await` 返回后先查 `IsInsideTree()`，用到的对象查 `IsInstanceValid()`
- `CreateTimer(1.0)` 暂停时照常计时，要随暂停第二参数传 `false`
- 没人 `await` 的 `Task` 异常不打印，入口 `try/catch` 并 `GD.PushError`
- `async void` 的异常由引擎在帧回调里打印
- 线程里碰场景树只能 `CallDeferred()`

## 输入事件模式匹配

```csharp
using Godot;

public partial class Player : Node2D
{
    public override void _UnhandledInput(InputEvent @event)
    {
        switch (@event)
        {
            case InputEventKey { Pressed: true, Echo: false, Keycode: Key.Escape }:
                GetTree().Quit();
                break;
            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left } click:
                GD.Print(click.Position);
                break;
            case InputEventMouseMotion motion:
                GD.Print(motion.Relative);
                break;
        }
        if (@event.IsActionPressed(Actions.Jump))
        {
            GetViewport().SetInputAsHandled();
        }
    }
}

public static class Actions
{
    public static readonly StringName Jump = "jump";
}
```

- 事件类型用 `case` 属性模式匹配，一次判断类型和字段
- 动作判断用 `@event.IsActionPressed(StringName)`，`StringName` 放静态字段，不写字符串字面量
- 每帧轮询用 `Input.IsActionPressed(Actions.Jump)`、`Input.GetVector(...)`，参数同样用 `StringName`
- `_UnhandledInput` 处理游戏输入，`_Input` 抢在 UI 之前，`_GuiInput` 属于 `Control`

## 热重载

- 重新构建时编辑器卸载用户程序集，重新加载后恢复实例
- 生成器为每个类生成 `SaveGodotObjectData` 与 `RestoreGodotObjectData`

| 成员 | 重载后 |
|---|---|
| 非静态、可读可写、Variant 兼容的字段与属性 | 恢复，含 private、private setter、未导出的 |
| 自定义信号 `+=` 订阅的委托 | 恢复 |
| 只读、`init`、静态 | 回到初始值，静态字段随旧程序集丢弃 |
| `List<T>`、.NET `Dictionary` 等非 Variant 类型 | 回到初始值 |
- 官方 c_sharp_basics 说只保存导出变量，与生成器源码不符，以源码为准
- 不可保存的状态实现 `ISerializationListener` 重建，`OnBeforeSerialize()` 在保存前调用，`OnAfterDeserialize()` 在恢复后调用
- 卸载失败时日志写 `Possible causes: Strong GC handles, running threads, etc.`
- 已知原因：字段里存着 `Callable`，对应 `[ExportToolButton]` 的 GD0111
- 已知原因：仍在运行的 `Task` 和 `Thread`
- 每次卸载最多等 1 秒，连续失败 `dotnet/project/assembly_reload_attempts` 次（默认 3）后日志报 `Giving up on assembly reloading`，需要重启编辑器
- `[Tool]` 脚本在重载时也在编辑器里运行，里面开的后台任务要在 `_ExitTree()` 里停

```csharp
using System.Collections.Generic;
using Godot;

public partial class Inventory : Node, ISerializationListener
{
    private Godot.Collections.Array<string> _ids = new();
    private readonly Dictionary<string, int> _index = new();

    public void OnBeforeSerialize()
    {
    }

    public void OnAfterDeserialize()
    {
        _index.Clear();
        for (int i = 0; i < _ids.Count; i++)
        {
            _index[_ids[i]] = i;
        }
    }
}
```

## 线程

```csharp
using Godot;

public partial class Crowd : Node
{
    private const int Chunk = 256;
    private readonly float[] _results = new float[4096];
    private long _taskId;

    public override void _Ready()
    {
        int chunks = (_results.Length + Chunk - 1) / Chunk;
        _taskId = WorkerThreadPool.AddGroupTask(Callable.From<int>(ComputeChunk), chunks, -1, true);
    }

    public override void _ExitTree()
    {
        WorkerThreadPool.WaitForGroupTaskCompletion(_taskId);
    }

    private void ComputeChunk(int chunk)
    {
        int end = Mathf.Min((chunk + 1) * Chunk, _results.Length);
        for (int i = chunk * Chunk; i < end; i++)
        {
            _results[i] = Mathf.Sqrt(i);
        }
    }
}
```

- `AddGroupTask()` 每个元素调一次 `Callable`，元素数传块数，每块处理一段下标
- 纯 C# 计算可用 `Parallel.For` 配 `Partitioner.Create(0, n, chunk)`
- `highPriority` 默认 `false`，低优先级任务同时最多占 `threading/worker_pool/low_priority_thread_ratio` 比例的线程，默认 0.3。每帧要等结果的任务传 `true`
- 每个 `AddTask()` 或 `AddGroupTask()` 都必须配对调用 `WaitForTaskCompletion()` 或 `WaitForGroupTaskCompletion()`，否则任务占用的资源不释放
- 任务里不碰场景树，不改共享的资源。结果写进各自独立的下标，主线程等完成后再读
- `WorkerThreadPool` 的任务不自动回主线程，结果用 `CallDeferred()` 交回
| 调用 | 线程 |
|---|---|
| 场景树操作 | 只在主线程，线程里用 `CallDeferred()` |
| `RenderingServer`、物理服务器的设置类调用 | 可在线程里调，排进命令队列 |
| 射线、形状查询、`MoveAndSlide()` | 只在主线程，`PhysicsServer3D.body_test_motion()` 与 `space_get_direct_state()` 只认主线程 |

- 开不开 `physics/3d/run_on_separate_thread` 都一样
- 在线程里构造不在树里的节点并组装是安全的，加入场景树用 `CallDeferred(Node.MethodName.AddChild, node)`
- `AStar2D`、`AStar3D`、`AStarGrid2D` 不是线程安全的，同一个实例只给一个线程用

## 跨界开销

普通引擎方法与属性走缓存好的方法指针直接调用，不经 Variant。下面这些多付一次分配、拷贝或按名查找：

```csharp
using Godot;

public partial class Trail : Line2D
{
    private readonly Vector2[] _points = new Vector2[32];

    public void Push(Vector2 head)
    {
        System.Array.Copy(_points, 0, _points, 1, _points.Length - 1);
        _points[0] = head;
        Points = _points;
    }
}
```

- Packed 数组属性每次读都在原生侧和托管侧各复制一整份
- 循环里写 `Points[i]` 每次迭代复制整个数组，改为持有托管数组，改完整体赋回
- 4.7.2 的绑定给 Packed 数组参数生成了 ReadOnlySpan 重载，传切片不分配托管数组，原生侧仍复制一次
- `Get("position")` `Set()` 先查脚本属性，再按名沿继承链查原生属性
- 类型已知就直接读写 C# 属性
- `_Process` `_PhysicsProcess` 每节点每帧一次跨界，空的覆写删掉
- 几百个同类节点由一个管理器统一驱动，见 godot-performance
- `GD.Print()` 分配 `object[]`、装箱、拼接再转码成引擎字符串，调试构建里默认每行刷新标准输出
- 可变参数方法 `Call()`、`CallDeferred()`、`EmitSignal()`、`Rpc()` 把全部参数转成 Variant，热路径用生成的事件或直接方法调用
- 单次普通跨界调用很便宜，先测再改
- 采样器偏向在跨界返回点取样，小调用显得很贵
- 实测采样显示占主线程 6% 的跨界调用，改掉后基准只快 2% 以内

## 每帧分配

`_Process` 里避免分配：

| 写法 | 改法 |
|---|---|
| `GetChildren()` | 每次新建原生数组和包装，用 `GetChildCount()` 加 `GetChild(i)`，或缓存 |
| LINQ、`ToArray()`、`ToList()`、`new List<T>()`、`new float[n]` | 缓冲区放字段，`Clear()` 复用 |
| 每帧捕获变量的 lambda | 分配闭包，需要 `Callable` 时缓存到字段 |
| `Call("m", a, b)`、`EmitSignal(name, a, b)` | `params` 分配数组，用强类型调用或 `Call("m", [a, b])` |
| 循环里读写原生属性 | 读到局部变量，最后写回一次 |
| 每帧拼接文本 | 数值没变就不更新 `Label.Text` |

- 不需要的节点 `SetProcess(false)`，不可见时不每帧 `QueueRedraw()`

## 已释放对象与包装对象

一个原生对象只有一个托管包装对象，所有 C# 引用都指向它。

- 节点释放时引擎对托管对象调 `Dispose()`，只清原生指针，字段原样保留
- C# 集合还存着该节点时，它字段里的材质、纹理包装对象一起留着
- 每个包装对象占一个原生引用，原生资源一直不释放
- 对共享的 `Resource` 调 `Dispose()`，原生资源不释放，所有持有者的引用一起失效
- 失效引用访问抛 `ObjectDisposedException`，`IsInstanceValid()` 为 `false`
- 共享资源不调 `Dispose()`，丢掉引用交给 GC
- 长期集合跟着对象生命周期删：加入时连对方的 `tree_exiting`，回调里移除
- 拿不到移除时机时存 `GetInstanceId()`，用时 `GodotObject.InstanceFromId()`，已释放返回 `null`
- 存 id 的集合也要有上界，下例在 `node_removed` 里删 id
- 不能只靠 `_Process` 清空，`PROCESS_MODE_DISABLED` 时 `_Process` 不跑，信号照常到

```csharp
using System.Collections.Generic;
using Godot;

public partial class MeshWatcher : Node
{
    private readonly HashSet<ulong> _pending = [];

    public override void _EnterTree()
    {
        GetTree().NodeAdded += OnNodeAdded;
        GetTree().NodeRemoved += OnNodeRemoved;
    }

    public override void _ExitTree()
    {
        GetTree().NodeAdded -= OnNodeAdded;
        GetTree().NodeRemoved -= OnNodeRemoved;
    }

    public override void _Process(double delta)
    {
        foreach (ulong id in _pending)
        {
            if (InstanceFromId(id) is MeshInstance3D mesh)
            {
                mesh.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
            }
        }
        _pending.Clear();
    }

    private void OnNodeAdded(Node node)
    {
        if (node is MeshInstance3D)
        {
            _pending.Add(node.GetInstanceId());
        }
    }

    private void OnNodeRemoved(Node node)
    {
        _pending.Remove(node.GetInstanceId());
    }
}
```

## 调试

- 内置 Profiler 不支持 C# 脚本
- 函数耗时用 `Time.GetTicksUsec()` 前后相减，或 Rider、dotTrace、`dotnet-trace collect -p <pid> --format Speedscope`
- 采样结果只用来找方向，改完用固定场景的基准前后对比
- 断点与单步在 IDE 里建调试配置，启动项目的 Godot 可执行文件，配置示例见官方 C# 基础文档
- 输出用 `GD.Print`，发布版剥离调试输出用 `OS.IsDebugBuild()` 判断
托管泄漏用 dotnet-dump 查：

```
dotnet tool install -g dotnet-dump
dotnet-dump collect -p <pid> --type Heap
dotnet-dump analyze <文件>
```

- analyze 里 `dumpheap -stat` 按类型列实例数，两次抓取对比涨的类型
- 对一个实例 `gcroot <地址>` 看谁持有它
