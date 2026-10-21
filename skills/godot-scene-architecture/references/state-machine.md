# 状态机模板

## 状态子节点

状态各有进出逻辑和独占数据时，一个状态一个节点，状态机节点只负责转移。

```gdscript
class_name State
extends Node

signal transition_requested(state_name: StringName)

func enter() -> void:
	pass

func exit() -> void:
	pass

func physics_update(_delta: float) -> void:
	pass
```

```gdscript
class_name StateMachine
extends Node

@export var initial: State

var current: State

func _ready() -> void:
	for child in get_children():
		if child is State:
			child.transition_requested.connect(_on_transition_requested)
	current = initial
	current.enter()

func _physics_process(delta: float) -> void:
	current.physics_update(delta)

func _on_transition_requested(state_name: StringName) -> void:
	var next := get_node_or_null(NodePath(state_name)) as State
	if next == null or next == current:
		return
	current.exit()
	current = next
	current.enter()
```

```gdscript
extends State

@export var body: CharacterBody2D
@export var speed: float = 200.0

func physics_update(_delta: float) -> void:
	var dir := Input.get_axis("move_left", "move_right")
	if dir == 0.0:
		transition_requested.emit(&"Idle")
		return
	body.velocity.x = dir * speed
	body.move_and_slide()
```

- 场景树：`Player > StateMachine > Idle / Run / Jump`，状态节点用 `@export` 拿宿主，不 `get_parent().get_parent()`
- 状态切换只走 `transition_requested` 信号，状态之间不互相引用
- 状态要在暂停时停，状态机节点继承默认的 `PROCESS_MODE_INHERIT` 即可

## AnimationTree 状态机

状态对应动画，转移由条件触发时，用 `AnimationTree` 的 `AnimationNodeStateMachine`，在编辑器里画转移，脚本只发指令。

```gdscript
extends CharacterBody2D

@onready var tree: AnimationTree = $AnimationTree
@onready var playback: AnimationNodeStateMachinePlayback = tree["parameters/playback"]

func _physics_process(_delta: float) -> void:
	if is_on_floor() and velocity.x != 0.0:
		playback.travel("run")
	elif is_on_floor():
		playback.travel("idle")
	else:
		playback.travel("jump")
```

- `tree.active = true` 才会运行，参数路径 `parameters/playback` 由根状态机节点生成
- `travel` 按转移图寻路，目标不可达时不动。要立即跳转用 `playback.start("name")`
- 转移条件可以在转移上设 `advance_condition`，脚本里 `tree.set("parameters/conditions/on_floor", true)`，适合布尔条件多的情况
- 逻辑状态（能不能攻击）和动画状态分开：逻辑用 `enum`，动画状态机只跟随表现
