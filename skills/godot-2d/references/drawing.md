# Line2D、Polygon2D 与 _draw

## 选择

| 需求 | 用 |
|---|---|
| 轨迹、激光、绳子、闪电 | `Line2D`，`width_curve` 控粗细，`gradient` 控颜色 |
| 填充的任意多边形、带贴图的形状 | `Polygon2D` |
| 网格线、血条框、范围圈、调试图形 | `_draw` 里 `draw_line`、`draw_rect`、`draw_circle`、`draw_polyline` |
| 虚线 | `draw_dashed_line` |
| 成百上千条线 | 一个 `_draw` 里 `draw_multiline`，比逐条 `draw_line` 快 |
| 成百上千个同类图形 | `MultiMeshInstance2D` |
| 地面、平台 | `TileMapLayer`，或 `Sprite2D` 开 `region_enabled` 与 `texture_repeat` |
| 进度条 | `ProgressBar`、`TextureProgressBar`，不改 `ColorRect` 的 size |
| 带圆角、描边的面板 | `StyleBoxFlat` 或 `Panel`，不叠多个 `ColorRect` |

一格一个 `ColorRect` 画地板刻度、网格是最常见的反模式，几百个节点换一次 `_draw` 即可。

## _draw

<!-- check: extends Node2D -->
```gdscript
@export var cell := 16
@export var size := Vector2i(40, 23):
	set(value):
		size = value
		queue_redraw()

func _draw() -> void:
	for x in size.x + 1:
		draw_line(Vector2(x * cell, 0), Vector2(x * cell, size.y * cell), Color(1, 1, 1, 0.15))
	for y in size.y + 1:
		draw_line(Vector2(0, y * cell), Vector2(size.x * cell, y * cell), Color(1, 1, 1, 0.15))
```

- `_draw` 只在 `queue_redraw` 之后重新执行，绘制命令被缓存。数据变了才调 `queue_redraw`，放在 setter 里最干净。
- 不要在 `_process` 里无条件 `queue_redraw`。节点不可见或离屏时用 `set_process(false)` 停掉。
- `draw_set_transform` 设置之后所有绘制的局部变换。
- `draw_line` 等的 `width` 为负时画细线，缩放后不变粗。想随缩放变粗传正数。
- `draw_multimesh` 的纹理不能只存在局部变量里，GDScript 里函数结束后变量先销毁，绘制在之后才发生，存成成员。
- 位图字体与光栅化字体用 `draw_string` 时受缩放影响变糊，同 Camera2D 的 zoom 说明。

## Line2D

- `points` 是局部坐标。`closed` 为 true 闭合。
- 关节、端点：`joint_mode`、`begin_cap_mode`、`end_cap_mode`，圆角精度 `round_precision`。
- 贴纹理用 `texture_mode`：`LINE_TEXTURE_TILE` 平铺，`LINE_TEXTURE_STRETCH` 拉伸。
- 拖尾：`top_level = true` 并保持节点在原点，每帧把目标的 `global_position` 追加成点，超出长度 `remove_point(0)`。

<!-- check: extends Line2D -->
```gdscript
@export var target: Node2D
@export var max_points := 24

func _ready() -> void:
	top_level = true
	global_position = Vector2.ZERO


func _physics_process(_delta: float) -> void:
	add_point(target.global_position)
	if get_point_count() > max_points:
		remove_point(0)
```

## Polygon2D

- `polygon` 顶点，`uv` 贴图坐标，`vertex_colors` 逐顶点着色，`polygons` 指定凹多边形的三角划分。
- `skeleton` 与 `add_bone` 做 2D 骨骼蒙皮，动画部分见 godot-animation。
- 多边形随地形生成时，复杂凹形先用 `Geometry2D` 做布尔运算和三角化，不手写。
