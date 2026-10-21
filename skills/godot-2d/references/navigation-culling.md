# 寻路与离屏处理

## VisibleOnScreen

<!-- check: extends Node2D -->
```gdscript
@onready var _notifier: VisibleOnScreenNotifier2D = $VisibleOnScreenNotifier2D

func _ready() -> void:
	_notifier.screen_exited.connect(queue_free)
```

- `rect` 手动框住精灵，不会自动跟随贴图大小。
- 离屏停止处理：给敌人加子节点 `VisibleOnScreenEnabler2D`，`enable_node_path` 默认指向父节点，离屏时目标被设为 `PROCESS_MODE_DISABLED`。`enable_mode` 对应 `Node.ProcessMode`，默认继承。
- `enable_node_path` 只在设置属性和进树时解析并缓存。
- 子弹飞出屏幕销毁用 `screen_exited`，不要每帧比较坐标。
- 判断当前是否在屏幕内：`is_on_screen`。

## NavigationAgent2D 最短用法

<!-- check: extends CharacterBody2D -->
```gdscript
const SPEED := 90.0

@onready var _agent: NavigationAgent2D = $NavigationAgent2D

func _ready() -> void:
	_agent.path_desired_distance = 4.0
	_agent.target_desired_distance = 4.0
	_agent.velocity_computed.connect(_on_velocity_computed)


func go_to(target: Vector2) -> void:
	_agent.target_position = target


func _physics_process(_delta: float) -> void:
	if NavigationServer2D.map_get_iteration_id(_agent.get_navigation_map()) == 0:
		return
	var wanted := Vector2.ZERO
	if not _agent.is_navigation_finished():
		wanted = global_position.direction_to(_agent.get_next_path_position()) * SPEED
	if _agent.avoidance_enabled:
		_agent.velocity = wanted
	else:
		_on_velocity_computed(wanted)


func _on_velocity_computed(safe_velocity: Vector2) -> void:
	velocity = safe_velocity
	move_and_slide()
```

场景搭法：放 `NavigationRegion2D`，指定 `NavigationPolygon`，用多边形工具画可走区域后点 Bake。多边形边缘与碰撞物体之间留出角色半径，不然角色会卡在碰撞上。

- 地图同步前 `get_next_path_position` 返回自身位置，方向向量为零。官方示例用 `map_get_iteration_id` 为 0 时跳过查询，`_ready` 里不要 await。
- `path_desired_distance` 太大会跳过路径点并走出导航网格，太小会反复重算路径。按角色速度和地图调。
- `is_navigation_finished` 为 true 时不要继续调 `get_next_path_position`，否则站定的角色会抖。
- 避障：`avoidance_enabled` 为 true，把期望速度写到 `NavigationAgent2D.velocity`，在 `velocity_computed` 信号里移动。避障按 agent 数量收费，只给需要的开。
- 开避障后 `velocity_computed` 每物理帧按最后写入的 `velocity` 发射，到达目标后要写入零向量，否则角色继续走。
- 避障必须设过 `target_position`，否则 `safe_velocity` 恒为零。`max_speed` 默认 100，角色速度更高时要同步调大。
- `radius` 只影响避障。寻路半径在烘焙时由 `NavigationPolygon.agent_radius` 决定，不同尺寸的单位要用不同的导航地图。
- 烘焙来源用 `parsed_geometry_type` 与 `parsed_collision_mask` 选择，可以直接从碰撞体生成。代码里建网格用 `NavigationPolygon.vertices` 加 `add_polygon`；`make_polygons_from_outlines` 已弃用。
- TileMapLayer 内置导航限制多，官方建议烘焙成 `NavigationRegion2D`，并关掉 TileMapLayer 的导航。
- 2D 导航网格不能在同一张导航地图里叠放。
- 格子地图用 `AStarGrid2D`，不是导航网格。任意位置到任意位置的实时移动才用 NavigationServer。
- 连接两块不相邻区域用 `NavigationLink2D`，只声明连通和代价，移动仍要自己写。
