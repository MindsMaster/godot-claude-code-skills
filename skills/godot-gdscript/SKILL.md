---
name: godot-gdscript
description: 写或改 GDScript 时用。静态类型 :=、Array[T]、Dictionary[K, V]、class_name、preload、@export 系列、@onready、signal connect emit bind lambda、await 协程、match、static var、StringName、is_instance_valid、setter getter、super、assert push_error、call_deferred、项目警告设置 warnings。GDScript typing, annotations, signals, coroutine, warning settings.
---

# GDScript 写法

语言层的写法与陷阱：类型、注解、信号、协程、警告。节点选型、场景组织、数据资源不在这里。C# 写法去 godot-csharp，卡顿与分配去 godot-performance。

目标 4.7，最低 4.4。示例按 4.4 可运行写，更新的特性标版本号。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 延时一次 | `await get_tree().create_timer(t).timeout` 或 Timer 节点 | `_process` 里累加 delta |
| 周期执行 | Timer 节点的 `timeout` 信号 | `_process` 里 `if elapsed > 0.5` |
| 输入轴 | `Input.get_vector()`、`Input.get_axis()` | 手写正负键相减 |
| 数值靠近目标 | `move_toward()`、`lerp()`、`Tween` | 手写 SmoothDamp |
| 取子节点 | `%Name` 唯一名、`@export var x: Node`、`@onready` | 长硬路径 `get_node("../../A/B")` |
| 枚举名字互转 | `State.keys()`、`State.find_key(v)`、`State["RUN"]` | match 字符串表 |
| 数组变换 | `filter` `map` `reduce` `any` `all` `pick_random` `sort_custom` | for 加临时数组 |
| 随机 | `randi_range()`、`randf_range()`、`RandomNumberGenerator` | 自写 LCG |
| 浮点比较 | `is_equal_approx()`、`is_zero_approx()` | `==` 比较浮点 |
| 帧末调用 | `callable.call_deferred()`、`set_deferred()` | 用 Timer 凑一帧 |
| 数据放 Inspector 里改 | `Resource` 子类加 `@export` | JSON 手写解析 |

## 静态类型

```gdscript
extends Node

var speed: float = 200.0
var hp := 10
var names: Array[String] = []
var scores: Dictionary[StringName, int] = {}
var target: Node2D

func take_damage(amount: int) -> bool:
	hp -= amount
	return hp <= 0

func _ready() -> void:
	var raw: Dictionary = {"k": 1}
	var value: int = raw["k"]
	var sprite := get_node_or_null("Sprite") as Sprite2D
	print(value, sprite)
```

- `:=` 从右值推断，右值是 Variant 时是错误 `inference_on_variant`。无类型 Dictionary 取值、`call()` 返回值都是 Variant，写 `var v: int = raw["k"]`
- `load()` 返回 `Resource`，要具体类型写 `var tex: Texture2D = load(path)`。路径是常量字符串时用 `preload()`，它带出具体类型
- `$Node` 和 `get_node()` 返回 `Node`，写 `@onready var sprite: Sprite2D = $Sprite`，场景里类型不符时加载处立即报错。`as` 失败静默得 `null`，只在就要这个结果时用
- `Array[T]` 运行时强制元素类型。`map()` 返回无类型 Array，赋给 `Array[T]` 变量报错，用 `typed.assign(untyped)`。`filter()` 保留源数组的元素类型
- `Dictionary[K, V]` 4.4+，不支持再嵌套类型，`Dictionary[String, Dictionary]` 可以
- 循环变量写类型 4.2+：`for n: Node in nodes:`
- 大量数值用 `PackedFloat32Array`、`PackedVector2Array`，`Array[float]` 仍是 Variant 数组
- 枚举做类型时本质是 `int`，传整数给枚举参数触发 `int_as_enum_without_cast`，写成员名或显式转换
- 对象类型可为 `null`，数值与字符串类型不可

## class_name 与 preload

- `class_name Foo` 注册全局类，任何脚本可直接当类型和构造。类名不能与 autoload 同名，报 `Class "Foo" hides an autoload singleton`，也不能与引擎类同名
- 没有 `class_name` 的脚本用常量引用，`preload` 参数必须是常量字符串，加载发生在脚本解析时。路径运行时才定用 `load()`

<!-- check: skip -->
```gdscript
const Rifle := preload("res://weapons/rifle.gd")

var main_weapon: Rifle = Rifle.new()
```

- 两个脚本互相 `preload` 在 4.7 可加载。仍建议用 `class_name` 打断环
- `@export` 类型只能是内置类型、`Resource`、`Node`、枚举，继承 `RefCounted` 的内部类是解析错误
- 3.x 的 `export var`、`onready var`、`yield`、`connect("sig", obj, "method")` 在 4.x 都没了

## 注解

```gdscript
extends Node2D

@export var speed: float = 200.0
@export_range(0.0, 1.0, 0.01) var ratio := 0.5
@export_enum("Idle", "Run") var mode: int = 0
@export_file("*.tscn") var next_scene: String
@export var bullet_scene: PackedScene
@export var spawn_point: Marker2D
@export_flags_2d_physics var hit_mask: int

@export_group("Loot")
@export var drops: Array[Resource] = []

@onready var label: Label = %Label
@onready var timer: Timer = $Timer

func _ready() -> void:
	timer.start()
	label.text = str(speed)
```

全表见 [references/annotations.md](references/annotations.md)。

- `@export` 的类型来自标注或默认值，两者都没有是解析错误，要 Variant 写 `: Variant`
- `@export var n: Node` 只在 Node 派生脚本里可用，`Resource` 里导出 Node 是解析错误
- 顺序是声明初值，`_init()`，场景里保存的值赋入，`_ready()`。`_init()` 里读到的是默认值
- 导出变量的 setter 在场景实例化时先于 `_ready()` 调用，此时 `@onready` 变量是 `null`，setter 里判断 `is_node_ready()`
- `@onready` 与 `@export` 同用是错误 `onready_with_export`。成员默认值里用 `$` 不带 `@onready` 是错误 `get_node_default_without_onready`
- 代码里 `add_child()` 创建的节点直接赋成员，不需要 `@onready`
- 场景里已存的属性值覆盖脚本新默认值，改默认值不会改已保存过该属性的场景
- 导出 `Resource` 会在场景加载时一并加载，大关卡场景用 `@export_file` 存路径，用时再 `load()`。4.5+ 它存 UID，要原始路径用 `@export_file_path`
- `@export_tool_button("名字")` 4.4+，必须配 `@tool`

## 信号

```gdscript
extends Node

signal died
signal damaged(amount: int, source: Node)

@export var button: Button

func _ready() -> void:
	button.pressed.connect(_on_pressed)
	damaged.connect(_log_damage.bind("player"))
	died.connect(queue_free, CONNECT_ONE_SHOT)

func _on_pressed() -> void:
	damaged.emit(3, self)

func _log_damage(amount: int, _source: Node, tag: String) -> void:
	print(tag, amount)
```

- `bind()` 的参数追加在发射参数之后，`unbind(n)` 丢掉末尾 n 个发射参数
- 同一个 Callable 连两次返回 `ERR_INVALID_PARAMETER` 并打印错误，先 `is_connected()` 判断
- `CONNECT_ONE_SHOT` 触发一次后断开，`CONNECT_DEFERRED` 推迟到帧末
- 接收者释放时连接自动断开，lambda 捕获了 `self` 成员时也一样
- 声明后类内没有 emit、connect、await 任何使用触发 `unused_signal`，由外部发射的信号加 `@warning_ignore("unused_signal")`
- 信号参数类型写在声明里供文档和补全，`emit()` 不检查，接收方法的参数类型不符时调用报错

```gdscript
extends Node

func _ready() -> void:
	var stats: Dictionary = {"count": 0}
	var bump := func() -> void:
		stats["count"] += 1
	bump.call()
	bump.call()
	print(stats["count"])
```

局部变量在创建 lambda 时按值捕获一次。lambda 里 `count += 1` 只改 lambda 内的副本，外面不变，还触发 `confusable_capture_reassignment`。要回写就捕获 Array、Dictionary 或对象，改其内容。

## await 与协程

```gdscript
extends Node

signal answered(choice: int)

func open_door(door: Node3D) -> void:
	await get_tree().create_timer(1.0).timeout
	if not is_inside_tree() or not is_instance_valid(door):
		return
	door.hide()

func ask() -> int:
	var choice: int = await answered
	return choice
```

- 函数体里有 `await` 就是协程。调用者不 `await` 时，协程跑到第一个 `await` 就返回，调用者继续往下。`missing_await` 默认关闭，开启能抓到漏写
- 信号带 1 个参数时 `await` 得到该值，多个参数得到 Array，无参数得到 `null`
- `await` 之后世界已变：目标节点可能已释放，自己可能已离开场景树，此时 `get_tree()` 打印错误并返回 `null`，下一个 `await get_tree()...` 报空值调用错误
- 自己被 `free()` 时挂起的协程不再恢复也不报错，`await` 后面的清理与状态复位都不执行。要清理的状态放 `_exit_tree()` 或 `tree_exiting` 里复位
- `create_timer(time_sec, process_always = true)` 默认暂停时也走，要受暂停影响传 `false`
- `await get_tree().process_frame` 等一帧，`physics_frame` 等物理帧，`await node.ready` 等就绪
- 没有内置超时，用 Timer 的 `timeout` 与业务信号谁先到谁处理

## 对象有效性

- 已 `free()` 的对象变量不会自动变 `null`，访问报 `previously freed`。`is_instance_valid(obj)` 判断是否还在
- `queue_free()` 之后到帧末之前 `is_instance_valid()` 仍为真，判断待删除用 `is_queued_for_deletion()`
- 物理回调、信号回调、遍历子节点时释放节点用 `queue_free()`，不用 `free()`
- `RefCounted` 与 `Resource` 靠引用计数，不会悬空，也不用 `free()`
- 长期持有可能被释放的节点，存 `weakref(node)`，用时 `get_ref()`
- `_init()` 里 `get_node()` 失败，节点此时不在树里。要树的逻辑放 `_ready()` 或 `_enter_tree()`

## 断言与日志

- `assert(cond, "msg")` 只在调试构建运行，发布版整句不执行，条件里不写有副作用的表达式
- `push_error(...)` 与 `push_warning(...)` 写进调试器错误面板和终端，带调用栈，不中断执行。需要上报的错误用它们，不用 `print`
- `print_rich("[color=red]x[/color]")` 支持 BBCode，`printerr` 写 stderr，`breakpoint` 关键字在调试器里停住
- 调试输出放 `if OS.is_debug_build():` 里

## Callable 与延迟调用

```gdscript
extends Node

func _ready() -> void:
	var child := Node.new()
	add_child.call_deferred(child)
	set_deferred(&"process_mode", Node.PROCESS_MODE_DISABLED)
	var sorted: Array[int] = [3, 1, 2]
	sorted.sort_custom(func(a: int, b: int) -> bool: return a > b)
```

- `call_deferred` 在当前帧空闲阶段末尾执行，返回值永远是 `null`
- 物理回调里改碰撞形状、`Area2D.monitoring`、`CollisionShape2D.disabled` 要用 `set_deferred`，直接改报 `Can't change this state while flushing queries`，改 `monitoring` 报 `Function blocked during in/out signal`
- 线程里碰场景树只能 `call_deferred`
- 方法引用直接写 `_on_pressed`，不写 `Callable(self, "_on_pressed")`，改名时前者会被检查到
- `callable.is_valid()` 判断绑定对象是否还在

## 陷阱

match 的绑定与守卫、静态成员、setter、super 的完整写法见 [references/syntax.md](references/syntax.md)。

- 整数除法 `5 / 2` 是 `2`，触发 `integer_division`。要小数写 `5 / 2.0` 或 `float(a) / b`
- Array 和 Dictionary 按引用传递，`var b = a` 两个变量指向同一份。拷贝用 `duplicate()`，嵌套用 `duplicate(true)`
- `const` 数组和字典只读，`append` 报 `Array is in read-only state`
- 子类写了 `_init()` 不会自动调父类 `_init()`，`_ready()` 同理，要显式 `super()`
- 声明初值不调 setter，类内其他方法里的赋值才调
- 未使用的参数加下划线前缀 `_delta` 不触发 `unused_parameter`
- 浮点传给整数参数触发 `narrowing_conversion`，显式 `int()`、`roundi()`、`floori()`
- 遍历数组时增删元素会跳项。遍历副本 `arr.duplicate()` 或倒序下标
- `call("do_it")`、`connect("sig", ...)` 的字符串拼写错到运行时才暴露，优先 Callable 引用与信号对象
- 脚本里定义与引擎原生方法同名的方法触发 `native_method_override`，默认即错误
- 局部变量与成员同名触发 `shadowed_variable`
- `static var` 所在脚本不会被卸载，持有大资源时手动清空

## 警告设置

警告在项目设置 `debug/gdscript/warnings/*`，值 0 忽略、1 警告、2 错误，高级设置里才可见。全表与默认值见 [references/warnings.md](references/warnings.md)。

全类型化项目建议改成错误：

```ini
[debug]

gdscript/warnings/untyped_declaration=2
gdscript/warnings/missing_await=2
gdscript/warnings/narrowing_conversion=2
gdscript/warnings/int_as_enum_without_cast=2
gdscript/warnings/unassigned_variable=2
```

- `untyped_declaration` 要求每个变量、参数、返回值、`for` 循环变量有类型，`:=` 算有类型
- `inferred_declaration` 反过来禁止 `:=`，用 `:=` 风格时保持 0
- `return_value_discarded` 对每个不接返回值的 `connect()` 报警，开启后要接 `var err := ...` 或加 `@warning_ignore`
- `unsafe_method_access`、`unsafe_property_access`、`unsafe_call_argument` 抓鸭子类型调用，默认关，想收紧时设 1
- 文件内忽略 `@warning_ignore("unused_signal")`，区域忽略 `@warning_ignore_start` 与 `@warning_ignore_restore`
- `directory_rules` 默认忽略 `res://addons`

## 参考

- [references/annotations.md](references/annotations.md) 导出与其他注解全表
- [references/syntax.md](references/syntax.md) match、静态成员、StringName、setter、super
- [references/warnings.md](references/warnings.md) 全部警告与默认值
- [GDScript 基础](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_basics.html)
- [静态类型](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/static_typing.html)
- [导出](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_exports.html)
- [警告系统](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/warning_system.html)
