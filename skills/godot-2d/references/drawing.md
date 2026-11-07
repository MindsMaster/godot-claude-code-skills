# Line2D、Polygon2D 与 _draw

线、多边形与自绘的选择、`_draw` 写法、Line2D 拖尾、Polygon2D。

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

- 一格一个 `ColorRect` 画网格是反模式，换成一个 `_draw`

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

```csharp
public partial class Grid : Node2D
{
    private Vector2I _size = new(40, 23);

    [Export] public int Cell { get; set; } = 16;

    [Export]
    public Vector2I Size
    {
        get => _size;
        set
        {
            _size = value;
            QueueRedraw();
        }
    }

    public override void _Draw()
    {
        var color = new Color(1, 1, 1, 0.15f);
        for (int x = 0; x <= _size.X; x++)
        {
            DrawLine(new Vector2(x * Cell, 0), new Vector2(x * Cell, _size.Y * Cell), color);
        }
        for (int y = 0; y <= _size.Y; y++)
        {
            DrawLine(new Vector2(0, y * Cell), new Vector2(_size.X * Cell, y * Cell), color);
        }
    }
}
```

- 绘制命令被缓存，`queue_redraw` 之后才重新执行 `_draw`
- 数据变了才调 `queue_redraw`，放在 setter 里
- 不在 `_process` 里无条件 `queue_redraw`
- 节点不可见或离屏时 `set_process(false)`
- `draw_set_transform` 设置之后所有绘制的局部变换
- `width` 为负画细线，缩放后不变粗；要随缩放变粗传正数
- `draw_multimesh` 的纹理存成成员，局部变量在绘制前已销毁
- 位图字体与光栅化字体的 `draw_string` 缩放后变糊

### 多边形三角剖分

`draw_colored_polygon` 与 `draw_polygon` 每次绘制都三角剖分，按局部坐标判定，与屏幕像素无关。

- 多边形很小时凸多边形也会剖分失败
- 失败报 `Invalid polygon data, triangulation failed`，不画
- 失败尺寸没有固定阈值
- 会缩到接近 0 的形状设一个下限，低于下限不画
- 圆用 `draw_circle`，不走三角剖分
- 自己能算三角形时用 `RenderingServer.canvas_item_add_triangle_array` 传索引

## Line2D

| 属性 | 用途 |
|---|---|
| `points` | 局部坐标 |
| `closed` | true 闭合 |
| `joint_mode` `begin_cap_mode` `end_cap_mode` | 关节与端点 |
| `round_precision` | 圆角精度 |
| `texture_mode` | `LINE_TEXTURE_TILE` 平铺，`LINE_TEXTURE_STRETCH` 拉伸 |

拖尾：`top_level = true` 并保持节点在原点，每帧追加目标的 `global_position`，超长 `remove_point(0)`。

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

```csharp
public partial class Trail : Line2D
{
    [Export] public Node2D Target { get; set; }
    [Export] public int MaxPoints { get; set; } = 24;

    public override void _Ready()
    {
        TopLevel = true;
        GlobalPosition = Vector2.Zero;
    }

    public override void _PhysicsProcess(double delta)
    {
        AddPoint(Target.GlobalPosition);
        if (GetPointCount() > MaxPoints)
        {
            RemovePoint(0);
        }
    }
}
```

## Polygon2D

| 属性或方法 | 用途 |
|---|---|
| `polygon` | 顶点 |
| `uv` | 贴图坐标 |
| `vertex_colors` | 逐顶点着色 |
| `polygons` | 凹多边形的三角划分 |
| `skeleton`、`add_bone` | 2D 骨骼蒙皮，动画见 godot-animation |

- 随地形生成的复杂凹形，先用 `Geometry2D` 做布尔运算和三角化
