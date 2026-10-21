---
name: godot-2d
description: Godot 4 的 2D 游戏用内置节点怎么搭 CharacterBody2D move_and_slide 角色移动 碰撞层与 mask 规划 Area2D 触发区 TileMapLayer TileSet 瓦片地图 地形 自定义数据层 Camera2D limit 平滑 drag zoom 震屏 Parallax2D 视差背景 y_sort_enabled z_index 绘制顺序 CanvasLayer HUD 像素风 pixel art stretch viewport integer scale snap_2d_transforms_to_pixel PointLight2D CanvasModulate 2D 光照 VisibleOnScreenNotifier2D VisibleOnScreenEnabler2D 离屏暂停 NavigationAgent2D 寻路 RayCast2D ShapeCast2D 射线检测 intersect_ray intersect_shape intersect_point direct_space_state 物理查询 Line2D Polygon2D _draw 自绘 2D HDR glow 泛光。用于写 2D 场景、做 2D 相机或地图、查某个 2D 需求有没有内置节点。3D 里放 2D 角色见 godot-2d-in-3d。
---

# Godot 2D

2D 游戏常见需求的内置节点选择、最短写法和易错点。动画播放、着色器特效、UI 控件、输入映射不在这里。3D 场景里放 2D 角色走 godot-2d-in-3d。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 角色、敌人移动与碰撞 | `CharacterBody2D.move_and_slide` | 手写碰撞检测与滑动 |
| 拾取、伤害区、触发区 | `Area2D` 加信号 | 手写矩形相交 |
| 脚下、身前持续探测 | `RayCast2D`、`ShapeCast2D` 节点 | 每帧 new 查询参数 |
| 一次性射线、点选、范围内有谁 | `direct_space_state` 的 `intersect_ray`、`intersect_point`、`intersect_shape` | 遍历全部物体手算相交 |
| 瓦片地图 | `TileMapLayer` 加 `TileSet` | `TileMap` 已弃用，每格一个节点 |
| 相机边界 | `Camera2D` 的 `limit_*` | 每帧手写夹取 |
| 相机平滑与死区 | `position_smoothing_enabled`、`drag_*_enabled` | 手写 SmoothDamp |
| 震屏 | `Camera2D.offset` 加 `FastNoiseLite` | 移动相机节点本身 |
| 视差背景 | `Parallax2D`（4.3+） | `ParallaxBackground` 与 `ParallaxLayer` 已弃用，手算偏移 |
| 是否在屏幕内 | `VisibleOnScreenNotifier2D` | 手写矩形与相机比较 |
| 离屏暂停逻辑 | `VisibleOnScreenEnabler2D` | 每帧距离判断 |
| 遮挡排序 | `y_sort_enabled`、`z_index` | 每帧改 z_index |
| 固定在屏幕上的层 | `CanvasLayer` | 手算相机反向偏移 |
| 光照与阴影 | `PointLight2D`、`DirectionalLight2D`、`LightOccluder2D`、`CanvasModulate` | 多个 SubViewport 拼光照 |
| 泛光 | `WorldEnvironment` 的 `Environment.glow_enabled` | SubViewport 手搓 bloom |
| 实时寻路 | `NavigationRegion2D` 加 `NavigationAgent2D` | 手写 A* 与路径跟随 |
| 格子寻路 | `AStarGrid2D` | 手写 A* |
| 线、轨迹、血条形状 | `Line2D`、`Polygon2D`、`_draw` | 一格一个 `ColorRect` |
| 大量相同物体 | `MultiMeshInstance2D` | 几千个 Sprite2D |
| 像素风 | 项目设置，见下 | 手写缩放与取整 |
| 命中闪白 | shader uniform 加 Tween | 把 Modulate 调到大于 1 |

## 做法

### CharacterBody2D

<!-- check: extends CharacterBody2D -->
```gdscript
const SPEED := 160.0
const JUMP := -320.0

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity += get_gravity() * delta
	elif Input.is_action_just_pressed("jump"):
		velocity.y = JUMP
	velocity.x = Input.get_axis("left", "right") * SPEED
	move_and_slide()
```

<!-- check: extends CharacterBody2D -->
```gdscript
func _physics_process(_delta: float) -> void:
	velocity = Input.get_vector("left", "right", "up", "down") * 120.0
	move_and_slide()
```

- 俯视角把 `motion_mode` 设为 `MOTION_MODE_FLOATING`。默认的 grounded 模式有地面、墙、天花板之分，俯视角会出现滑坡与卡边行为。
- `move_and_slide` 自带 delta，`velocity` 单位是像素每秒，不要乘 delta。`move_and_collide` 要乘。
- 斜坡不脱地用 `floor_snap_length`，上下坡速度一致开 `floor_constant_speed`，站定不下滑是 `floor_stop_on_slope`。
- 撞到什么：`get_slide_collision(i).get_collider()`，数量 `get_slide_collision_count`。
- 平台带动玩家是内置的，离开平台的速度处理看 `platform_on_leave`。

<!-- check: extends CharacterBody2D -->
```csharp
public override void _PhysicsProcess(double delta)
{
    Vector2 v = Velocity;
    v.X = Input.GetAxis("left", "right") * 160f;
    Velocity = v;
    MoveAndSlide();
}
```

C# 里 Velocity 是结构体属性，直接给它的 X 赋值编译不过，先取副本再整体赋回。

### 碰撞层与 mask

layer 是我在哪一层，mask 是我扫描哪些层。先在项目设置里给层起名，代码只用 1 到 32 的编号。

```ini
[layer_names]

2d_physics/layer_1="world"
2d_physics/layer_2="player"
2d_physics/layer_3="enemy"
2d_physics/layer_4="player_hitbox"
2d_physics/layer_5="enemy_hitbox"
```

| 对象 | layer | mask |
|---|---|---|
| 地形、墙 | world | 无 |
| 玩家 | player | world |
| 敌人 | enemy | world |
| 玩家攻击判定 Area2D | player_hitbox | enemy |
| 敌人攻击判定 Area2D | enemy_hitbox | player |
| 拾取物 Area2D | 无 | player |

- Area2D 作为检测方只设 mask，自己不需要在任何 layer 里，除非别的 Area2D 要检测它。
- 代码里改单个位：`set_collision_layer_value(2, true)`、`set_collision_mask_value(1, true)`，编号从 1 起。
- 函数参数里的位掩码是 `1 << (层号 - 1)`，全部层是 `0xffffffff`。
- 敌人之间不想互相挤：敌人的 mask 里不放 enemy 层。

### Area2D

<!-- check: extends Area2D -->
```gdscript
signal collected(by: Node2D)

@onready var _shape: CollisionShape2D = $CollisionShape2D

func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	collected.emit(body)
	_shape.set_deferred("disabled", true)
```

- 信号回调在物理查询期间触发，禁用形状、改 `monitoring` 用 `set_deferred`，或 `call_deferred`。
- `get_overlapping_bodies` 每个物理步更新一次，刚移动完立刻查不到，优先用信号。
- `monitoring` 是我检测别人，`monitorable` 是别人能检测我。
- 撞 TileMapLayer 时 `body_entered` 的参数是 `TileMapLayer`，不是格子。需要格子见 references/tilemaplayer.md。

### 射线与空间查询

| 需求 | 用这个 |
|---|---|
| 固定方向持续探测，脚下、身前 | `RayCast2D` 节点，每物理步自动更新 |
| 有宽度的探测，台阶、宽激光 | `ShapeCast2D` 节点 |
| 一次性射线，hitscan、视线 | `intersect_ray` |
| 点下去有谁 | `intersect_point` |
| 圆形或矩形范围内有谁 | `intersect_shape` |

```ini
[node name="GroundProbe" type="RayCast2D" parent="."]
target_position = Vector2(0, 12)
collision_mask = 1
```

<!-- check: extends CharacterBody2D -->
```gdscript
@onready var _ground: RayCast2D = $GroundProbe

func _physics_process(_delta: float) -> void:
	if _ground.is_colliding():
		var point: Vector2 = _ground.get_collision_point()
		print(point, _ground.get_collider())
```

<!-- check: extends CharacterBody2D -->
```gdscript
const MASK := (1 << 0) | (1 << 2)

func _physics_process(_delta: float) -> void:
	if not Input.is_action_just_pressed("fire"):
		return
	var query := PhysicsRayQueryParameters2D.create(
			global_position, get_global_mouse_position(), MASK, [get_rid()])
	var hit: Dictionary = get_world_2d().direct_space_state.intersect_ray(query)
	if not hit.is_empty():
		var point: Vector2 = hit.position
		print(point, hit.collider)
```

- 节点 `RayCast2D.target_position` 相对自己，`exclude_parent` 默认 true 排除父级碰撞体。同一物理步里改了 `target_position` 或位置就要读结果，先 `force_raycast_update`。`enabled` 为 false 时 `force_raycast_update` 仍然有效。`ShapeCast2D` 对应 `force_shapecast_update`，要先给 `shape`。
- `intersect_ray` 结果是字典，没命中为空，命中有 `position` `normal` `collider` `collider_id` `rid` `shape`。`intersect_point` 与 `intersect_shape` 返回字典数组，没有 `position`，第二个参数 `max_results` 默认 32。
- 查询参数的 mask 默认全部层，节点的 `collision_mask` 默认只有第 1 层。
- `ShapeCast2D`、`intersect_shape`、`intersect_point` 的完整写法、C#、结果字段：references/physics-queries.md。

### TileMapLayer

- 新代码一律 `TileMapLayer`，一层一个节点，多层靠多个节点。旧 `TileMap` 在编辑器里一键转换。
- 读写：`set_cell(coords, source_id, atlas_coords)`、`erase_cell`、`get_cell_tile_data(coords).get_custom_data("name")`、`local_to_map`、`map_to_local`。
- 碰撞、导航、遮挡、自定义数据、地形都在 TileSet 里先建对应层再给每块瓦片填。
- 自动连接用 `set_cells_terrain_connect`，不要自己写邻格位掩码。
- 带逻辑的物件如宝箱、火把用 TileSet 的 Scenes Collection 源，或直接放场景，不要在 `_draw` 里模拟。
- 手写 `.tscn` 预置格子用无头脚本 `set_cell` 加 `ResourceSaver.save` 生成，手编 `tile_map_data` 头 2 字节必须是 0，否则整层读成 0 格：references/tilemaplayer.md。
- 完整表格、运行时改瓦片、碰撞回查格子、Y 排序：references/tilemaplayer.md。

### Camera2D 与 Parallax2D

```ini
[node name="Camera2D" type="Camera2D" parent="Player"]
position_smoothing_enabled = true
position_smoothing_speed = 6.0
limit_left = 0
limit_top = 0
limit_right = 2560
limit_bottom = 720
```

- 相机做玩家子节点，跟随、边界、平滑、死区都是内置。`limit_*` 是整数像素。
- `limit_enabled` 自 4.5 起才有，4.4 上限制总是启用。
- 震屏改 `offset` 不改节点位置，`offset` 可以越过 limit。噪声用 `FastNoiseLite`。
- 瞬间切换位置后调 `reset_smoothing`，否则相机飞过去。
- 跟随物理角色且画面抖：`process_callback` 改 `CAMERA2D_PROCESS_PHYSICS`，或打开 `physics/common/physics_interpolation`。
- `zoom` 大于 1 是放大，视野变小。
- 视差背景用 `Parallax2D`（4.3+）：子节点贴图左上角放 `(0, 0)`，`scroll_scale` 小于 1 是远景，`repeat_size` 填图的尺寸，缩小视野时加大 `repeat_times`。
- 完整震屏代码、从 TileMapLayer 算 limit、Parallax2D 摆法和尺寸问题：references/camera-parallax.md。

### y_sort_enabled 与 z_index

- 俯视角让下方的物体盖住上方：共同父节点开 `y_sort_enabled`，子节点按 Y 排序。排序依据是节点原点，所以角色原点放脚底。
- 开了的父节点下，子节点自己没开时它的整棵子树作为一个整体参与排序。
- Y 排序只在相同 `z_index` 的节点之间生效。
- `z_index` 默认相对父节点累加，`z_as_relative` 关掉才是绝对值。UI 和特效层用 CanvasLayer，不靠 z_index 堆高。
- 同级不排序时，场景树里靠后的画在上面。

### CanvasLayer

- HUD、暂停菜单、转场放 `CanvasLayer`，不随 Camera2D 移动缩放。`layer` 大的在上，负数在世界后面。
- 同一个 `layer` 值的多个 CanvasLayer 前后顺序不确定，别靠它。
- 想让 CanvasLayer 里的东西跟着世界走并带深度感：`follow_viewport_enabled` 加 `follow_viewport_scale`。

### 像素风

```ini
[display]

window/size/viewport_width=640
window/size/viewport_height=360
window/stretch/mode="viewport"
window/stretch/scale_mode="integer"

[rendering]

textures/canvas_textures/default_texture_filter=0
```

- 设置路径：`display/window/stretch/mode`、`display/window/stretch/scale_mode`、`rendering/textures/canvas_textures/default_texture_filter`、`rendering/2d/snap/snap_2d_transforms_to_pixel`、`rendering/2d/snap/snap_2d_vertices_to_pixel`。
- 4.7 新建项目默认 `canvas_items` 加 `expand`，像素风项目要手动改成 `viewport`。
- 取整两个设置官方不建议同开，只开 `snap_2d_transforms_to_pixel`。取整与相机平滑一起开会更不平滑。
- `Sprite2D.centered` 默认 true，奇数尺寸贴图会落在半像素上变形。
- 抖动排查、字体、光影分辨率、HDR：references/pixel-art.md。

### 光照、离屏、寻路、自绘、泛光

这几块的最短代码放 references，需求出现时去读。

| 需求 | 要点 | 文件 |
|---|---|---|
| 2D 光照与阴影 | `CanvasModulate` 压暗，`PointLight2D` 必须有 `texture`，`LightOccluder2D` 投影 | references/lighting-glow.md |
| 泛光与 HDR 2D | `rendering/viewport/hdr_2d` 加 `WorldEnvironment`，`modulate` 大于 1 发光 | references/lighting-glow.md |
| 离屏销毁与暂停 | `VisibleOnScreenNotifier2D`，`VisibleOnScreenEnabler2D` | references/navigation-culling.md |
| 寻路 | `NavigationRegion2D` 烘焙，`NavigationAgent2D` 每物理帧取 `get_next_path_position` | references/navigation-culling.md |
| 线、多边形、网格线 | `Line2D`、`Polygon2D`、`_draw` 加 `queue_redraw` | references/drawing.md |

## 陷阱

- `TileMap`、`ParallaxBackground`、`ParallaxLayer` 已弃用，旧教程里常见，别照抄。
- 俯视角忘了 `MOTION_MODE_FLOATING`：默认 grounded 模式按 `up_direction` 区分地面与墙并对斜坡加减速，floating 模式所有碰撞按墙处理，滑动速度恒定。
- 碰撞形状的 `disabled` 官方要求用 `set_deferred` 改，信号回调里直接改容易出错。
- `direct_space_state` 在 `_process` 或 `_input` 里取：默认设置下不报错但只反映上一个物理步，开了 `physics/2d/run_on_separate_thread` 就报 `Space state is inaccessible` 并返回 null。查询放进 `_physics_process`，输入事件里只记标志。
- `PhysicsRayQueryParameters2D` 不会自动排除发射者，射线从体内出发加 `hit_from_inside` 或穿过自己的形状都会命中自己，`exclude` 填 `[get_rid()]`。节点 `RayCast2D` 才有 `exclude_parent`。
- `collide_with_areas` 在 `RayCast2D`、`ShapeCast2D` 和三种 query 参数里默认都是 false，射线与点查询打不到 `Area2D`，受击框用 Area2D 时要手动开。
- `Area2D` 要检测 TileMapLayer 或 StaticBody2D，对方的 layer 要出现在它的 mask 里，并且 TileSet 里配了碰撞形状。
- `Camera2D.zoom` 不计入位图字体与光栅化字体的过采样，缩放后文字会糊。清晰文字放进 CanvasLayer，或开 MSDF。
- `viewport` 拉伸模式下场景整体低分辨率渲染，精灵没有亚像素位置和旋转。需要时走 `canvas_items` 加取整。
- 把 2D 节点每帧手算透视缩放伪 3D：位置、缩放、排序、光照都要自己维护。需要真透视、旋转镜头、光照阴影时改真 3D 加 `Sprite3D`，取舍见 godot-2d-in-3d。
- `Sprite2D` 的切片动画用 `hframes`、`vframes` 与 `frame_coords`，朝向翻转用 `flip_h`。
- 一格一个 `ColorRect`、手写边界夹取、手写 SmoothDamp、手写矩形与相机相交判断，都有内置替代，见先查内置。

## 参考

- references/camera-parallax.md 相机边界、平滑死区、完整震屏、Parallax2D 尺寸与摆法
- references/physics-queries.md ShapeCast2D、intersect_shape、intersect_point、C# 写法、结果字段
- references/tilemaplayer.md TileSet 配置表、格子读写、地形、碰撞回查、运行时改瓦片、Y 排序
- references/pixel-art.md 两条像素风路线、抖动排查、导入与字体、光影分辨率
- references/lighting-glow.md 2D 光照与阴影、HDR 2D 与 glow
- references/navigation-culling.md VisibleOnScreen 系列、NavigationAgent2D 最短用法
- references/drawing.md Line2D、Polygon2D、_draw 的选择与写法
- https://docs.godotengine.org/en/stable/tutorials/physics/ray-casting.html
- https://docs.godotengine.org/en/stable/tutorials/2d/using_tilemaps.html
- https://docs.godotengine.org/en/stable/tutorials/2d/2d_parallax.html
- https://docs.godotengine.org/en/stable/tutorials/2d/2d_lights_and_shadows.html
- https://docs.godotengine.org/en/stable/tutorials/2d/canvas_layers.html
- https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html
- https://docs.godotengine.org/en/stable/tutorials/navigation/navigation_introduction_2d.html
