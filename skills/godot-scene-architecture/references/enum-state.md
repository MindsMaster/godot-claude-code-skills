# enum 状态机

状态少、转移简单时的完整写法：一个枚举加一个 `match`。

## 写法

转移只走 `_set_state`，进入时的一次性逻辑放在里面。

```gdscript
extends CharacterBody2D

enum State { IDLE, RUN, JUMP }

const SPEED := 200.0
const JUMP_VELOCITY := -400.0

var state: State = State.IDLE

func _physics_process(delta: float) -> void:
	var axis := Input.get_axis("move_left", "move_right")
	match state:
		State.IDLE, State.RUN:
			if Input.is_action_just_pressed("jump") and is_on_floor():
				_set_state(State.JUMP)
			elif axis != 0.0:
				_set_state(State.RUN)
			else:
				_set_state(State.IDLE)
		State.JUMP:
			if is_on_floor():
				_set_state(State.IDLE)
	if not is_on_floor():
		velocity += get_gravity() * delta
	velocity.x = axis * SPEED
	move_and_slide()

func _set_state(next: State) -> void:
	if next == state:
		return
	state = next
	if next == State.JUMP:
		velocity.y = JUMP_VELOCITY
```

```csharp
public partial class Player : CharacterBody2D
{
    public enum State { Idle, Run, Jump }

    private const float Speed = 200.0f;
    private const float JumpVelocity = -400.0f;

    public State Current { get; private set; } = State.Idle;

    public override void _PhysicsProcess(double delta)
    {
        float axis = Input.GetAxis("move_left", "move_right");
        switch (Current)
        {
            case State.Idle:
            case State.Run:
                if (Input.IsActionJustPressed("jump") && IsOnFloor())
                {
                    SetState(State.Jump);
                }
                else if (axis != 0.0f)
                {
                    SetState(State.Run);
                }
                else
                {
                    SetState(State.Idle);
                }
                break;
            case State.Jump:
                if (IsOnFloor())
                {
                    SetState(State.Idle);
                }
                break;
        }
        Vector2 velocity = Velocity;
        if (!IsOnFloor())
        {
            velocity += GetGravity() * (float)delta;
        }
        velocity.X = axis * Speed;
        Velocity = velocity;
        MoveAndSlide();
    }

    private void SetState(State next)
    {
        if (next == Current)
        {
            return;
        }
        Current = next;
        if (next == State.Jump)
        {
            Velocity = new Vector2(Velocity.X, JumpVelocity);
        }
    }
}
```

- C# 的 `CharacterBody2D.Velocity` 是结构体属性，不能只改 X，取到局部变量改完再赋回
