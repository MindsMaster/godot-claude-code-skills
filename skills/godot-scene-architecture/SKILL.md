---
name: godot-scene-architecture
description: 拆分 Godot 4 场景与组织节点时用。PackedScene 组件复用、节点引用 @onready @export %UniqueName、信号与直接调用的选择、分组 call_group、Autoload 与普通节点、组合与继承、状态机、暂停 process_mode、queue_free 与 is_instance_valid、_ready 顺序、场景切换。scene tree architecture, signals, autoload.
---

# Godot 场景架构

解决怎么把游戏拆成场景和节点：谁实例化谁，节点怎么互相找到，怎么通信，状态怎么管，场景怎么切。不管具体节点的用法，见 godot-2d godot-ui godot-animation。资源当数据用见 godot-resources-data，C# 通用规则见 godot-csharp。

默认做法：一个概念一个 `.tscn`，脚本挂在场景根上，场景自带它需要的子节点，对外只露 `@export` 属性、信号和少量方法。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 可复用对象 敌人 子弹 面板 | 独立 `.tscn` + `PackedScene.instantiate()` | 代码里 `new` 一整棵节点树，`.tscn` 只剩空壳 |
| 同场景内的节点引用 | `%UniqueName` 或 `@onready` 缓存 | 长路径 `get_node("A/B/C")`，每帧 `get_node` |
| 场景外的目标引用 | `@export var target: Node2D` 在 Inspector 连 | 写死 `/root/Main/Level/Player` |
| 一类对象批量通知 | `add_to_group` + `get_tree().call_group` | 手写注册表数组，全局事件总线 |
| 子对象通知父对象 | 信号 | 子节点 `get_parent().foo()` |
| 全局共享的数据 | 自定义 `Resource`，或 autoload 里只放真全局状态 | Manager 套 Manager |
| 状态切换 | `enum` + `match`，复杂时状态子节点或 `AnimationTree` 状态机 | 一串 `is_jumping` `is_attacking` bool 加计时器 |
| 暂停菜单 | `SceneTree.paused` + `Node.process_mode` | 每个脚本里判断 `is_paused` 的 bool |
| 同一逻辑给多个场景用 | 组件节点 `class_name` 脚本，做成子节点 | 复制粘贴到两个脚本，深继承链 |
| 场景切换 | `change_scene_to_file` / `change_scene_to_packed` | 手动 `free` 旧场景再 `add_child` 新场景 |
| 非节点的纯逻辑对象 | `RefCounted` 或 `Resource` | 为了存数据继承 `Node` 再挂树上 |

## 场景即组件

场景自包含：只依赖自己的子节点。需要外部信息时由父级注入，三种方式按用途选：

| 方式 | 用于 | 写法 |
|---|---|---|
| 信号 | 子对象报告发生了什么 | 子 `emit`，父 `connect` |
| `@export` 属性 | 配置和目标引用 | Inspector 里设，或父脚本在 `add_child` 前设 |
| `Callable` 属性 | 子对象需要回调父级提供的行为 | 父把方法赋给子的属性 |

实例化的最短写法：

```gdscript
class_name Bullet
extends Area2D

var direction: Vector2 = Vector2.RIGHT
var speed: float = 400.0

func _physics_process(delta: float) -> void:
	position += direction * speed * delta
```

```gdscript
class_name Spawner
extends Node2D

@export var bullet_scene: PackedScene

func fire(dir: Vector2) -> void:
	var bullet := bullet_scene.instantiate() as Bullet
	bullet.direction = dir
	get_parent().add_child(bullet)
	bullet.global_position = global_position
```

初始参数在 `add_child` 之前设，`_ready` 里就能读到。`global_position` 在 `add_child` 之后设，之前设 2D 会当成本地坐标，3D 直接报错。

`@export var scene: PackedScene` 比 `preload("res://...")` 写死路径好：Inspector 可换，路径移动时引用跟着走。同脚本内固定不变的小场景用 `preload` 也行。

### 何时在代码里造节点

合理：数量由数据决定的重复结构，如背包格子、按地图数据生成的墙；纯运行时的辅助节点，如一次性 `Timer`；编辑器工具里生成预览。

不合理：每个子节点都是固定的、有布局的、美术要调的。这类写进 `.tscn`，代码只 `instantiate()` 一次。代码造出来的 UI 和关卡，美术无法在编辑器里看到和调整，也没法用场景继承。

代码造节点并且要存进 `PackedScene` 或在编辑器场景里显示时，每个节点都要设 `owner`，见 [references/lifecycle.md](references/lifecycle.md)。

## 节点引用

```gdscript
extends Node2D

@export var target: Node2D
@export_node_path("Marker2D") var spawn_path: NodePath

@onready var score: Label = %ScoreLabel
@onready var sprite: Sprite2D = $Sprite2D
@onready var spawn: Marker2D = get_node(spawn_path)

func _process(_delta: float) -> void:
	if target != null:
		look_at(target.global_position)
```

- 直接子节点用 `$Name`，更深的节点在场景面板右键 `Access as Unique Name` 后用 `%Name`
- 一律 `@onready` 缓存成带类型的成员变量，不在 `_process` 里取
- `@export var x: Node2D` 在 `instantiate()` 返回时已解析为节点，`_enter_tree` 和 `_ready` 里可用，`_init` 里是 `null`。代码里 `instantiate()` 出来的场景要自己赋值
- 找不到可能是正常情况时用 `get_node_or_null`

C# 在 `_Ready` 里把 `GetNode<Label>("%ScoreLabel")` 存进私有字段，节点引用属性写 `[Export] public Node2D Target { get; set; }`。

## 通信 call down signal up

向下（父到子）直接调方法或设属性。向上（子到父）发信号，父连接。兄弟之间通过共同的父节点转发，或者各自 `@export` 对方。

```gdscript
class_name Health
extends Node

signal changed(current: int, maximum: int)
signal died

@export var maximum: int = 100

@onready var current: int = maximum

func damage(amount: int) -> void:
	current = maxi(current - amount, 0)
	changed.emit(current, maximum)
	if current == 0:
		died.emit()
```

```gdscript
extends CharacterBody2D

@onready var health: Health = $Health

func _ready() -> void:
	health.died.connect(queue_free)
```

- 信号名用过去式：`died` `item_collected`
- 成员初始化器里读 `@export` 拿到的是脚本默认值，Inspector 里改的值在 `_ready` 之前才到，依赖它的初值用 `@onready`
- 信号只用来响应，不用来发起指令。要对方做事就调方法
- 编辑器 Node 面板里连的信号写在 `.tscn` 里，父场景重命名方法时不会提示，脚本里 `connect` 更好追踪

C# 信号：

```csharp
public partial class Health : Node
{
    [Signal] public delegate void ChangedEventHandler(int current, int maximum);
    [Signal] public delegate void DiedEventHandler();

    [Export] public int Maximum { get; set; } = 100;

    public int Current { get; private set; }

    public override void _Ready() => Current = Maximum;

    public void Damage(int amount)
    {
        Current = Math.Max(Current - amount, 0);
        EmitSignal(SignalName.Changed, Current, Maximum);
        if (Current == 0)
        {
            EmitSignal(SignalName.Died);
        }
    }
}
```

## 分组

分组是一类对象的广播通道，不是全局注册表。

```gdscript
extends Node2D

func raise_alarm() -> void:
	get_tree().call_group("guards", "alert", global_position)
```

- 加入分组在节点面板 Groups 页签里勾，或 `add_to_group("guards")`
- `get_tree().call_group_flags(SceneTree.GROUP_CALL_DEFERRED, ...)` 延后到帧末，遍历中会增删节点时用
- 场景里唯一的对象（玩家）用 `get_tree().get_first_node_in_group("player")` 在 `_ready` 里取一次，缓存

## Autoload

只放全局、生命周期跨场景的状态：存档槽、设置、场景切换器、跨关卡的任务进度。Autoload 不会随 `change_scene_to_*` 释放。

```ini
[autoload]

Settings="*res://src/autoload/settings.gd"
```

- 开头的 `*` 对应面板的 Enable 列，GDScript 里才有全局名。C# 不受影响，自己写静态 Instance 属性
- 从 autoload 的 `_ready` 里取当前场景节点会失败，主场景还没加载
- 能放进场景的就放进场景。每个场景自己持有自己的 `AudioStreamPlayer`，不要做全局音效池。会 `queue_free` 的对象不播自己的收尾音效，它出树时声音被停，交给关卡里常驻的播放器
- 共享函数用 `class_name` + `static func`，共享数据用自定义 `Resource`，都不需要 autoload
- 不建 GameManager EventBus UIManager 这类总管。信号总线让谁发谁收无法追踪，改成直接引用或沿树传递

## 组合优先于继承

重复出现的行为做成子节点组件，宿主用 `@export` 传进来，不靠 `get_parent()`：

```gdscript
class_name HurtBox
extends Area2D

@export var health: Health

func _ready() -> void:
	area_entered.connect(_on_area_entered)

func _on_area_entered(area: Area2D) -> void:
	if area is HitBox:
		health.damage(area.damage)
```

```gdscript
class_name HitBox
extends Area2D

@export var damage: int = 1
```

- 敌人、玩家、可破坏物都挂同一个 Health 加 HurtBox，不做 Damageable 基类
- 继承留给同类事物的细分，一层够用。需要第三层时先想能否拆成组件
- 场景继承（New Inherited Scene）用于同一模板的变体，比如换了贴图和数值的敌人。继承场景里改父场景的结构会影响所有变体
- 嵌入的子场景默认只能改根节点属性，右键 `Editable Children` 才能改内部节点，改动写在宿主场景里，父场景改结构时容易失效

## 状态机

按复杂度选，一个概念只用一种：

| 状态数与转移 | 用法 |
|---|---|
| 2 到 5 个，转移简单 | `enum State` + `match`，见 [references/enum-state.md](references/enum-state.md) |
| 每个状态有自己的进出逻辑和数据 | 每个状态一个子节点，见 [references/state-machine.md](references/state-machine.md) |
| 状态对应动画，转移由动画条件驱动 | `AnimationTree` 的 `AnimationNodeStateMachine` |

- 所有转移走一个入口函数，进入和退出的一次性逻辑放在里面

## 暂停与 process_mode

```gdscript
extends Control

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	hide()

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		get_tree().paused = not get_tree().paused
		visible = get_tree().paused
		get_viewport().set_input_as_handled()
```

- `PROCESS_MODE_INHERIT` 是默认值，沿父级走，根节点默认当 `PROCESS_MODE_PAUSABLE`
- 负责切换暂停的节点设 `ALWAYS`，`WHEN_PAUSED` 的节点未暂停时收不到输入。暂停菜单内容设 `WHEN_PAUSED`，背景音乐和转场设 `ALWAYS`
- `PROCESS_MODE_DISABLED` 关掉整棵子树的处理，比逐个 `set_process(false)` 干净。屏幕外的对象用 `VisibleOnScreenEnabler2D` 或 `VisibleOnScreenEnabler3D`，它按可见性切 `PROCESS_MODE_DISABLED`
- `Node.set_process(false)` 只关 `_process`，不影响 `_physics_process` 和输入
- `SceneTree.paused` 同时停物理。`create_timer` 的 `process_always` 默认 `true`，暂停时也走

## 陷阱

- 子节点的 `_ready` 先于父节点。父的 `_ready` 里可以放心用子，子的 `_ready` 里不要假设父已就绪
- `queue_free()` 后对象到帧末才释放，`is_instance_valid` 在这之前仍返回 `true`。判断是否已在销毁用 `is_queued_for_deletion()`
- 物理回调（`body_entered` `area_entered`）里增删碰撞体、改 `CollisionShape2D.disabled` 会报 `Can't change this state while flushing queries`，改 `monitoring` `monitorable` 报 `Function blocked during in/out signal`。用 `set_deferred("disabled", true)` 或 `call_deferred`
- 手写 `.tscn` 给 `@export` 的 Node 类型属性赋值，节点头漏写 `node_paths=PackedStringArray(...)` 则运行期为 `null`，见 [references/lifecycle.md](references/lifecycle.md)
- `%Name` 只在同一个场景的 owner 内有效，跨实例化子场景取不到；代码里 `add_child` 的节点 `owner` 为 `null` 时 `%Name` 查不到，设了 `owner` 才生效
- 节点在树外时 `get_tree()` 返回 `null`，`await get_tree().process_frame` 报错。先 `add_child`
- `change_scene_to_*` 调用后到帧末，`get_tree().current_scene` 是 `null`。切换 API 的细节见 [references/scene-switching.md](references/scene-switching.md)
- lambda 里捕获了会被释放的节点，释放后触发会报错。用方法引用连接，Godot 会在对象释放时自动断开
- `_process` 里每帧 `get_node` `find_child` `get_nodes_in_group`，或 `get_node("../Sibling")` 这类向上路径。缓存，或改成 `@export` 和信号
- 上帝节点：一个 `Level.gd` 管相机、HUD、生成、计时、状态。按职责拆成子场景，各自有脚本，Level 只负责组装

## 参考

- [references/lifecycle.md](references/lifecycle.md)：`_enter_tree` `_ready` `_exit_tree` 的选择，`owner` 规则，手写 `.tscn` 的 `node_paths`，`call_deferred` 必须用的场合，释放与失效引用
- [references/scene-switching.md](references/scene-switching.md)：`change_scene_to_*` 的行为，自己做切换的场合，带加载界面的切换
- [references/enum-state.md](references/enum-state.md)：`enum` 加 `match` 的完整示例
- [references/state-machine.md](references/state-machine.md)：状态子节点模板，`AnimationTree` 状态机用法
- 官方文档：https://docs.godotengine.org/en/stable/tutorials/best_practices/index.html
