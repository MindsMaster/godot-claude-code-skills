# 寻路与离屏处理

VisibleOnScreen 系列、NavigationAgent2D 最短用法、导航网格与避障。

## VisibleOnScreen

<!-- check: extends Node2D -->
```gdscript
@onready var _notifier: VisibleOnScreenNotifier2D = $VisibleOnScreenNotifier2D

func _ready() -> void:
	_notifier.screen_exited.connect(queue_free)
```

```csharp
public partial class Bullet : Node2D
{
    public override void _Ready()
    {
        var notifier = GetNode<VisibleOnScreenNotifier2D>("VisibleOnScreenNotifier2D");
        notifier.ScreenExited += QueueFree;
    }
}
```

- `rect` 手动框住精灵，不随贴图大小自动跟随
- 子弹飞出屏幕销毁用 `screen_exited`，不每帧比较坐标
- 当前是否在屏幕内：`is_on_screen`
- 离屏停处理：敌人加子节点 `VisibleOnScreenEnabler2D`
- `enable_node_path` 默认指向父节点，离屏时目标设为 `PROCESS_MODE_DISABLED`
- `enable_mode` 对应 Node 的处理模式，默认继承
- `enable_node_path` 只在设置属性和进树时解析并缓存

## NavigationAgent2D

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

```csharp
public partial class Walker : CharacterBody2D
{
    private const float Speed = 90.0f;

    private NavigationAgent2D _agent;

    public override void _Ready()
    {
        _agent = GetNode<NavigationAgent2D>("NavigationAgent2D");
        _agent.PathDesiredDistance = 4.0f;
        _agent.TargetDesiredDistance = 4.0f;
        _agent.VelocityComputed += OnVelocityComputed;
    }

    public void GoTo(Vector2 target)
    {
        _agent.TargetPosition = target;
    }

    public override void _PhysicsProcess(double delta)
    {
        if (NavigationServer2D.MapGetIterationId(_agent.GetNavigationMap()) == 0)
        {
            return;
        }
        Vector2 wanted = Vector2.Zero;
        if (!_agent.IsNavigationFinished())
        {
            wanted = GlobalPosition.DirectionTo(_agent.GetNextPathPosition()) * Speed;
        }
        if (_agent.AvoidanceEnabled)
        {
            _agent.Velocity = wanted;
        }
        else
        {
            OnVelocityComputed(wanted);
        }
    }

    private void OnVelocityComputed(Vector2 safeVelocity)
    {
        Velocity = safeVelocity;
        MoveAndSlide();
    }
}
```

场景：放 `NavigationRegion2D`，指定 `NavigationPolygon`，画可走区域后 Bake。

- 可走区域边缘与碰撞物体之间留出角色半径，否则卡在碰撞上
- 地图同步前 `get_next_path_position` 返回自身位置
- `map_get_iteration_id` 为 0 时跳过查询，`_ready` 里不 await
- `path_desired_distance` 太大跳过路径点，太小反复重算
- `is_navigation_finished` 为 true 后不再调 `get_next_path_position`，否则站定抖动

| 避障 | 规则 |
|---|---|
| 开启 | `avoidance_enabled` 为 true，期望速度写 `NavigationAgent2D.velocity`，在 `velocity_computed` 里移动 |
| 到达后 | 写入零向量，否则每物理帧按最后的 `velocity` 继续走 |
| 前提 | 设过 `target_position`，否则 `safe_velocity` 恒为零 |
| `max_speed` | 默认 100，角色更快时同步调大 |
| `radius` | 只影响避障 |
| 开销 | 按 agent 数量收费，只给需要的开 |

## 导航网格

- 寻路半径由烘焙时的 `NavigationPolygon.agent_radius` 决定
- 不同尺寸的单位用不同的导航地图
- 烘焙来源用 `parsed_geometry_type` 与 `parsed_collision_mask` 选，可从碰撞体生成
- 代码建网格：`NavigationPolygon.vertices` 加 `add_polygon`
- `make_polygons_from_outlines` 已弃用
- TileMapLayer 内置导航限制多，官方建议烘焙成 `NavigationRegion2D` 并关掉层导航
- 2D 导航网格不能在同一张导航地图里叠放
- 格子地图用 `AStarGrid2D`，任意位置实时移动才用 NavigationServer
- 连接不相邻区域用 `NavigationLink2D`，只声明连通和代价，移动自己写
