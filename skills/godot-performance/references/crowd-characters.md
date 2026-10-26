# 大量 CharacterBody 拥挤

几十到几百个 `CharacterBody3D` 互相碰撞时 `move_and_slide()` 成为瓶颈的排查和省法。先列不改行为的做法，改玩法的避让路线放最后，要策划确认。数字取自 4.7.2 源码，Jolt 是 4.6 起新项目的默认 3D 物理。2D 的 `CharacterBody2D` 结构相同，只是没有 Jolt 那一层。

## 一次 move_and_slide 做了什么

| 步骤 | 次数 | 条件 |
|---|---|---|
| 平台位移查询 | 0 或 1 | 站在有速度的平台上 |
| 滑动循环 `body_test_motion` | 1 到 `max_slides` 次，默认 6 | 速度为 0 也至少 1 次；没撞到或剩余位移为 0 就提前结束 |
| 吸地 | 0 到 2 | 上一帧在地面、这一帧离地时 |
| `floor_constant_speed` 补偿 | 0 或 1 | 默认关 |

Jolt 里每次 `body_test_motion` 又分三步：

1. 解穿插：最多 `physics/jolt_physics_3d/motion_queries/recovery_iterations` 轮，默认 4，每轮对 `safe_margin` 内的所有物体做一次窄相，每轮只推出穿插深度的 `recovery_amount`，默认 0.4
2. 扫掠：不是解析扫掠，是对每个候选物体二分查找，步数 4 到 16，按位移长度定
3. 收集碰撞：撞到或发生过解穿插就再做一次窄相，给每个接触生成流形

拥挤时变贵的原因：运动学体的新位置要到下一个物理步才进 Jolt，同一帧里每个角色查到的邻居都是上一步的位置。相向移动的角色每帧重新穿插，下一帧就跑满解穿插，每个邻居再二分一轮，乘以两三次滑动。

每次滑动迭代都会 `set_global_transform()`，Node3D 设变换时无条件递归整棵 Node3D 子树，不判断值是否相同。角色下挂的节点越多，每次迭代越贵。

## 不改行为能省的

- 收紧碰撞掩码：运动查询的过滤是单向的，自己的 `collision_mask` 与对方的 `collision_layer` 相与，宽相阶段就剔除。只去掉本来就不该挡角色的层，如掉落物、作为物理体的子弹、装饰物
- 只挂一个形状。多个形状在 Jolt 里组成复合形状，查询要多一层遍历和多次窄相
- 每帧只调一次 `move_and_slide()`，地面、墙、天花板状态读它的结果，不另做射线或 `test_move()`
- 视觉节点放浅：模型、血条、特效挂在角色下时层级越少越好。纯视觉且不需要跟随旋转的可以 `top_level`，自己同步位置
- 静止跳过，见后面的静止时跳过一节

## 碰撞形状：圆柱最贵

一个 C# 项目 164 个拥挤怪物，每个物理步全部 `_physics_process` 耗时，只换怪物形状，Jolt：

| 形状 | 毫秒 | 对比圆柱 |
|---|---|---|
| `CylinderShape3D` | 17.9 | |
| `CapsuleShape3D`、`SphereShape3D` | 12.6 | -30% |
| `BoxShape3D` | 11.4 | -37% |
| 圆柱，怪物之间不碰撞 | 11.4 | -37% |

- 贵在圆柱之间互相穿插，换掉形状和去掉怪物间碰撞省得一样多
- 加大圆柱的 `margin` 和 `physics/jolt_physics_3d/collisions/collision_margin_fraction` 没有效果
- 换形状会改变脚底和外轮廓：盒子对角线方向宽出 41%，胶囊高度不能小于两倍半径，扁平的大怪会变高。属于改手感，要策划确认
- 新角色一开始就用胶囊，不用圆柱

## 静止时跳过

<!-- check: extends CharacterBody3D -->
```gdscript
@export var speed: float = 4.0
var desired_direction := Vector3.ZERO

func _physics_process(delta: float) -> void:
	velocity.x = desired_direction.x * speed
	velocity.z = desired_direction.z * speed
	if not is_on_floor():
		velocity += get_gravity() * delta
	if velocity.is_zero_approx() and is_on_floor() and get_platform_velocity().is_zero_approx():
		return
	move_and_slide()
```

- UE 的 CharacterMovementComponent 在 bAlwaysCheckFloor 为 false 且零位移时复用上次地面结果，这里是同一个思路
- 前提一：重力只在离地时累加，否则速度永远不为 0
- 前提二：脚下是不动的地面。站在会动的平台上不能跳过，平台开始移动时 `get_platform_velocity()` 还是上次的值
- 跳过期间 `is_on_floor()`、`get_real_velocity()`、滑动碰撞列表保持上一次的结果
- 跳过的角色不再自己解穿插，别人走进来时由移动的一方推开自己。挤成一团时手感可能有细微差别，改完对比录像

## 不能把 move_and_slide 分到线程

- `PhysicsServer3D` 外面套着一层多线程包装，Jolt 和 Godot Physics 都有。这层的 `body_test_motion()` 与 `space_get_direct_state()` 一开头检查是否主线程，不是就报错返回
- 把角色根节点的 `process_thread_group` 设成 `PROCESS_THREAD_GROUP_SUB_THREAD` 后在里面调 `move_and_slide()`，结果是报错且角色原地不动
- `physics/3d/run_on_separate_thread` 只把物理步挪到另一个线程，与 `_process` 和渲染重叠。`move_and_slide()` 仍在主线程逐个执行，对这个瓶颈帮助很小。上面同一个项目实测开启后每步从 17.2 毫秒变成 20.1 毫秒。开启后在 `_process` 里调物理查询会报物理空间正在步进
- 可行的拆法：AI、寻路结果处理、期望速度这些纯计算放子线程组或 `WorkerThreadPool`，主线程一个管理器循环里依次 `move_and_slide()`，见 [many-entities.md](many-entities.md) 的统一驱动

## 不建议的调参

下面这些能直接省时间，但会改变碰撞结果，属于降质：

- 调小 `max_slides`：撞墙两次就停
- 调小 `recovery_iterations`：残留更多穿插，容易抖
- 关 `physics/jolt_physics_3d/motion_queries/use_enhanced_internal_edge_removal`：地形网格上可能出现幽灵碰撞
- 降 `physics/common/physics_ticks_per_second`
- 屏幕外角色停止移动

`physics/jolt_physics_3d/limits/max_bodies` 一类只是容量上限，不影响查询开销。

## 改为避让：要策划确认

去掉角色之间的物理碰撞，改用导航避让让它们互相让开，是 UE Mass 与 DetourCrowd 处理人群的方式。它会改变手感：

- 角色之间不再顶住、推挤，隘口不会自然排队堵住
- 提前绕开，围攻阵型更散
- RVO 在密集时不保证完全不重叠，Godot 没有 DetourCrowd 那样积分后的位置修正

UE 的 CrowdManager 默认 bResolveCollisions 为 false，即角色仍保留胶囊碰撞，避让只用来减少接触。这是改动更小的折中：保留碰撞，加避让，接触少了解穿插就少。

<!-- check: extends CharacterBody3D -->
```gdscript
@onready var _agent: NavigationAgent3D = $NavigationAgent3D
var desired_velocity := Vector3.ZERO

func _ready() -> void:
	_agent.avoidance_enabled = true
	_agent.radius = 0.5
	_agent.neighbor_distance = 4.0
	_agent.velocity_computed.connect(_on_velocity_computed)
	_agent.target_position = global_position

func _physics_process(_delta: float) -> void:
	_agent.velocity = desired_velocity

func _on_velocity_computed(safe_velocity: Vector3) -> void:
	velocity = safe_velocity
	move_and_slide()
```

| 属性 | 默认 | 建议 |
|---|---|---|
| `radius` | 0.5 | 等于碰撞胶囊半径 |
| `neighbor_distance` | 50 米 | 3 到 5 米，UE Mass 约 4 米 |
| `max_neighbors` | 10 | 保持，RVO 只取最近的这几个 |
| `time_horizon_agents` | 1.0 | 0.5 到 1 |
| `use_3d_avoidance` | false | 地面角色保持 false |
| `avoidance_layers` `avoidance_mask` `avoidance_priority` | | 区分怪物与玩家，玩家优先级高 |

- 从没设过 `target_position` 的代理不会把 `velocity` 提交给服务器，回调照常触发但安全速度一直是 0。只用避让不寻路时也先设一次
- 避让在 `NavigationServer3D` 里算，`navigation/avoidance/thread_model/avoidance_use_multiple_threads` 默认开，各代理分到 `WorkerThreadPool` 并行。时机在节点 `_physics_process` 之后、物理步之前，`velocity_computed` 回调里 `move_and_slide()` 当帧生效
- `neighbor_distance` 默认 50 米对地面怪物太大，缩小主要省邻居搜索，结果近似等价，改完要看效果
- 去掉怪物之间碰撞时：怪物的 `collision_mask` 去掉怪物层，玩家的 `collision_mask` 保留怪物层，玩家仍会被挡住
- 想在去碰撞后仍不重叠：照 DetourCrowd 在空间哈希上加 4 轮位置推开，每轮推开穿插深度的一部分，系数 0.7。这是纯计算，可以并行，之后再交给 `move_and_slide()` 处理环境阻挡
