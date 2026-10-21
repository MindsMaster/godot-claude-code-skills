# 性能测量

SKILL.md 给了工具总表，这里是每项的细节：Profiler 读法、监视器清单、CPU 与 GPU 的判断、手动计时、命令行选项。

## Profiler

Debugger 面板的 Profiler 页。运行游戏后切回编辑器点 Start，勾 Autostart 则下次运行自动开始，该勾选不跨编辑器会话保存。

- 主要度量是 Frame Time、Physics Frame、Idle Time、Physics Time。Frame Time 含渲染，脚本和物理都正常却有尖峰时，往往是渲染侧，例如粒子或特效出现
- Idle 指 `_process()` 与按 Idle 更新的 Timer、相机，Physics 指 `_physics_process()` 与按 Physics 更新的内置节点
- Measure 下拉可选毫秒或占帧时间的百分比。作用域选 Inclusive 含子调用，选 Self 只算函数体，找耗时的函数用 Self
- 列表里除脚本函数还有 Physics 2D、Physics、Audio 等引擎项
- 平均值是函数被调用多次时的平均，一帧里调用 5 次每次 0.05 ms，平均 0.05 ms 总计 0.25 ms，看总计更直观
- Profiler 不支持 C# 脚本

## Visual Profiler

渲染阶段的 CPU 与 GPU 耗时，左边类别，右边 CPU 与 GPU 帧时间图。

- 只含渲染相关的 CPU 时间如绘制调用提交，不含脚本与物理
- 类别名后带 Parallel 的表示 GPU 上并行执行，只关掉其中一项收益不如预期
- 结果随视口分辨率变化，窗口大小模式为 `disabled` 或 `canvas_items` 时由窗口大小决定。对比时用同样的窗口
- 编辑器设置 `debugger/profiler_target_fps` 控制百分比视图的目标帧时间
- 图缩放被尖峰拉歪时关掉 Fit to Frame
- Compatibility 渲染器在 macOS 上不支持

## Monitors

Debugger 面板的 Monitors 页，所有监视器一直在记录，没打开页面时也能事后回看。数据来自 `Performance` 单例，`Performance.get_monitor(Performance.TIME_FPS)` 读取。

| 类别 | 常量 | 说明 |
|---|---|---|
| 时间 | `TIME_FPS` | 上一秒渲染帧数，每秒才更新一次 |
| 时间 | `TIME_PROCESS` | 一帧耗时，秒 |
| 时间 | `TIME_PHYSICS_PROCESS` | 一个物理帧耗时，秒 |
| 时间 | `TIME_NAVIGATION_PROCESS` | 一个导航步耗时，秒 |
| 内存 | `MEMORY_STATIC` `MEMORY_STATIC_MAX` | 已用与可用静态内存，字节，release 构建不可用 |
| 内存 | `MEMORY_MESSAGE_BUFFER_MAX` | 消息队列缓冲峰值，延迟调用与通知用 |
| 对象 | `OBJECT_COUNT` `OBJECT_RESOURCE_COUNT` `OBJECT_NODE_COUNT` | 对象、资源、场景树节点数 |
| 对象 | `OBJECT_ORPHAN_NODE_COUNT` | 不在场景树里的节点数，只在调试模式可用 |
| 渲染 | `RENDER_TOTAL_OBJECTS_IN_FRAME` | 上一帧渲染的对象数，不含被剔除的 |
| 渲染 | `RENDER_TOTAL_PRIMITIVES_IN_FRAME` | 上一帧顶点或索引数，含深度预通道与阴影通道，约为场景顶点数的两三倍 |
| 渲染 | `RENDER_TOTAL_DRAW_CALLS_IN_FRAME` | 上一帧绘制调用数 |
| 渲染 | `RENDER_VIDEO_MEM_USED` `RENDER_TEXTURE_MEM_USED` `RENDER_BUFFER_MEM_USED` | 显存、纹理、渲染缓冲，字节 |
| 物理 | `PHYSICS_2D_ACTIVE_OBJECTS` `PHYSICS_2D_COLLISION_PAIRS` `PHYSICS_2D_ISLAND_COUNT` | 2D 活动 RigidBody2D、碰撞对、岛数 |
| 物理 | `PHYSICS_3D_ACTIVE_OBJECTS` `PHYSICS_3D_COLLISION_PAIRS` `PHYSICS_3D_ISLAND_COUNT` | 3D 活动 RigidBody3D 与 VehicleBody3D、碰撞对、岛数 |
| 音频 | `AUDIO_OUTPUT_LATENCY` | 输出延迟，不要每帧读 |
| 导航 | `NAVIGATION_2D_AGENT_COUNT` `NAVIGATION_3D_AGENT_COUNT` 等 | 地图、区域、链接、多边形、障碍物、避障代理数量，2D 与 3D 分开的版本 4.5+ |
| 管线 | `PIPELINE_COMPILATIONS_CANVAS` `_MESH` `_SURFACE` `_DRAW` `_SPECIALIZATION` | 4.4+，只增不减 |

管线编译监视器的含义：

- `CANVAS`：绘制 2D 节点时编译，引擎没有 2D 预编译，首次绘制会卡
- `MESH`：加载网格时编译，运行中加载网格会卡，线程加载可缓解。节点上的材质覆盖不在这一步编译
- `SURFACE`：场景里 3D 对象首次实例化后、绘制前编译，包括不可见节点
- `DRAW`：绘制时按需编译，预编译没覆盖到。出现在这里是引擎没覆盖的情况，正常不该有
- `SPECIALIZATION`：后台优化编译，不会造成卡顿，每帧很多时可能降帧率

## 游戏内叠加

<!-- check: extends Label -->
```gdscript
func _ready() -> void:
	visible = OS.is_debug_build()
	set_process(visible)

func _process(_delta: float) -> void:
	var frame_ms := Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
	var draws := int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	text = "%d fps  %.2f ms  %d draws" % [Engine.get_frames_per_second(), frame_ms, draws]
```

## CPU 还是 GPU

- 关 V-Sync，对比大窗口与小窗口的 FPS。小窗口明显更快，说明受限于像素（填充率）。几乎不变，瓶颈在别处
- 填充率受限时：简化着色器、减少纹理读取、缩小阴影贴图、减少透明叠加、降低 `Viewport` 分辨率或用 `rendering/scaling_3d/mode` 缩放
- 绘制调用多时：2D 自动合批，3D 复用材质与着色器、预先合并静态网格、用 MultiMesh 画重复物体
- 用二分法加假设验证：关掉一类节点或一个系统看帧时间变化，比猜更快
- CPU 在脚本：Profiler 的 Self 排序。CPU 在渲染提交：Visual Profiler 的 CPU 条。GPU：Visual Profiler 的 GPU 条或 `--gpu-profile`
- 外部工具如 Nsight Graphics、Radeon GPU Profiler、PIX（仅 Direct3D 12）、Xcode（仅 Metal）看 GPU 更细
- 相对性能随硬件而变，移动端要在真机上测

## 手动计时

<!-- check: extends Node -->
```gdscript
func measure(action: Callable, runs: int = 1000) -> float:
	var start := Time.get_ticks_usec()
	for i in runs:
		action.call()
	return float(Time.get_ticks_usec() - start) / runs
```

- 重复 1000 次以上取平均，单次计时精度不够，也受 CPU 缓存影响，第一次通常最慢
- C# 同理：`Time.GetTicksUsec()` 前后相减

## 内存与泄漏

- Monitors 里 `OBJECT_NODE_COUNT`、`OBJECT_ORPHAN_NODE_COUNT` 持续上升，说明节点创建后没释放
- `Node.print_orphan_nodes()` 列出孤儿节点。摘出场景树的池化节点也算孤儿，属于预期
- ObjectDB Profiler 4.6+：Debugger 面板里对 ObjectDB 拍快照，比较两张快照的差异
- Video RAM 页按资源路径列出显存占用，查大纹理
- 对象快照不含引擎内部不暴露给脚本的类

## 命令行选项

| 选项 | 作用 |
|---|---|
| `--print-fps` | 打印帧率到标准输出 |
| `--disable-vsync` | 强制关闭垂直同步，不覆盖驱动层强制的 V-Sync |
| `--max-fps <fps>` | 限制最大帧率，0 为不限 |
| `--fixed-fps <fps>` | 固定帧率，禁用实时同步 |
| `--gpu-profile` | 打印帧渲染里最耗时的 GPU 任务 |
| `--gpu-validation` | 开启图形 API 验证层 |

项目设置里对应 `display/window/vsync/vsync_mode` 与 `application/run/max_fps`。
