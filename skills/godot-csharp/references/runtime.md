# C# 运行时细节

输入事件匹配、热重载与程序集卸载、线程、跨界开销、调试。

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

- 重新构建时编辑器卸载用户程序集，重新加载后恢复实例。生成器给每个类生成 `SaveGodotObjectData` 与 `RestoreGodotObjectData`，保存范围是非静态、可读可写、Variant 兼容类型的字段与属性。private 成员算，导出与否都算，private setter 算，`init` 不算。自定义信号用 `+=` 订阅的委托也一并保存
- 官方 c_sharp_basics 写的是除导出变量外状态不保存，与生成器源码和 4.7.2 实测生成代码不一致，以源码为准
- 只读成员、`init` 属性、静态成员、`List<T>` 与 .NET `Dictionary` 等不兼容类型不保存，重载后回到初始值。静态字段随旧程序集丢弃
- 不可保存的状态实现 `ISerializationListener` 重建，`OnBeforeSerialize()` 在保存前调用，`OnAfterDeserialize()` 在恢复后调用
- 卸载失败时引擎日志写 `Possible causes: Strong GC handles, running threads, etc.`。官方文档点名的一例是字段或带后备字段的属性里存着 `Callable`，对应 `[ExportToolButton]` 的 GD0111。其他来源文档没有逐项列出，仍在运行的 `Task` 和 `Thread` 属于日志里的 running threads
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

- `AddGroupTask()` 每个元素调一次 `Callable`，元素传块数，每块处理一段下标，省掉逐元素的跨界调用。纯 C# 计算也可以用 `Parallel.For` 配 `Partitioner.Create(0, n, chunk)`
- `highPriority` 默认 `false`，低优先级任务同时最多占 `threading/worker_pool/low_priority_thread_ratio` 比例的线程，默认 0.3。每帧要等结果的任务传 `true`
- 每个 `AddTask()` 或 `AddGroupTask()` 都必须配对调用 `WaitForTaskCompletion()` 或 `WaitForGroupTaskCompletion()`，否则任务占用的资源不释放
- 任务里不碰场景树，不改共享的资源。结果写进各自独立的下标，主线程等完成后再读
- `WorkerThreadPool` 的任务不会自动回主线程，结果用 `CallDeferred()` 交回。在主线程发起的 `await Task.Run(...)` 的 continuation 下一帧回主线程，规则见 SKILL.md 的 async 一节
- 场景树只在主线程操作，线程里用 `CallDeferred()`。`RenderingServer` 与物理服务器的设置类调用可在线程里调，会排进命令队列。物理查询不行：`PhysicsServer3D.body_test_motion()` 与 `space_get_direct_state()` 只认主线程，所以射线、形状查询、`MoveAndSlide()` 都要留在主线程，开不开 `physics/3d/run_on_separate_thread` 都一样
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

- Packed 数组属性每次读都在原生侧和托管侧各复制一整份。循环里写 `Points[i]` 每次迭代复制整个数组。自己持有托管数组，改完整体赋回一次
- 4.7.2 的绑定给 Packed 数组参数生成了 ReadOnlySpan 重载，传切片不分配托管数组，原生侧仍复制一次
- `Get("position")` 与 `Set()` 先进引擎，再回调 C# 脚本实例找脚本属性，再按名沿继承链查原生属性。类型已知就直接读写属性，如 `Node2D.position` 对应的 C# 属性
- 引擎按方法名逐个节点分派 `_Process` 和 `_PhysicsProcess`，每次一个跨界。空的覆写删掉。几百个同类节点由一个管理器统一驱动，见 godot-performance 的 many-entities.md
- `GD.Print()` 分配 `object[]`、装箱、拼接再转码成引擎字符串，调试构建里默认每行刷新标准输出
- 可变参数方法 `Call()`、`CallDeferred()`、`EmitSignal()`、`Rpc()` 把全部参数转成 Variant，热路径用生成的事件或直接方法调用
- 单次普通跨界调用很便宜，先测再改。一个项目里 dotnet-trace 显示每帧沿父链找节点、四叉树重复读全局位置 合计占主线程 6%，改掉后基准只快 2% 以内，在噪声范围里。采样器偏向在跨界返回点取样，小调用会显得很贵

## 调试

- 内置 Profiler 不支持 C# 脚本，函数耗时用 `Time.GetTicksUsec()` 前后相减，或外部工具如 JetBrains Rider、dotTrace、`dotnet-trace collect -p <pid> --format Speedscope`。采样结果只用来找方向，改完用固定场景的基准前后对比
- 断点与单步在 IDE 里建调试配置，启动项目的 Godot 可执行文件，配置示例见官方 C# 基础文档
- 输出用 `GD.Print`，发布版剥离调试输出用 `OS.IsDebugBuild()` 判断
