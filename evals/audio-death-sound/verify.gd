extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头
# 用 SFX 总线的实时峰值判断死亡音效是否在响 不依赖具体实现

var _enemy: Node
var _start := 0
var _step := 0


func _initialize() -> void:
	change_scene_to_file("res://main.tscn")


func _process(_delta: float) -> bool:
	if current_scene == null:
		return false
	var now := Time.get_ticks_msec()
	match _step:
		0:
			_enemy = current_scene.find_child("EnemyA", true, false)
			_start = now
			_step = 1
		1:
			if now - _start > 300:
				if _peak() > -50.0:
					print("VERIFY FAIL: 敌人没死时 SFX 总线已经有声音")
				_enemy.call("take_damage", 3)
				_start = now
				_step = 2
		2:
			if now - _start > 120:
				if not _gone():
					print("VERIFY FAIL: 死亡后敌人仍可见或仍参与碰撞")
				_step = 3
		3:
			if now - _start > 250:
				if _peak() < -50.0:
					print("VERIFY FAIL: 死亡后 SFX 总线上听不到死亡音效")
				_step = 4
		4:
			if now - _start > 650:
				if _peak() < -50.0:
					print("VERIFY FAIL: 死亡音效没播完就断了")
				_step = 5
		5:
			if now - _start > 2500:
				if is_instance_valid(_enemy) and _enemy.is_inside_tree():
					print("VERIFY FAIL: 音效播完后敌人节点没有释放")
				quit()
				return true
	return false


func _peak() -> float:
	return AudioServer.get_bus_peak_volume_left_db(AudioServer.get_bus_index(&"SFX"), 0)


func _gone() -> bool:
	if not is_instance_valid(_enemy) or not _enemy.is_inside_tree():
		return true
	var area := _enemy as Area2D
	var sprite := area.get_node_or_null("Sprite") as CanvasItem
	var hidden := not area.visible or (sprite != null and not sprite.visible)
	var shape := area.get_node_or_null("CollisionShape2D") as CollisionShape2D
	var off := shape == null or shape.disabled or area.collision_layer == 0
	off = off or (not area.monitorable and not area.monitoring) or area.process_mode == Node.PROCESS_MODE_DISABLED
	return hidden and off
