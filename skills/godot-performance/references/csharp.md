# C# 对照

SKILL.md 各节示例的 C# 写法。通用的 C# 规则与跨界开销见 godot-csharp。

## 测量

```csharp
public partial class BulletMonitor : Node
{
    private static readonly StringName MonitorId = "game/bullets";

    private int _bullets;

    public override void _Ready()
    {
        Performance.AddCustomMonitor(MonitorId, Callable.From(GetBulletCount));
    }

    public override void _ExitTree()
    {
        Performance.RemoveCustomMonitor(MonitorId);
    }

    public int GetBulletCount()
    {
        return _bullets;
    }
}
```

- Profiler 不显示 C# 方法，用 `System.Diagnostics.Stopwatch` 或 IDE 性能工具
- dotnet-counters 看 GC 次数与托管堆大小

## 回调开关

```csharp
public partial class Sleeper : Node2D
{
    public override void _Ready()
    {
        SetProcess(false);
        SetPhysicsProcess(false);
    }

    public void Activate()
    {
        SetPhysicsProcess(true);
    }

    public override void _PhysicsProcess(double delta)
    {
        Position += new Vector2(100.0f * (float)delta, 0.0f);
    }
}
```

- 只有重写了的回调才被引擎调用，不需要的就别重写
- 每次回调是一次引擎到托管的跨界，几百个实体改用管理器统一驱动

## MultiMesh

```csharp
public partial class DotField : MultiMeshInstance2D
{
    public override void _Ready()
    {
        Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform2D,
            UseColors = true,
            Mesh = new QuadMesh { Size = new Vector2(8.0f, 8.0f) },
            InstanceCount = 2000,
            VisibleInstanceCount = 0,
        };
    }

    public void ShowCount(int count)
    {
        Multimesh.VisibleInstanceCount = count;
        for (int i = 0; i < count; i++)
        {
            Multimesh.SetInstanceTransform2D(i, new Transform2D(0.0f, new Vector2(i * 10.0f, 0.0f)));
            Multimesh.SetInstanceColor(i, Colors.White);
        }
    }
}
```

- 对象初始化器按书写顺序赋值，实例数写在格式之后
- 每个 SetInstance 调用都是一次跨界，上千个实例改写 Buffer
- Buffer 用复用的 `float[]` 填好再赋值

## 线程

```csharp
public partial class ChunkedCompute : Node
{
    private const int Chunk = 256;

    private float[] _results = Array.Empty<float>();
    private long _taskId = -1;

    public void Start(int count)
    {
        _results = new float[count];
        int chunks = Mathf.CeilToInt(count / (float)Chunk);
        _taskId = WorkerThreadPool.AddGroupTask(Callable.From<int>(ComputeChunk), chunks, -1, true, "compute");
    }

    private void ComputeChunk(int chunk)
    {
        int end = Math.Min((chunk + 1) * Chunk, _results.Length);
        for (int i = chunk * Chunk; i < end; i++)
        {
            _results[i] = MathF.Sqrt(i);
        }
    }

    public override void _Process(double delta)
    {
        if (_taskId != -1 && WorkerThreadPool.IsGroupTaskCompleted(_taskId))
        {
            WorkerThreadPool.WaitForGroupTaskCompletion(_taskId);
            _taskId = -1;
            GD.Print(_results[0]);
        }
    }

    public override void _ExitTree()
    {
        if (_taskId != -1)
        {
            WorkerThreadPool.WaitForGroupTaskCompletion(_taskId);
        }
    }
}
```

- 纯托管计算也可用 `Parallel.For` 或 `Task.Run`，走 .NET 线程池
- 结果写进托管数组，主线程统一提交给引擎
- 线程里不调场景树 API，用 CallDeferred

## 加载卡顿

```csharp
public partial class LevelLoader : Node
{
    private const string LevelPath = "res://levels/level_1.tscn";

    private readonly Godot.Collections.Array _progress = new();

    public override void _Ready()
    {
        SetProcess(false);
    }

    public void StartLoad()
    {
        ResourceLoader.LoadThreadedRequest(LevelPath, "PackedScene", true);
        SetProcess(true);
    }

    public override void _Process(double delta)
    {
        switch (ResourceLoader.LoadThreadedGetStatus(LevelPath, _progress))
        {
            case ResourceLoader.ThreadLoadStatus.InProgress:
                GD.Print(_progress[0]);
                break;
            case ResourceLoader.ThreadLoadStatus.Loaded:
                SetProcess(false);
                GetTree().ChangeSceneToPacked(ResourceLoader.LoadThreadedGet(LevelPath) as PackedScene);
                break;
            default:
                SetProcess(false);
                GD.PushError("load failed");
                break;
        }
    }
}
```
