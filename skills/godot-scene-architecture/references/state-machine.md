# 状态机模板

状态子节点模板和 `AnimationTree` 状态机的用法。

## 状态子节点

状态各有进出逻辑和独占数据时用：一个状态一个节点，状态机节点只负责转移。

场景树：`Player > StateMachine > Idle / Run / Jump`。

```gdscript
class_name State
extends Node

@warning_ignore("unused_signal")
signal transition_requested(state_name: StringName)

func enter() -> void:
	pass

func exit() -> void:
	pass

func physics_update(_delta: float) -> void:
	pass
```

```csharp
public partial class State : Node
{
    [Signal] public delegate void TransitionRequestedEventHandler(StringName stateName);

    public virtual void Enter()
    {
    }

    public virtual void Exit()
    {
    }

    public virtual void PhysicsUpdate(double delta)
    {
    }
}
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

```csharp
public partial class StateMachine : Node
{
    [Export] public State Initial { get; set; }

    public State Current { get; private set; }

    public override void _Ready()
    {
        foreach (Node child in GetChildren())
        {
            if (child is State state)
            {
                state.TransitionRequested += OnTransitionRequested;
            }
        }
        Current = Initial;
        Current.Enter();
    }

    public override void _PhysicsProcess(double delta)
    {
        Current.PhysicsUpdate(delta);
    }

    private void OnTransitionRequested(StringName stateName)
    {
        var next = GetNodeOrNull<State>(stateName.ToString());
        if (next == null || next == Current)
        {
            return;
        }
        Current.Exit();
        Current = next;
        Current.Enter();
    }
}
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

```csharp
public partial class RunState : State
{
    private static readonly StringName Idle = "Idle";

    [Export] public CharacterBody2D Body { get; set; }
    [Export] public float Speed { get; set; } = 200.0f;

    public override void PhysicsUpdate(double delta)
    {
        float dir = Input.GetAxis("move_left", "move_right");
        if (dir == 0.0f)
        {
            EmitSignal(SignalName.TransitionRequested, Idle);
            return;
        }
        Body.Velocity = new Vector2(dir * Speed, Body.Velocity.Y);
        Body.MoveAndSlide();
    }
}
```

- 状态节点用 `@export` 拿宿主，不用 `get_parent().get_parent()`
- 状态切换只走 `transition_requested`，状态之间不互相引用
- 状态机节点用默认的 `PROCESS_MODE_INHERIT`，暂停时随父级停
- C# 子类发基类信号用 `EmitSignal(SignalName.X)`

## AnimationTree 状态机

状态对应动画、转移由条件触发时用。转移在编辑器里画，脚本只发指令。树的其他用法见 godot-animation。

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

```csharp
public partial class AnimatedPlayer : CharacterBody2D
{
    private AnimationNodeStateMachinePlayback _playback;

    public override void _Ready()
    {
        var tree = GetNode<AnimationTree>("AnimationTree");
        _playback = tree.Get("parameters/playback").As<AnimationNodeStateMachinePlayback>();
    }

    public override void _PhysicsProcess(double delta)
    {
        if (IsOnFloor() && Velocity.X != 0.0f)
        {
            _playback.Travel("run");
        }
        else if (IsOnFloor())
        {
            _playback.Travel("idle");
        }
        else
        {
            _playback.Travel("jump");
        }
    }
}
```

| 调用 | 行为 |
|---|---|
| `travel("x")` | 按转移图走最短路径，无路径时直接跳到 x |
| `start("x")` | 不走转移图，直接切到 x |
| `tree.set("parameters/conditions/on_floor", true)` | 设转移条件，转移的 `advance_mode` 须为 `ADVANCE_MODE_AUTO` |

- `travel` 和 `start` 在 AnimationTree 下次处理时生效
- 调用后立刻读 `get_current_node()` 仍是旧状态
- `AnimationTree.active` 默认 `true`
- `parameters/playback` 由根状态机节点生成
- 逻辑状态用 `enum`，动画状态机只跟随表现
