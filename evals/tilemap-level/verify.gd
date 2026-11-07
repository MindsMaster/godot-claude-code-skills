extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头

var _fails := 0


func _fail(msg: String) -> void:
	_fails += 1
	print("VERIFY FAIL: ", msg)


func _initialize() -> void:
	var main: Node = (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	var layers := main.find_children("*", "TileMapLayer", true, false)
	if layers.is_empty():
		_fail("main.tscn 里没有 TileMapLayer")
		quit(1)
		return
	var cells: Dictionary[Vector2i, Vector2i] = {}
	var layer := layers[0] as TileMapLayer
	for n in layers:
		var l := n as TileMapLayer
		for c in l.get_used_cells():
			cells[c] = l.get_cell_atlas_coords(c)
		if l.get_used_cells().size() > layer.get_used_cells().size():
			layer = l
	if cells.size() < 20:
		_fail("预置格子太少 %d" % cells.size())
	var ts := layer.tile_set
	if ts == null or ts.get_physics_layers_count() == 0:
		_fail("TileSet 没有 physics layer")
	elif not _all_tiles_collide(ts):
		_fail("有瓦片没有碰撞形状")
	if ts == null or ts.get_terrain_sets_count() == 0:
		_fail("TileSet 没有 terrain set")
	_check_shapes(cells)
	_check_player(main, layer, cells)
	quit(1 if _fails > 0 else 0)


func _all_tiles_collide(ts: TileSet) -> bool:
	for i in ts.get_source_count():
		var src := ts.get_source(ts.get_source_id(i)) as TileSetAtlasSource
		if src == null:
			continue
		for t in src.get_tiles_count():
			var data := src.get_tile_data(src.get_tile_id(t), 0)
			if data.get_collision_polygons_count(0) == 0:
				return false
	return true


# 每格按上下左右邻居是否有地面推出应有的图集坐标
func _check_shapes(cells: Dictionary[Vector2i, Vector2i]) -> void:
	var wrong := 0
	for c: Vector2i in cells:
		var col := 1
		if not cells.has(c + Vector2i.LEFT):
			col = 0
		elif not cells.has(c + Vector2i.RIGHT):
			col = 2
		var row := 1
		if not cells.has(c + Vector2i.UP):
			row = 0
		elif not cells.has(c + Vector2i.DOWN):
			row = 2
		if cells[c] != Vector2i(col, row):
			wrong += 1
	if wrong > 0:
		_fail("%d 格的边缘或转角与位置不符" % wrong)


func _check_player(main: Node, layer: TileMapLayer, cells: Dictionary[Vector2i, Vector2i]) -> void:
	var player := main.find_child("Player", true, false) as Node2D
	if player == null:
		_fail("找不到 Player")
		return
	var at := layer.local_to_map(layer.to_local(player.global_position))
	for y in range(at.y, at.y + 200):
		if cells.has(Vector2i(at.x, y)):
			if y == at.y:
				_fail("玩家出生在地面格子里")
			return
	_fail("玩家下方没有地面")
