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
- 批量改格子后引擎在帧尾统一更新。立刻要读碰撞或导航时调 `update_internals`。

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


func _tile_data_runtime_update(coords: Vector2i, tile_data: TileData) -> void:
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

## 存档

运行时改过的地图存档：遍历 `get_used_cells`，记 `get_cell_source_id`、`get_cell_atlas_coords`、`get_cell_alternative_tile`，读档用 `set_cell` 还原。TileSet 删过瓦片后用 `fix_invalid_tiles` 清掉无效格子。
