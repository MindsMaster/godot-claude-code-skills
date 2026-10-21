# Camera2D 与 Parallax2D

## 结构

- 相机做玩家子节点最省事，跟随、边界、平滑都是内置。多目标跟随才需要自己算位置并设 `global_position`。
- 同一时刻一个视口只有一个当前相机，切换用 `make_current`。

```ini
[node name="Camera2D" type="Camera2D" parent="Player"]
position_smoothing_enabled = true
position_smoothing_speed = 6.0
drag_horizontal_enabled = true
drag_left_margin = 0.1
drag_right_margin = 0.1
```

## 边界

`limit_*` 是整数像素，值取自地图矩形乘格子尺寸。

<!-- check: extends TileMapLayer -->
```gdscript
func fit_camera_limits(cam: Camera2D) -> void:
	var rect := get_used_rect()
	var size := tile_set.tile_size
	cam.limit_left = rect.position.x * size.x
	cam.limit_top = rect.position.y * size.y
	cam.limit_right = rect.end.x * size.x
	cam.limit_bottom = rect.end.y * size.y
```

- `limit_enabled` 自 4.5 起才有，4.4 上限制总是启用。
- `limit_smoothed` 要 `position_smoothing_enabled` 同时开才有效。

## 平滑与死区

- `position_smoothing_speed` 越大追得越紧。`drag_*_margin` 是死区占半屏的比例，1 表示到屏幕边缘才动，`drag_*_enabled` 开了才生效。
- `drag_horizontal_offset` 只用来设初值或强制值，不会随死区自动更新。
- 瞬间切换位置后调 `reset_smoothing`，否则相机会飞过去。传送且用了物理插值时同样要调 `Node.reset_physics_interpolation`。
- 跟随物理角色且画面抖：`process_callback` 改 `CAMERA2D_PROCESS_PHYSICS`，或打开 `physics/common/physics_interpolation`。
- `zoom` 大于 1 是放大，视野变小。X 与 Y 分量一般取同值。
- `get_screen_center_position` 是相机当前实际看向的中心，`get_target_position` 是目标位置，开平滑时两者不同。

## 震屏

改 `offset`，它可以越过 limit，贴边时也能震。不要移动相机节点本身，会与跟随打架。

<!-- check: extends Camera2D -->
```gdscript
@export var max_offset := 10.0
@export var decay := 1.5

var _trauma := 0.0
var _t := 0.0
var _noise := FastNoiseLite.new()

func _ready() -> void:
	_noise.seed = randi()


func add_trauma(amount: float) -> void:
	_trauma = minf(_trauma + amount, 1.0)


func _process(delta: float) -> void:
	if _trauma <= 0.0:
		offset = Vector2.ZERO
		return
	_t += delta * 80.0
	var power := _trauma * _trauma * max_offset
	offset = Vector2(_noise.get_noise_2d(_t, 0.0), _noise.get_noise_2d(_t, 64.0)) * power
	_trauma = maxf(_trauma - decay * delta, 0.0)
```

- 像素风项目里把结果 `offset.round()`，避免半像素。
- 偏移量与 trauma 的平方成正比，衰减时尾段更柔和。

## Parallax2D（4.3+）

```ini
[node name="Sky" type="Parallax2D" parent="."]
scroll_scale = Vector2(0.2, 1)
repeat_size = Vector2(640, 0)
repeat_times = 3

[node name="Sprite2D" type="Sprite2D" parent="Sky"]
centered = false
```

- 子节点贴图左上角放在 `(0, 0)`，向右下延伸。居中放置会让循环区域只盖一半。
- `repeat_size` 填一张图的尺寸，图要不小于视口。相机缩小看到更多时加大 `repeat_times`，3 表示前后各多一份。
- 贴图比视口小时：缩小视口基准、缩放 Parallax2D、缩放子节点，或用 `Sprite2D` 的 `texture_repeat` 加 `region_enabled` 与 `region_rect` 铺满。子节点缩放时 `repeat_size` 和 `region_rect` 不跟着缩放，要手动乘。
- 官方参考值：森林 `(0.7, 1)`，山 `(0.5, 1)`，低云 `(0.3, 1)`，高云 `(0.2, 1)`，天空 `(0.1, 1)`。
- `scroll_scale` 小于 1 是远景，大于 1 是近景，0 不动。
- `autoscroll` 做云的自动飘动，单位像素每秒。`scroll_offset` 调起始位置。
- `limit_begin` 与 `limit_end` 限制滚动范围。
- 放进 `CanvasLayer` 时 `follow_viewport` 要与 `CanvasLayer.follow_viewport_enabled` 一致。
- 旧的 `ParallaxBackground` 加 `ParallaxLayer` 已弃用。
