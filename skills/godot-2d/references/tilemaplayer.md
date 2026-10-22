# TileMapLayer 与 TileSet

## 结构

- `TileSet` 是资源，放在每个 `TileMapLayer` 的 `tile_set`，多层共用同一个。
- 一个 `TileMapLayer` 节点一层，同一格一层只能放一块。地面、墙、装饰分成多个节点，节点顺序就是绘制顺序。
- `TileMap` 已弃用。旧场景在 TileMap 底部面板右上角工具箱菜单选 Extract TileMap layers as individual TileMapLayer nodes 转换。新代码不再写 `TileMap` 的 `layer` 参数。
- `TileMapLayer` 自 4.3 起可用。4.4 以前的项目升级后再转。

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

- Terrain Set 的 mode 有三种：`TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES`、`TileSet.TERRAIN_MODE_MATCH_CORNERS`、`TileSet.TERRAIN_MODE_MATCH_SIDES`。
- 先在 TileSet 里建好 Physics Layer 才能画碰撞多边形，导航和遮挡同理，顺序不能反。
- 同一块瓦片要不同自定义数据时建 alternative tile，不另开图集。

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

- 空格子的 `get_cell_source_id` 为 -1，`get_cell_tile_data` 返回 null，先判空。
- `local_to_map` 吃局部坐标，世界坐标先 `to_local`。
- `map_to_local` 返回格子中心，不含 `TileData.texture_origin`。
- 取区域：`get_used_cells` 全部、`get_used_cells_by_id` 按源和图集坐标过滤、`get_used_rect` 包围盒。邻格用 `get_surrounding_cells` 或 `get_neighbor_cell`，六边形也正确。
- 批量改格子后引擎在帧尾统一更新。立刻要读碰撞或导航时调 `update_internals`，之后 `move_and_collide` 马上撞得到新格子，`intersect_point` 这类空间查询仍要等下一个物理步。

## 地形自动连接

```gdscript
extends TileMapLayer

const TERRAIN_SET := 0
const TERRAIN_GROUND := 0

func paint_ground(cells: Array[Vector2i]) -> void:
	set_cells_terrain_connect(cells, TERRAIN_SET, TERRAIN_GROUND)
```

- `set_cells_terrain_connect` 把格子设为该地形并与邻格连接，可能改邻格。`set_cells_terrain_path` 按路径顺序连接，适合道路。
- TileSet 没配全所有组合的 peering bits 时结果不对，先查 TileSet。
- 自己按邻格位掩码选瓦片的代码可以删掉。

挖掉或擦掉地形格子时把 terrain 设为 -1，邻格的边缘会跟着重选。

```gdscript
extends TileMapLayer

const TERRAIN_SET := 0

func dig(cell: Vector2i) -> void:
	set_cells_terrain_connect([cell], TERRAIN_SET, -1)
```

- `erase_cell` 只清这一格，邻格仍是旧瓦片。4.7.2 实测，3 格厚 7 格宽的地面挖掉顶行中间一格：`erase_cell` 后两侧的顶边瓦片不变，terrain 设 -1 后两侧换成右上角和左上角，下方一格换成顶边。
- 引擎文档没写 -1，行为以上述实测为准。
- 没有任何瓦片能拼出当前邻接组合时，该格留空。3x3 图集只有 9 宫格，只能铺宽高都不小于 2 格的矩形，一格厚的浮台在 `set_cells_terrain_connect` 之后整条是空的。要一格厚的浮台，图集里得有左端、中段、右端三块单独的瓦片。

## 手写 TileSet 的 terrain

手写 `.tscn` 或 `.tres` 里的 terrain，格式取自 4.7.2 用 `ResourceSaver.save` 存出的 TileSet。

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

- 不写的 peering bit 是 -1，表示这个方向没有地形。
- 方形瓦片的 peering bit 名字、`TileSet.CellNeighbor` 常量与可用的 mode：

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

- 只给瓦片实体连着地面的方向写 bit，朝外的方向不写。每块都写满 8 个 bit，`set_cells_terrain_connect` 只能选出个别瓦片，结果是散乱的空洞。
- mode 为 2 时文件里多写 corner bit，加载不报错，结果与只写 side 相同。mode 为 0 却只写 side，矩形地面也能连对，但转角处没有 corner 约束。
- 3x3 的 9 宫格图集（左上、顶、右上、左、中、右、左下、底、右下），mode 0 下每块要写的 bit：

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

mode 2 只取 side 列，mode 1 只取 corner 列。

- 预置格子仍然按 `tile_map_data` 手编或无头脚本生成，位置对应的瓦片按上表选：顶行用顶行瓦片，最左列用左列，内部用中间块。无头脚本里直接 `set_cells_terrain_connect` 最省事。

## 碰撞

- 碰撞形状按 `physics_quadrant_size` 分块合并，默认 16x16 格一块。
- `TileMapLayer` 作为碰撞体出现在 Area2D 的 `body_entered` 里，参数是 `TileMapLayer`，不是单个格子。
- `KinematicCollision2D.get_collider_rid` 配 `TileMapLayer.get_coords_for_body_rid` 取被撞的格子。默认返回的是块坐标，要精确格子坐标须把 `physics_quadrant_size` 设成 1，代价是关掉形状合并。
- 会动的 TileMapLayer，如移动平台，开 `use_kinematic_bodies`。
- 一块瓦片的碰撞多边形可勾单向，margin 在多边形属性里。
- 关碰撞用 `TileMapLayer.collision_enabled`，不删 TileSet 的 Physics Layer。

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

- `_use_tile_data_runtime_update` 只对需要的格子返回 true，多返回会拖慢整层。
- `tile_data` 的子资源与 TileSet 共享，改碰撞多边形、导航多边形、遮挡前先 `duplicate()`。
- 结果会变时调 `notify_runtime_tile_data_update`，帧尾才更新，且开销大，不要每帧调。
- 破坏地形这类一次性变化直接 `set_cell` 或 `erase_cell` 换瓦片，不走运行时更新。

## 排序与渲染

- 俯视角 Y 排序：`TileMapLayer` 的 `y_sort_enabled` 打开，瓦片按各自 `TileData.y_sort_origin` 加层的 `y_sort_origin` 排，层的 `y_sort_origin` 可用来垫高一层。角色与 TileMapLayer 放在同一个开了 `y_sort_enabled` 的父节点下。
- 打开 Y 排序后 `rendering_quadrant_size` 不再生效，瓦片按 Y 分组。
- `x_draw_order_reversed` 只在 Y 排序打开时有意义。
- 大地图保持默认 `rendering_quadrant_size`。需要逐块 Material 或 Modulate 用 `TileData.material`、`TileData.modulate`，不另开 Sprite2D。

## 导航

- TileSet 里的 Navigation Layer 内置导航限制多，官方建议设计完烘焙成 `NavigationRegion2D` 并关掉 TileMapLayer 的 `navigation_enabled`。
- 2D 导航网格不能叠放在同一张导航地图里，多层 TileMapLayer 不要都开导航。

## 图案复用

`get_pattern` 取一块区域成 `TileMapPattern`，`set_pattern` 贴到别处，房间模板和程序化生成用这个。`map_pattern` 处理六边形偏移坐标。

## 在 .tscn 里预置格子

首选无头脚本生成：加载场景，对 `TileMapLayer` 调 `set_cell`，`PackedScene.pack` 后 `ResourceSaver.save` 存回。引擎自己写 `tile_map_data`，不会错。

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

- 4.7.2 实测，存回的场景能读回 12 格，`tile_set` 仍是外部资源引用
- 脚本在 `_init` 里报错时 `quit()` 不会执行，进程不退出。命令前加 `timeout`
- 存回后场景头由 `format=3` 变成 `format=4`，`tile_map_data` 变成 base64 字符串。这是引擎的正常输出
- 场景里的图层节点要先带好 `tile_set`。代码新建的 `TileMapLayer` 要设 `owner`，否则 `pack` 不打包它

手编 `tile_map_data` 只在改几格的小修改时用。格式 ID 0：

| 位置 | 类型 | 内容 |
|---|---|---|
| 头 2 字节 | uint16 | 格式 ID，必须是 0 |
| 每格 12 字节 | int16 int16 | 格子坐标 x y |
| | uint16 | source_id |
| | uint16 uint16 | 图集坐标 x y |
| | uint16 | alternative_tile |

全部小端，总长 2 加 12 乘格数。负坐标写补码，-1 是 `255, 255`，-3 是 `253, 255`。

```ini
[node name="Ground" type="TileMapLayer" parent="."]
tile_map_data = PackedByteArray(0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 253, 255, 0, 0, 1, 0, 0, 0, 0, 0)
tile_set = ExtResource("1")
```

这段是 3 格：(0, 2) 和 (1, 2) 用 source 0 的图集坐标 (0, 0)，(-1, -3) 用图集坐标 (1, 0)。

- 头写成 1 或 2 时 4.7.2 报 `Unsupported tile map data format: N`，N 是写入的头，整层读成 0 格。没有格子就没有碰撞，角色会穿过地面
- 引擎写出的 base64 形式解码后是同一布局，手编用十进制列表更好核对

## 存档

运行时改过的地图存档：遍历 `get_used_cells`，记 `get_cell_source_id`、`get_cell_atlas_coords`、`get_cell_alternative_tile`，读档用 `set_cell` 还原。TileSet 删过瓦片后用 `fix_invalid_tiles` 清掉无效格子。
