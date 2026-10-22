# AnimationTree 细节

SKILL.md 给了节点选型与最短代码。本文补参数路径、状态机操作和常见搭建方式。

## 搭建顺序

1. 场景里有 AnimationPlayer，动画都在它的库里，已建好 `RESET`
2. 加 AnimationTree，`anim_player` 指向播放器，`tree_root` 新建 AnimationNodeStateMachine 或 AnimationNodeBlendTree
3. 勾选 `active`
4. 此后动画只经 AnimationTree 播放，脚本不再对播放器调 `play()`

`callback_mode_process` 在 AnimationTree 上单独设置，物理体角色设 `ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS`。

## 参数路径

| 节点 | 路径 | 说明 |
|---|---|---|
| StateMachine | `parameters/playback` | 取到 AnimationNodeStateMachinePlayback |
| BlendSpace1D | `parameters/<名>/blend_position` | float |
| BlendSpace2D | `parameters/<名>/blend_position` | Vector2 |
| Blend2 | `parameters/<名>/blend_amount` | 0 到 1 |
| OneShot | `parameters/<名>/request` | `AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE` `ONE_SHOT_REQUEST_ABORT` `ONE_SHOT_REQUEST_FADE_OUT` |
| OneShot | `parameters/<名>/active` | 只读，是否在播 |
| Transition | `parameters/<名>/transition_request` | 目标状态名 |
| Transition | `parameters/<名>/current_state` | 只读 |
| TimeSeek | `parameters/<名>/seek_request` | 秒 |
| TimeScale | `parameters/<名>/scale` | 0 暂停 负数倒放 |
| StateMachine 转场条件 | `parameters/conditions/<变量名>` | Advance Condition 对应的 bool |

嵌套状态机的路径带层级，如 `parameters/Ground/playback`。路径以 Inspector 悬停显示为准。

Advance Expression 不出现在参数里，它读 `advance_expression_base_node` 指向节点上的变量。

## 状态机操作

```gdscript
extends CharacterBody2D

@onready var _tree: AnimationTree = $AnimationTree
@onready var _state: AnimationNodeStateMachinePlayback = _tree["parameters/playback"]

func _physics_process(_delta: float) -> void:
	if not _state.is_playing():
		_state.start(&"Idle")
	var current := _state.get_current_node()
	if current == &"Idle" and absf(velocity.x) > 1.0:
		_state.travel(&"Run")
```

| 方法 | 用途 |
|---|---|
| `travel(to, reset_on_teleport)` | 沿转场图走到目标，无路径则直接跳 |
| `start(node, reset)` | 直接开始于某状态，与 `travel` 一样下次处理才生效 |
| `next()` | 有 travel 路径或 Auto 转场时立即进入下一状态 |
| `stop()` | 停止 |
| `get_current_node()` | 当前状态名 |
| `get_travel_path()` | 正在走的路径 |

- 转场的 Switch Mode：Immediate 立即切，Sync 立即切并把新状态定位到旧状态的位置（走路切跑步脚步不跳变），At End 等当前动画播完
- 转场 Advance Mode：Disabled 不用，Enabled 只在 `travel()` 时用，Auto 按条件自动走
- Xfade Time 与 Xfade Curve 做过渡混合
- Reset 控制进入新状态时是否从头播
- 状态机的 `allow_transition_to_self` 为 true 才允许 `travel()` 到当前状态，配合 `reset_on_teleport` 重头播放，连续攻击连击要开
- 状态机的 `state_machine_type`：Root 顶层，Nested 嵌套，Grouped 受父状态机控制，不独立工作，父级或祖先里必须有 Root 或 Nested 状态机

## 攻击叠加在移动上

1. BlendTree 里放一个 OneShot，`in` 接移动用的状态机，`shot` 接攻击动画
2. 给 OneShot 设 Filters，只勾上半身骨骼或相关轨道，下半身继续走路
3. `fadein_time` 与 `fadeout_time` 设几十毫秒
4. 脚本里发请求，用 `active` 判断是否正在攻击：

```gdscript
extends CharacterBody2D

@onready var _tree: AnimationTree = $AnimationTree

func attack() -> void:
	if _tree["parameters/AttackShot/active"]:
		return
	_tree["parameters/AttackShot/request"] = AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE
```

OneShot 的 `autorestart` 在播放结束后自动重新触发，先发一次 FIRE 才开始，ABORT 停止重触发，间隔由 `autorestart_delay` 控制，默认 1 秒。`break_loop_at_end` 让循环动画在末尾结束。

## BlendSpace

- 1D 用于速度：idle 放 0，walk 放 100，run 放 200，`blend_position` 直接填速度
- 2D 用于八方向：点按方向摆放，`blend_position` 填归一化方向。`auto_triangles` 默认 true 自动三角化
- 摆点的坐标单位自定，`min_space` 与 `max_space` 设范围，与脚本里传入的值同一量纲
- 不同长度的动画混合要同相位，否则脚步错位。4.7+ 用 `sync_mode`，走跑混合选 `AnimationNodeBlendSpace2D.SYNC_MODE_CYCLIC_MUTABLE`。更早版本用布尔 `sync`，它在 4.7 已弃用
- 方向切换不要用 8 个状态，用一个 BlendSpace2D 加 `blend_position`

## 根运动

AnimationTree 的 `root_motion_track` 指定位移轨道后，用 `get_root_motion_position()` 取一帧位移，除以 `delta` 驱动 CharacterBody3D 的 `velocity`。轨道必须是 3D 位置轨道，否则返回零向量。

## 事件与回调

- 状态变化事件连 AnimationNodeStateMachinePlayback 的 `state_started` 与 `state_finished` 信号 4.5+，更早版本比较 `get_current_node()`
- 在动画里做方法调用轨道和音频轨道，AnimationTree 混合时同样会触发，方法调用遵守 `callback_mode_method`
- AnimationTree 继承 `AnimationMixer`，有 `animation_started` 与 `animation_finished` 信号，循环动画不发 finished

## 确定性

AnimationTree 开 `deterministic`，缺轨道按 RESET 或 0 作初始值，默认 false 时缺轨道的动画不参与该属性的混合。回放用途再把 `callback_mode_process` 设成 `ANIMATION_CALLBACK_MODE_PROCESS_MANUAL`，每 tick `advance(delta)`。
