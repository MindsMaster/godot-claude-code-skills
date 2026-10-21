# C# 运行时细节

输入事件匹配、热重载与程序集卸载、线程。

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

- 重新构建时编辑器卸载用户程序集，重新加载后恢复实例。生成器给每个类生成保存与恢复代码，范围是可读可写、非静态、Variant 兼容类型的字段与属性，导出与否都算
- 只读成员、`init` 属性、静态成员、`List<T>` 与 .NET `Dictionary` 等不兼容类型不保存，重载后回到初始值
- 静态字段里的托管对象随旧程序集一起丢弃，静态字段持有的 `GodotObject` 在重载后指向已释放对象
- 卸载要求没有外部对象引用用户程序集里的类型或委托。常见的外部引用有：仍在运行的 `Task`、`Thread`、`System.Threading.Timer`，对 .NET 静态事件（如 AppDomain 的事件）的订阅，缓存了用户类型的序列化器
- 卸载没完成时编辑器按 `dotnet/project/assembly_reload_attempts` 重试，默认 3，也是等待卸载的秒数
- `[Tool]` 脚本在重载时也在编辑器里运行，里面开的后台任务要在 `_ExitTree()` 里停

## 线程

```csharp
using Godot;

public partial class Crowd : Node
{
    private readonly float[] _results = new float[256];
    private long _taskId;

    public override void _Ready()
    {
        _taskId = WorkerThreadPool.AddGroupTask(Callable.From<int>(Compute), _results.Length);
    }

    public override void _ExitTree()
    {
        WorkerThreadPool.WaitForGroupTaskCompletion(_taskId);
    }

    private void Compute(int index)
    {
        _results[index] = Mathf.Sqrt(index);
    }
}
```

- 每个 `AddTask()` 或 `AddGroupTask()` 都必须配对调用 `WaitForTaskCompletion()` 或 `WaitForGroupTaskCompletion()`，否则任务占用的资源不释放
- 任务里不碰场景树，不改共享的资源。结果写进各自独立的下标，主线程等完成后再读
- `WorkerThreadPool` 的任务不会自动回主线程，结果用 `CallDeferred()` 交回。`await Task.Run(...)` 的 continuation 会回主线程
- 场景树只在主线程操作，线程里用 `CallDeferred()`。服务器 API（`RenderingServer`、`PhysicsServer2D` 等）线程安全，渲染与物理服务器需要在项目设置里开启线程模型
- 在线程里构造不在树里的节点并组装是安全的，加入场景树用 `CallDeferred(Node.MethodName.AddChild, node)`
- `AStar2D`、`AStar3D`、`AStarGrid2D` 不是线程安全的，同一个实例只给一个线程用

## 调试

- 内置 Profiler 不支持 C# 脚本，函数耗时用 `Time.GetTicksUsec()` 前后相减，或外部工具如 JetBrains Rider 与 dotTrace
- 断点与单步用 IDE 附加调试器
- 输出用 `GD.Print`，发布版剥离调试输出用 `OS.IsDebugBuild()` 判断
