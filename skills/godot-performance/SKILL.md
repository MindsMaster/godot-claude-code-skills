---
name: godot-performance
description: 排查和优化卡顿掉帧时用。先测再改：Debugger Profiler、Visual Profiler、Monitors、Performance.get_monitor、add_custom_monitor。热点的内置解法：MultiMesh、RenderingServer 与 PhysicsServer 直接调用、对象池、VisibleOnScreenEnabler、set_process(false)、物理插值 physics_interpolation、WorkerThreadPool、ResourceLoader 线程加载、着色器编译卡顿 pipeline ubershader、每帧字符串与分配。Godot performance profiling, stutter, frame drops, optimization.
---

# Godot 性能

先测再改：定位瓶颈，选内置方案，再测一次确认。不管具体渲染特效，也不管 GDScript 与 C# 的语法写法，那些去 godot-gdscript 与 godot-csharp。

目标 4.7，最低 4.4。

## 先查内置

| 现象 | 用这个 | 别自己写 |
|---|---|---|
| 数千个相同物体 | `MultiMeshInstance2D`、`MultiMeshInstance3D` 加 `MultiMesh` | 每个物体一个 Sprite 或 MeshInstance 节点 |
| 数千颗 2D 子弹或粒子 | `RenderingServer` 的 canvas item 与 `PhysicsServer2D`，或 `MultiMesh` 加数组存状态，至少做对象池 | 每颗子弹一个 Area2D 加 Sprite2D 节点 |
| 屏幕外的敌人或装置仍在运行 | `VisibleOnScreenEnabler2D`、`VisibleOnScreenEnabler3D` | 手写矩形相交判断 |
| 只用于事件响应的节点 | 去掉空的 `_process`，`set_process(false)` | 空 `_process` 留着 |
| 周期逻辑 | `Timer` 节点 | `_process` 里累加计时 |
| 移动抖动 | 物理插值 | 在 `_process` 里手动推进物理体 |
| 大批量计算 | `WorkerThreadPool.add_group_task()` | 自建 `Thread` 池 |
| 进关卡或换场景卡顿 | `ResourceLoader.load_threaded_request()` 加轮询 | 玩法中途同步 `load()` |
| 特效第一次出现卡一下 | 预热场景，看 Pipeline 监视器 | 运行时第一次才实例化特效 |
| 频繁创建销毁同类节点 | 对象池 | 每次 `instantiate()` 再 `queue_free()` |
| 找固定目标 | 分组加缓存引用，或信号 | 每帧遍历全部对象做字符串比较 |
| 项目自己的指标 | `Performance.add_custom_monitor()` | `print` 刷屏 |
| 调试文本 | `OS.is_debug_build()` 里按需更新 | 每帧对整个状态求哈希只为显示 |

## 先测

步骤：确认是 CPU 还是 GPU，再用对应工具定位到函数或渲染阶段，改一处，再测。

| 工具 | 位置 | 看什么 |
|---|---|---|
| Profiler | Debugger 面板 | 脚本函数、物理、音频耗时，选 Self 而不是 Inclusive 找耗时的函数体 |
| Visual Profiler | Debugger 面板 | 渲染各阶段的 CPU 与 GPU 耗时，不含脚本与物理 |
| Monitors | Debugger 面板 | FPS、节点数、孤儿节点、绘制调用、显存、物理对子数、Pipeline 编译数 |
| Video RAM | Debugger 面板 | 每个资源占用的显存 |
| ObjectDB Profiler | Debugger 面板 4.6+ | 对象快照与差异，查泄漏 |
| 手动计时 | 代码 | `Time.get_ticks_usec()` 前后相减，跑 1000 次取平均 |

- Profiler 默认不运行，手动点 Start，运行时会拖慢游戏。Profiler 不支持 C# 脚本，C# 用手动计时或 IDE 的性能工具
- 判断是否填充率受限：关 V-Sync，命令行用 `--disable-vsync`，对比大窗口与小窗口的 FPS，小窗口明显更快说明受限于像素
- 命令行 `--print-fps` 打印帧率，`--gpu-profile` 打印帧内最耗时的 GPU 任务
- Visual Profiler 的结果随视口大小变化，对比前后要用同样的窗口
- 编辑器里运行带额外开销，以导出构建为准

### 自定义监视器

```gdscript
extends Node

var _bullets: int = 0

func _ready() -> void:
	Performance.add_custom_monitor("game/bullets", get_bullet_count)

func _exit_tree() -> void:
	Performance.remove_custom_monitor("game/bullets")

func get_bullet_count() -> int:
	return _bullets
```

- id 里的斜杠分类，没有斜杠归到 Custom。回调返回非负数
- 同一个 id 重复添加报错，场景重载前先 `remove_custom_monitor()`
- `add_custom_monitor()` 第四个参数 `type` 是 4.6+，用来标注数量、内存、时间、百分比
- 游戏内叠加显示用 `Performance.get_monitor(Performance.TIME_FPS)` 与 `Performance.get_custom_monitor("game/bullets")`，放在 `OS.is_debug_build()` 里

更多监视器常量、Profiler 用法、CPU 与 GPU 判断见 [references/profiling.md](references/profiling.md)。

## 关掉不需要的回调

```gdscript
extends Node2D

func _ready() -> void:
	set_process(false)
	set_physics_process(false)

func activate() -> void:
	set_physics_process(true)

func _physics_process(delta: float) -> void:
	position.x += 100.0 * delta
```

- 定义了 `_process` 或 `_physics_process` 的节点默认开启回调，`_ready()` 里按需关闭
- `hide()` 只是不绘制，回调仍在跑。要停整棵子树用 `process_mode = Node.PROCESS_MODE_DISABLED`
- 区域或关卡整体不用时，`remove_child()` 摘出场景树，比暂停或隐藏省得多，需要时再 `add_child()`。摘出的节点要自己保存引用并在不再需要时 `free()`
- 大量互不依赖的节点处理可设 `process_thread_group`，组内不能访问组外节点，跨组用 `call_deferred()` 或 `call_deferred_thread_group()`

### 屏幕外自动停用

```ini
[node name="Enemy" type="CharacterBody2D" parent="."]

[node name="Enabler" type="VisibleOnScreenEnabler2D" parent="Enemy"]
rect = Rect2(-64, -64, 128, 128)
```

目标节点默认是父节点，`enable_node_path` 默认 `..`，区域进入屏幕时启用，离开时设为 `PROCESS_MODE_DISABLED`。只要信号不要自动开关时用 `VisibleOnScreenNotifier2D` 的 `screen_entered` 与 `screen_exited`。它们依赖渲染剔除，节点 `visible` 为 `false` 时不工作。3D 同名类用 `aabb`。

## MultiMesh

```gdscript
extends MultiMeshInstance2D

func _ready() -> void:
	var quad := QuadMesh.new()
	quad.size = Vector2(8.0, 8.0)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_2D
	mm.use_colors = true
	mm.mesh = quad
	mm.instance_count = 2000
	mm.visible_instance_count = 0
	multimesh = mm

func show_count(count: int) -> void:
	multimesh.visible_instance_count = count
	for i in count:
		multimesh.set_instance_transform_2d(i, Transform2D(0.0, Vector2(i * 10.0, 0.0)))
		multimesh.set_instance_color(i, Color.WHITE)
```

- 先设 `transform_format`、`use_colors`、`use_custom_data`，最后设 `instance_count`，之后改格式无效
- 一次分配最大数量，用 `visible_instance_count` 控制显示数量
- 不能按实例做视锥剔除，整体全画或全不画。分散的实例按区域拆成多个 MultiMesh，并设置 `custom_aabb` 避免每次重算包围盒
- 每个实例的动画用 shader 里的 `INSTANCE_ID` 与 `INSTANCE_CUSTOM`，状态用 `set_instance_custom_data()` 传入
- 一次性写全部实例用 `PackedFloat32Array` 类型的 `buffer`，比逐个 `set_instance_*` 快，C# 或 C++ 里在线程里填好再赋值
- 2D 实例用 `set_instance_transform_2d()`，3D 用 `set_instance_transform()`

## 直接用 Server

数千个每帧都要处理的对象，场景树的节点开销成为瓶颈时，绕过节点直接调服务器。完整示例与对象池见 [references/hotspots.md](references/hotspots.md)。

- `RenderingServer.canvas_item_create()` 加 `canvas_item_add_texture_rect()` 画 2D 精灵，`canvas_item_set_transform()` 每帧更新位置。碰撞用 `PhysicsServer2D.area_create()` 加 `area_add_shape()` 加 `area_set_space()`，官方示例是 Bullet Shower 演示项目
- 服务器对象用 `RID` 引用，没有引用计数，必须 `free_rid()`，漏掉就是泄漏
- 服务器 API 线程安全，渲染与物理服务器需要在项目设置里开启线程模型才能在线程里用
- 状态存进 `PackedVector2Array` 等紧凑数组，不为每个对象建 `RefCounted`
- 先试 MultiMesh 与对象池，它们够用就不要上服务器
- 对象池：节点用完 `remove_child()` 放进数组，复用时重置状态再 `add_child()`，池里的节点是孤儿，退出时手动 `free()`

## 物理 tick 与插值

```ini
[physics]

common/physics_ticks_per_second=30
common/physics_interpolation=true
```

- `physics/common/physics_ticks_per_second` 默认 60，降低能直接减少物理与 `_physics_process` 的 CPU，代价是模拟更粗
- 开启 `physics/common/physics_interpolation` 后渲染在物理帧之间插值，低 tick 率也平滑。2D 自 4.3，3D 自 4.4
- 移动和游戏逻辑放 `_physics_process()`，在 `_process()` 里移动会抖，间接移动也算，如移动父节点、Tween、AnimationPlayer
- 瞬移后先设变换，再 `reset_physics_interpolation()`，顺序反了会拖尾
- 插值会增加依赖物理 tick 的输入延迟，可以用更高的 tick 率补偿
- 3D 的相机或自定义插值可读 `Node3D.get_global_transform_interpolated()`，2D 没有对应方法
- `physics/common/max_physics_steps_per_frame` 默认 8，限制单帧最多模拟步数，防止卡顿越滚越大
- `_physics_process()` 里大量查询复用 `PhysicsRayQueryParameters2D` 对象，不每次新建

## 线程

```gdscript
extends Node

var _results: Array[float] = []
var _task_id: int = -1

func start(count: int) -> void:
	_results.resize(count)
	_task_id = WorkerThreadPool.add_group_task(_compute, count, -1, false, "compute")

func _compute(index: int) -> void:
	_results[index] = sqrt(float(index))

func _process(_delta: float) -> void:
	if _task_id != -1 and WorkerThreadPool.is_group_task_completed(_task_id):
		WorkerThreadPool.wait_for_group_task_completion(_task_id)
		_task_id = -1
		print(_results[0])

func _exit_tree() -> void:
	if _task_id != -1:
		WorkerThreadPool.wait_for_group_task_completion(_task_id)
```

- 优先 `WorkerThreadPool`，线程在启动时已创建。自建 `Thread` 创建开销大，在 Windows 上更明显，需要时在加载阶段创建好，且结束时必须 `wait_to_finish()`
- 每个任务都必须调用 `wait_for_task_completion()` 或 `wait_for_group_task_completion()`，否则资源不释放
- 场景树不是线程安全的，线程里只能 `call_deferred()`、`set_deferred()`。不在树里的节点可以在线程里创建和组装，加入场景树用 `add_child.call_deferred(node)`
- GDScript 的 Array 与 Dictionary 允许多线程读写元素，改变大小要加 `Mutex`
- 线程里避免需要同步 GPU 的操作，如创建纹理、读取图像数据
- 任务内容太轻，线程调度开销大于收益。先用 Profiler 确认是计算量大
- `AStar2D`、`AStar3D`、`AStarGrid2D` 不是线程安全的，一个实例只给一个线程用

## 加载卡顿

```gdscript
extends Node

const LEVEL_PATH := "res://levels/level_1.tscn"
var _progress: Array = []

func _ready() -> void:
	set_process(false)

func start_load() -> void:
	ResourceLoader.load_threaded_request(LEVEL_PATH, "PackedScene", true)
	set_process(true)

func _process(_delta: float) -> void:
	var status := ResourceLoader.load_threaded_get_status(LEVEL_PATH, _progress)
	match status:
		ResourceLoader.THREAD_LOAD_IN_PROGRESS:
			print(_progress[0])
		ResourceLoader.THREAD_LOAD_LOADED:
			set_process(false)
			var scene := ResourceLoader.load_threaded_get(LEVEL_PATH) as PackedScene
			get_tree().change_scene_to_packed(scene)
		_:
			set_process(false)
			push_error("load failed")
```

- `load_threaded_request()` 之后立刻 `load_threaded_get()` 会阻塞到加载完，等于同步加载。用 `load_threaded_get_status()` 轮询，`THREAD_LOAD_LOADED` 后再取
- `progress` 数组返回一个元素，值 0 到 1，可驱动进度条
- 加载在后台，`instantiate()` 大场景仍在主线程，大场景实例化也会卡。拆成小场景分帧添加，或在一个线程里实例化再 `add_child.call_deferred()`，不要多个线程同时碰同一个资源
- `@export` 的 `Resource` 会随场景一起加载，大关卡场景引用用 `@export_file` 存路径，用时线程加载
- 直接改共享资源的属性会污染 `ResourceLoader` 缓存，需要独立副本用 `duplicate()`

## 着色器编译卡顿

Forward+ 与 Mobile 渲染器自 4.4 起用 ubershader 与加载时预编译管线，Compatibility 渲染器没有。

- 效果第一次出现卡一下，打开 Monitors 里的 Pipeline 编译类监视器，如 `Performance.PIPELINE_COMPILATIONS_SURFACE`。游戏中数字突增就是在那一刻编译
- 运行中才实例化的特效，在关卡加载时把它的场景实例化一次，隐藏或放在屏幕外即可，引擎因此预编译管线
- 用到的渲染特性如反射探针、SDFGI、VoxelGI、TAA、SSAO 尽早出现在场景里，运行中途开关会触发重编译。MSAA 级别运行中改也会卡
- Compatibility 渲染器：加载关卡时把每种网格和特效在相机前显示一帧，用全屏 `ColorRect` 盖住
- `rendering/rendering_device/pipeline_cache/enable` 默认 `true`，把管线缓存写盘，二次运行更快。想模拟首次运行体验才关，并清理驱动缓存
- 导出设置里的 Shader Baker 4.5+ 把着色器中间码打进 PCK，缩短首次启动，不解决运行中的编译卡顿

## 每帧分配与字符串

- `_process` 里每帧创建 Array、Dictionary、字符串、Callable，会产生分配压力。缓冲区放成员变量复用，`clear()` 即可
- `str()`、`%`、字符串拼接每帧给 Label 赋值，数值没变就不更新
- `get_tree().get_nodes_in_group()` 每次返回新数组，不要每帧调用。目标固定时缓存引用，`get_first_node_in_group()` 在 `_ready()` 里取一次
- 对 N 个对象的每一个线性扫描 M 个对象，是 N 乘 M。先建 Dictionary 或按分组索引，一次性算好再查
- 比较名字用 `StringName` 字面量 `&"boss"`，不对每个对象做 `String` 比较
- 调试信息、哈希、统计只在 `OS.is_debug_build()` 为真且面板可见时计算。它在编辑器和调试模板里为真，release 模板里为假
- C# 的分配问题见 godot-csharp：`StringName` 缓存、LINQ、`GetChildren()`

## 陷阱

- 优化前后数据没有对比，改动可能是噪声。固定场景、固定窗口大小、多次取平均
- 小窗口测试判断填充率前要先关 V-Sync，否则 FPS 被刷新率封顶
- 空的 `_process()` 也会被每帧调用，删掉而不是留 `pass`
- 对象池里的节点隐藏后碰撞和计时器仍在运行
- `queue_free()` 的节点到帧末才释放，Monitors 的节点数不会立刻下降
- 孤儿节点监视器 `Performance.OBJECT_ORPHAN_NODE_COUNT` 持续增长说明节点摘出场景树后没有释放，`Node.print_orphan_nodes()` 列出它们
- `RenderingServer` 与 `PhysicsServer2D` 创建的 RID 不随节点释放
- 每帧线程里直接访问场景树，报错不一定每次出现，竞态难复现
- 帧率封顶在刷新率附近，优化效果要看毫秒帧时间，不看 FPS

## 参考

- [references/profiling.md](references/profiling.md) 监视器清单、Profiler 用法、CPU 与 GPU 判断、命令行选项
- [通用优化](https://docs.godotengine.org/en/stable/tutorials/performance/general_optimization.html)
- [CPU 优化](https://docs.godotengine.org/en/stable/tutorials/performance/cpu_optimization.html)
- [GPU 优化](https://docs.godotengine.org/en/stable/tutorials/performance/gpu_optimization.html)
- [使用 Server](https://docs.godotengine.org/en/stable/tutorials/performance/using_servers.html)
- [MultiMesh](https://docs.godotengine.org/en/stable/tutorials/performance/using_multimesh.html)
- [线程安全 API](https://docs.godotengine.org/en/stable/tutorials/performance/thread_safe_apis.html)
- [管线编译卡顿](https://docs.godotengine.org/en/stable/tutorials/performance/pipeline_compilations.html)
- [物理插值](https://docs.godotengine.org/en/stable/tutorials/physics/interpolation/physics_interpolation_introduction.html)
