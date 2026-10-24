# enum 状态机

状态少且转移简单时，一个枚举加一个 `match`，转移都走 `_set_state`，进入和退出的一次性逻辑放在里面。

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
