extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头
# 用播放位置除以真实时间得到实际播放速度 不依赖具体实现

var _start := 0
var _step := 0
var _growl: AudioStreamPlayer2D
var _mark_usec := 0
var _mark := {}


func _initialize() -> void:
	change_scene_to_file("res://main.tscn")


func _process(_delta: float) -> bool:
	if current_scene == null:
		return false
	var now := Time.get_ticks_msec()
	if _start == 0:
		_start = now
	var t := now - _start
	match _step:
		0:
			if t > 300:
				root.get_node("BulletTime").call("enter")
				_step = 1
		1:
			if t > 400:
				var enemy: Node = current_scene.get_node("Spawner").call("spawn", Vector2(50, 0))
				_growl = enemy.get_node("Growl")
				_step = 2
		2:
			if t > 700:
				_take_mark()
				_step = 3
		3:
			if t > 1700:
				_check_rates(Engine.time_scale, "子弹时间里")
				if Engine.time_scale > 0.5:
					print("VERIFY FAIL: enter 之后 Engine.time_scale 没有放慢")
				root.get_node("BulletTime").call("exit")
				_step = 4
		4:
			if t > 2000:
				_take_mark()
				_step = 5
		5:
			if t > 3000:
				_check_rates(1.0, "退出子弹时间后")
				quit()
				return true
	return false


func _players() -> Dictionary:
	return {"音乐": current_scene.get_node_or_null("Music"), "风声": current_scene.get_node_or_null("Wind"), "新生成敌人的吼叫": _growl}


func _take_mark() -> void:
	_mark_usec = Time.get_ticks_usec()
	_mark.clear()
	var players := _players()
	for label: String in players:
		if players[label] != null:
			_mark[label] = players[label].get_playback_position()


func _check_rates(expected: float, when: String) -> void:
	var seconds := (Time.get_ticks_usec() - _mark_usec) / 1000000.0
	var players := _players()
	for label: String in _mark:
		var rate: float = (players[label].get_playback_position() - _mark[label]) / seconds
		if absf(rate - expected) > 0.15:
			print("VERIFY FAIL: %s %s的播放速度是 %.2f 倍 应约 %.2f 倍" % [when, label, rate, expected])
