extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头
# 按播放位置判断同曲切场景有没有重头 按 Music 总线峰值判断有没有声音

var _start := 0
var _step := 0
var _before := 0.0


func _initialize() -> void:
	change_scene_to_file("res://title.tscn")


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
				current_scene.call("start_game")
				_step = 1
		1:
			if t > 2000:
				_expect_scene("Level1")
				# 标题曲的淡入还没结束就进了第一关 上一次淡变的收尾不能把新曲停掉
				if _playing().size() != 1 or _peak() < -12.0:
					print("VERIFY FAIL: 上一次淡变没结束就再次换曲后 音乐没有正常播放 在放的播放器 %d 个 Music 峰值 %.1f dB" % [_playing().size(), _peak()])
				_before = _position()
				current_scene.call("finish")
				_step = 2
		2:
			if t > 2600:
				_expect_scene("Level2")
				var after := _position()
				if after < _before + 0.3:
					print("VERIFY FAIL: 同一首曲子切场景后重头放了 位置 %.2f 秒 切之前 %.2f 秒" % [after, _before])
				if _peak() < -20.0:
					print("VERIFY FAIL: 同一首曲子切场景后 Music 总线没有声音")
				current_scene.call("finish")
				_step = 3
		3:
			if t > 2600 + 2200:
				_expect_scene("Boss")
				var playing := _playing()
				if playing.size() != 1:
					print("VERIFY FAIL: 换曲 2.2 秒后有 %d 个播放器在放 应只剩新曲" % playing.size())
				elif playing[0].get_playback_position() > 3.0:
					print("VERIFY FAIL: 换到 boss 场景后仍在放旧曲")
				if _peak() < -12.0:
					print("VERIFY FAIL: 换曲后新曲没有淡入到正常音量 Music 峰值 %.1f dB" % _peak())
				quit()
				return true
	return false


func _expect_scene(scene_name: String) -> void:
	if current_scene.name != scene_name:
		print("VERIFY FAIL: 当前场景是 %s 应为 %s" % [current_scene.name, scene_name])


func _playing() -> Array[AudioStreamPlayer]:
	var out: Array[AudioStreamPlayer] = []
	for n in root.find_children("*", "AudioStreamPlayer", true, false):
		var player := n as AudioStreamPlayer
		if player.playing and not player.stream_paused:
			out.append(player)
	return out


func _position() -> float:
	var best := 0.0
	for player in _playing():
		best = maxf(best, player.get_playback_position())
	return best


func _peak() -> float:
	return AudioServer.get_bus_peak_volume_left_db(AudioServer.get_bus_index(&"Music"), 0)
