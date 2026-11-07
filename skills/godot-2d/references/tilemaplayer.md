# TileMapLayer 与 TileSet

TileSet 配置、格子读写、地形自动连接、手写 terrain 与 `tile_map_data`、碰撞、运行时改瓦片、排序、导航、图案、存档。

## 结构

- `TileSet` 是资源，放在每个 `TileMapLayer` 的 `tile_set`，多层共用一个
- 一个 `TileMapLayer` 节点一层，同一格一层只放一块
- 地面、墙、装饰分成多个节点，节点顺序就是绘制顺序
- `TileMapLayer` 4.3+，4.4 以前的项目升级后再转
- 旧 `TileMap` 转换：底部面板工具箱菜单 Extract TileMap layers as individual TileMapLayer nodes
- 新代码不再写 `TileMap` 的 `layer` 参数

## TileSet 里要建的东西

| 需求 | TileSet 里建 | 给每块瓦片设 |
|---|---|---|
| 碰撞 | Physics Layers，设 collision layer 与 mask | 碰撞多边形，单向平台勾 one way |
| 寻路 | Navigation Layers | 导航多边形 |
| 光照遮挡 | Occlusion Layers | 遮挡多边形 |
| 自定义属性 | Custom Data Layers，起名与类型 | 每块填值 |
| 自动连接 | Terrain Sets 与 Terrains | 每块的 terrain 和 peering bits |
| 带逻辑的物件 | 新增 Scenes Collection 源 | 指定场景 |
| 动画瓦片 | 图集源里设瓦片的动画帧数与列数 | 无 |

- Terrain Set 的 mode：`TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES`
- 另有 `TileSet.TERRAIN_MODE_MATCH_CORNERS`、`TileSet.TERRAIN_MODE_MATCH_SIDES`
- 先建 Physics Layer 才能画碰撞多边形，导航和遮挡同理
- 同一块瓦片要不同自定义数据时建 alternative tile，不另开图集

## 读写格子

```gdscript
extends TileMapLayer

const SOURCE_ID := 0
const FLOOR := Vector2i(0, 0)

func paint(cell: Vector2i) -> void:
	set_cell(cell, SOURCE_ID, FLOOR)


func clear_cell(cell: Vector2i) -> void:
	erase_cell(cell)


func damage_at(world_pos: Vector2) -> int:
	var cell := local_to_map(to_local(world_pos))
	var data := get_cell_tile_data(cell)
	if data == null:
		return 0
	return data.get_custom_data("damage")


func cell_center_world(cell: Vector2i) -> Vector2:
	return to_global(map_to_local(cell))
```

```csharp
public partial class GroundLayer : TileMapLayer
{
    private const int SourceId = 0;
    private static readonly Vector2I Floor = new(0, 0);

    public void Paint(Vector2I cell)
    {
        SetCell(cell, SourceId, Floor);
    }

    public void ClearCell(Vector2I cell)
    {
        EraseCell(cell);
    }

    public int DamageAt(Vector2 worldPos)
    {
        Vector2I cell = LocalToMap(ToLocal(worldPos));
        TileData data = GetCellTileData(cell);
        if (data == null)
        {
            return 0;
        }
        return data.GetCustomData("damage").AsInt32();
    }

    public Vector2 CellCenterWorld(Vector2I cell)
    {
        return ToGlobal(MapToLocal(cell));
    }
}
```

- 空格子 `get_cell_source_id` 为 -1，`get_cell_tile_data` 返回 null，先判空
- `local_to_map` 吃局部坐标，世界坐标先 `to_local`
- `map_to_local` 返回格子中心，不含 `TileData.texture_origin`
- 邻格用 `get_surrounding_cells` 或 `get_neighbor_cell`，六边形也正确

| 取区域 | 方法 |
|---|---|
| 全部格子 | `get_used_cells` |
| 按源和图集坐标过滤 | `get_used_cells_by_id` |
| 包围盒 | `get_used_rect` |

- 批量改格子后帧尾统一更新
- 立刻要读碰撞或导航时调 `update_internals`
- 之后 `move_and_collide` 马上撞得到新格子
- `intersect_point` 这类空间查询仍要等下一个物理步

## 地形自动连接

```gdscript
extends TileMapLayer

const TERRAIN_SET := 0
const TERRAIN_GROUND := 0

func paint_ground(cells: Array[Vector2i]) -> void:
	set_cells_terrain_connect(cells, TERRAIN_SET, TERRAIN_GROUND)
```

```csharp
public partial class TerrainPainter : TileMapLayer
{
    private const int TerrainSet = 0;
    private const int TerrainGround = 0;

    public void PaintGround(Godot.Collections.Array<Vector2I> cells)
    {
        SetCellsTerrainConnect(cells, TerrainSet, TerrainGround);
    }
}
```

- `set_cells_terrain_connect` 设为该地形并与邻格连接，可能改邻格
- `set_cells_terrain_path` 按路径顺序连接，适合道路
- TileSet 没配全 peering bits 时结果不对，先查 TileSet
- 自己按邻格位掩码选瓦片的代码可删掉

挖掉地形格子时 terrain 设为 -1，邻格边缘跟着重选：

```gdscript
extends TileMapLayer

const TERRAIN_SET := 0

func dig(cell: Vector2i) -> void:
	set_cells_terrain_connect([cell], TERRAIN_SET, -1)
```

```csharp
public partial class Digger : TileMapLayer
{
    private const int TerrainSet = 0;

    public void Dig(Vector2I cell)
    {
        SetCellsTerrainConnect(new Godot.Collections.Array<Vector2I> { cell }, TerrainSet, -1);
    }
}
```

- `erase_cell` 只清这一格，邻格仍是旧瓦片
- 引擎文档没写 -1，行为以 4.7.2 实测为准
- 没有瓦片能拼出当前邻接组合时，该格留空
- 3x3 九宫格只能铺宽高都不小于 2 格的矩形
- 一格厚的浮台要图集里有左端、中段、右端三块单独瓦片

## 手写 TileSet 的 terrain

格式取自 4.7.2 用 `ResourceSaver.save` 存出的 TileSet。

```ini
[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_1"]
texture = ExtResource("2")
0:0/0 = 0
0:0/0/terrain_set = 0
0:0/0/terrain = 0
0:0/0/physics_layer_0/polygon_0/points = PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)
0:0/0/terrains_peering_bit/right_side = 0
0:0/0/terrains_peering_bit/bottom_right_corner = 0
0:0/0/terrains_peering_bit/bottom_side = 0

[sub_resource type="TileSet" id="TileSet_1"]
physics_layer_0/collision_layer = 1
terrain_set_0/mode = 0
terrain_set_0/terrain_0/name = "Ground"
terrain_set_0/terrain_0/color = Color(0.3, 0.6, 0.2, 1)
sources/0 = SubResource("TileSetAtlasSource_1")
```

| 位置 | 属性 | 含义 |
|---|---|---|
| TileSet | `terrain_set_N/mode` | `TileSet.TerrainMode`，0 角加边，1 只角，2 只边 |
| TileSet | `terrain_set_N/terrain_M/name`、`color` | 第 M 个 terrain，写 name 或 color 之一才存在 |
| 瓦片 | `X:Y/0/terrain_set` | 所属 terrain set，默认 -1 |
| 瓦片 | `X:Y/0/terrain` | 瓦片自己的 terrain，默认 -1 |
| 瓦片 | `X:Y/0/terrains_peering_bit/名字` | 该方向的邻居必须是哪个 terrain，值是 terrain 序号 |

- 不写的 peering bit 是 -1，表示该方向没有地形

方形瓦片的 peering bit 名字、`TileSet.CellNeighbor` 常量与可用 mode：

| 名字 | 常量 | mode 0 | mode 1 | mode 2 |
|---|---|---|---|---|
| `right_side` | `TileSet.CELL_NEIGHBOR_RIGHT_SIDE` 0 | 有 | 无 | 有 |
| `bottom_right_corner` | `TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER` 3 | 有 | 有 | 无 |
| `bottom_side` | `TileSet.CELL_NEIGHBOR_BOTTOM_SIDE` 4 | 有 | 无 | 有 |
| `bottom_left_corner` | `TileSet.CELL_NEIGHBOR_BOTTOM_LEFT_CORNER` 7 | 有 | 有 | 无 |
| `left_side` | `TileSet.CELL_NEIGHBOR_LEFT_SIDE` 8 | 有 | 无 | 有 |
| `top_left_corner` | `TileSet.CELL_NEIGHBOR_TOP_LEFT_CORNER` 11 | 有 | 有 | 无 |
| `top_side` | `TileSet.CELL_NEIGHBOR_TOP_SIDE` 12 | 有 | 无 | 有 |
| `top_right_corner` | `TileSet.CELL_NEIGHBOR_TOP_RIGHT_CORNER` 15 | 有 | 有 | 无 |

- 只给连着地面的方向写 bit，朝外的方向不写
- 每块写满 8 个 bit 时只能选出个别瓦片，结果是散乱空洞
- mode 2 多写 corner bit 不报错，结果与只写 side 相同
- mode 0 只写 side 时矩形地面也能连对，但转角无 corner 约束

3x3 九宫格图集，mode 0 下每块要写的 bit，mode 2 只取 side 列，mode 1 只取 corner 列：

| 瓦片 | side | corner |
|---|---|---|
| 左上 0:0 | right bottom | bottom_right |
| 顶 1:0 | left right bottom | bottom_left bottom_right |
| 右上 2:0 | left bottom | bottom_left |
| 左 0:1 | top right bottom | top_right bottom_right |
| 中 1:1 | top right bottom left | 四个 corner 全写 |
| 右 2:1 | top left bottom | top_left bottom_left |
| 左下 0:2 | top right | top_right |
| 底 1:2 | top left right | top_left top_right |
| 右下 2:2 | top left | top_left |

- 预置格子按位置选瓦片：顶行用顶行瓦片，最左列用左列，内部用中间块
- 无头脚本里直接 `set_cells_terrain_connect` 最省事

## 碰撞

- 碰撞形状按 `physics_quadrant_size` 分块合并，默认 16x16 格一块
- Area2D 的 `body_entered` 参数是 `TileMapLayer`，不是单个格子
- 被撞的格子：`KinematicCollision2D.get_collider_rid` 配 `TileMapLayer.get_coords_for_body_rid`
- 默认返回块坐标，要精确格子须把 `physics_quadrant_size` 设成 1
- 设成 1 会关掉形状合并
- 会动的 TileMapLayer，如移动平台，开 `use_kinematic_bodies`
- 瓦片碰撞多边形可勾单向，margin 在多边形属性里
- 关碰撞用 `TileMapLayer.collision_enabled`，不删 Physics Layer

## 运行时改瓦片属性

```gdscript
extends TileMapLayer

var _flash: Dictionary = {}

func _use_tile_data_runtime_update(coords: Vector2i) -> bool:
	return _flash.has(coords)


func _tile_data_runtime_update(_coords: Vector2i, tile_data: TileData) -> void:
	tile_data.modulate = Color(1.0, 0.5, 0.5)


func flash(coords: Vector2i) -> void:
	_flash[coords] = true
	notify_runtime_tile_data_update()
```

```csharp
public partial class FlashLayer : TileMapLayer
{
    private readonly HashSet<Vector2I> _flash = new();

    public override bool _UseTileDataRuntimeUpdate(Vector2I coords)
    {
        return _flash.Contains(coords);
    }

    public override void _TileDataRuntimeUpdate(Vector2I coords, TileData tileData)
    {
        tileData.Modulate = new Color(1.0f, 0.5f, 0.5f);
    }

    public void Flash(Vector2I coords)
    {
        _flash.Add(coords);
        NotifyRuntimeTileDataUpdate();
    }
}
```

- `_use_tile_data_runtime_update` 只对需要的格子返回 true，多返回拖慢整层
- `tile_data` 的子资源与 TileSet 共享，改碰撞、导航、遮挡多边形前先 `duplicate()`
- 结果会变时调 `notify_runtime_tile_data_update`，帧尾更新，开销大
- 不每帧调 `notify_runtime_tile_data_update`
- 破坏地形这类一次性变化直接 `set_cell` 或 `erase_cell`

## 排序与渲染

- 俯视角：`TileMapLayer` 开 `y_sort_enabled`
- 瓦片按 `TileData.y_sort_origin` 加层的 `y_sort_origin` 排
- 层的 `y_sort_origin` 可用来垫高一层
- 角色与 TileMapLayer 放在同一个开了 `y_sort_enabled` 的父节点下
- 开 Y 排序后 `rendering_quadrant_size` 不生效，瓦片按 Y 分组
- `x_draw_order_reversed` 只在 Y 排序打开时有意义
- 大地图保持默认 `rendering_quadrant_size`
- 逐块材质或颜色用 `TileData.material`、`TileData.modulate`

## 导航

- 内置导航限制多，官方建议烘焙成 `NavigationRegion2D`
- 烘焙后关掉 TileMapLayer 的 `navigation_enabled`
- 多层 TileMapLayer 不都开导航，2D 导航网格不能叠放

## 图案复用

- `get_pattern` 取一块区域成 `TileMapPattern`
- `set_pattern` 贴到别处，用于房间模板和程序化生成
- `map_pattern` 处理六边形偏移坐标

## 在 .tscn 里预置格子

首选无头脚本：加载场景，`set_cell`，`PackedScene.pack` 后 `ResourceSaver.save` 存回。C# 项目同样用这个 GDScript 脚本：

<!-- check: gdonly -->
```gdscript
extends SceneTree

const SCENE_PATH := "res://level.tscn"

func _initialize() -> void:
	var level := (load(SCENE_PATH) as PackedScene).instantiate()
	var ground := level.get_node("Ground") as TileMapLayer
	ground.clear()
	for x in range(-2, 10):
		ground.set_cell(Vector2i(x, 5), 0, Vector2i(0, 0))
	var packed := PackedScene.new()
	packed.pack(level)
	ResourceSaver.save(packed, SCENE_PATH)
	level.free()
	quit()
```

```bash
timeout 30 godot --headless --path . -s res://tools/paint_level.gd
```

- 4.7.2 实测，存回的场景能读回 12 格，`tile_set` 仍是外部引用
- 脚本在 `_init` 里报错时 `quit()` 不执行，命令前加 `timeout`
- 存回后场景头由 `format=3` 变成 `format=4`，属正常
- `tile_map_data` 变成 base64 字符串
- 场景里的图层节点要先带好 `tile_set`
- 代码新建的 `TileMapLayer` 要设 `owner`，否则 `pack` 不打包它

### 手编 tile_map_data

只用于改几格的小修改。格式 ID 0：

| 位置 | 类型 | 内容 |
|---|---|---|
| 头 2 字节 | uint16 | 格式 ID，必须是 0 |
| 每格 12 字节 | int16 int16 | 格子坐标 x y |
| | uint16 | source_id |
| | uint16 uint16 | 图集坐标 x y |
| | uint16 | alternative_tile |

- 全部小端，总长 2 加 12 乘格数
- 负坐标写补码，-1 是 `255, 255`，-3 是 `253, 255`

```ini
[node name="Ground" type="TileMapLayer" parent="."]
tile_map_data = PackedByteArray(0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 253, 255, 0, 0, 1, 0, 0, 0, 0, 0)
tile_set = ExtResource("1")
```

- 上例 3 格：(0, 2) 和 (1, 2) 用 source 0 的图集坐标 (0, 0)
- (-1, -3) 用图集坐标 (1, 0)
- 头写成 1 或 2 时报 `Unsupported tile map data format: N`，整层 0 格
- 0 格就没有碰撞，角色穿过地面
- 引擎写出的 base64 解码后是同一布局，手编用十进制列表好核对

## 存档

- 遍历 `get_used_cells`
- 记 `get_cell_source_id`、`get_cell_atlas_coords`、`get_cell_alternative_tile`
- 读档用 `set_cell` 还原
- TileSet 删过瓦片后用 `fix_invalid_tiles` 清掉无效格子
