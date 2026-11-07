# AnimationTree

AnimationTree 的搭建顺序、参数路径、状态机操作、OneShot、BlendSpace、根运动与事件。

## 搭建顺序

1. 场景里有 AnimationPlayer，动画在它的库里，已建 `RESET`
2. 加 AnimationTree，`anim_player` 指向播放器
3. `tree_root` 新建 AnimationNodeStateMachine 或 AnimationNodeBlendTree
4. 勾选 `active`
5. 此后只经 AnimationTree 播放，不对播放器调 `play()`

- `callback_mode_process` 在 AnimationTree 上单独设置
- 物理体角色设 `ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS`

## 参数路径

| 节点 | 路径 | 值 |
|---|---|---|
| StateMachine | `parameters/playback` | AnimationNodeStateMachinePlayback |
| BlendSpace1D | `parameters/<名>/blend_position` | float |
| BlendSpace2D | `parameters/<名>/blend_position` | Vector2 |
| Blend2 | `parameters/<名>/blend_amount` | 0 到 1 |
| OneShot | `parameters/<名>/request` | `AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE` `ONE_SHOT_REQUEST_ABORT` `ONE_SHOT_REQUEST_FADE_OUT` |
| OneShot | `parameters/<名>/active` | 只读，是否在播 |
| Transition | `parameters/<名>/transition_request` | 目标状态名 |
| Transition | `parameters/<名>/current_state` | 只读 |
| TimeSeek | `parameters/<名>/seek_request` | 秒 |
| TimeScale | `parameters/<名>/scale` | 0 暂停，负数倒放 |
| StateMachine 转场条件 | `parameters/conditions/<变量名>` | Advance Condition 的 bool |

- 嵌套状态机路径带层级，如 `parameters/Ground/playback`
- 路径以 Inspector 悬停显示为准
- Advance Expression 不在参数里，读 `advance_expression_base_node` 节点的变量

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

```csharp
public partial class StatePlayer : CharacterBody2D
{
    private AnimationTree _tree;
    private AnimationNodeStateMachinePlayback _state;

    public override void _Ready()
    {
        _tree = GetNode<AnimationTree>("AnimationTree");
        _state = _tree.Get("parameters/playback").As<AnimationNodeStateMachinePlayback>();
    }

    public override void _PhysicsProcess(double delta)
    {
        if (!_state.IsPlaying())
        {
            _state.Start("Idle");
        }
        StringName current = _state.GetCurrentNode();
        if (current == "Idle" && Mathf.Abs(Velocity.X) > 1.0f)
        {
            _state.Travel("Run");
        }
    }
}
```

| 方法 | 用途 |
|---|---|
| `travel(to, reset_on_teleport)` | 沿转场图走到目标，无路径直接跳 |
| `start(node, reset)` | 直接开始于某状态，下次处理才生效 |
| `next()` | 有 travel 路径或 Auto 转场时立即进入下一状态 |
| `stop()` | 停止 |
| `get_current_node()` | 当前状态名 |
| `get_travel_path()` | 正在走的路径 |

| 转场设置 | 取值 |
|---|---|
| Switch Mode | Immediate 立即切；Sync 立即切并对齐播放位置；At End 等当前动画播完 |
| Advance Mode | Disabled 不用；Enabled 只在 `travel()` 时用；Auto 按条件自动走 |
| Xfade Time、Xfade Curve | 过渡混合时长与曲线 |
| Reset | 进入新状态时是否从头播 |

| `state_machine_type` | 含义 |
|---|---|
| Root | 顶层 |
| Nested | 嵌套 |
| Grouped | 受父状态机控制，祖先里须有 Root 或 Nested |

- Sync 用于走路切跑步，脚步不跳变
- `allow_transition_to_self` 为 true 才能 `travel()` 到当前状态
- 连击重头播：开 `allow_transition_to_self`，配 `reset_on_teleport`

## 攻击叠加在移动上

1. BlendTree 里放 OneShot，`in` 接移动状态机，`shot` 接攻击动画
2. OneShot 设 Filters，只勾上半身骨骼或相关轨道
3. `fadein_time` 与 `fadeout_time` 设几十毫秒
4. 脚本发请求，用 `active` 判断是否在攻击

```gdscript
extends CharacterBody2D

@onready var _tree: AnimationTree = $AnimationTree

func attack() -> void:
	if _tree["parameters/AttackShot/active"]:
		return
	_tree["parameters/AttackShot/request"] = AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE
```

```csharp
public partial class Attacker : CharacterBody2D
{
    private AnimationTree _tree;

    public override void _Ready()
    {
        _tree = GetNode<AnimationTree>("AnimationTree");
    }

    public void Attack()
    {
        if (_tree.Get("parameters/AttackShot/active").AsBool())
        {
            return;
        }
        _tree.Set("parameters/AttackShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
    }
}
```

| OneShot 属性 | 作用 |
|---|---|
| `autorestart` | 播完自动重新触发，先发一次 FIRE 才开始，ABORT 停止 |
| `autorestart_delay` | 重触发间隔，默认 1 秒 |
| `break_loop_at_end` | 循环动画在末尾结束 |

## BlendSpace

| 类型 | 用途 | `blend_position` |
|---|---|---|
| 1D | 速度：idle 0，walk 100，run 200 | 直接填速度 |
| 2D | 八方向，点按方向摆放 | 归一化方向 |

- `auto_triangles` 默认 true，自动三角化
- `min_space` `max_space` 设范围，与脚本传入值同一量纲
- 方向切换用一个 BlendSpace2D，不用 8 个状态
- 不同长度的动画混合要同相位，否则脚步错位
- 4.7+ 用 `sync_mode`，走跑选 `AnimationNodeBlendSpace2D.SYNC_MODE_CYCLIC_MUTABLE`
- 更早版本用布尔 `sync`，4.7 已弃用

## 根运动

- `root_motion_track` 指定位移轨道
- `get_root_motion_position()` 取一帧位移，除以 `delta` 作 `velocity`
- 轨道须是 3D 位置轨道，否则返回零向量

## 事件与回调

- 状态变化连 `state_started` `state_finished` 信号 4.5+
- 4.5 以前比较 `get_current_node()`
- 方法调用轨道和音频轨道在混合时同样触发
- 方法调用遵守 `callback_mode_method`
- AnimationTree 继承 `AnimationMixer`，有 `animation_started` `animation_finished`
- 循环动画不发 `animation_finished`

## 确定性

- `deterministic` 为 true：缺轨道按 RESET 或 0 作初始值
- 默认 false：缺轨道的动画不参与该属性混合
- 回放再设 `ANIMATION_CALLBACK_MODE_PROCESS_MANUAL`，每 tick `advance(delta)`
