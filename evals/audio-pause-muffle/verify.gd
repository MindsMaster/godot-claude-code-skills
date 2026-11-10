extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头
# Master 上临时挂频谱分析 比较高频与低频的能量比判断音乐有没有变闷 不依赖具体实现

var _start := 0
var _step := 0
var _spectrum: AudioEffectSpectrumAnalyzerInstance
var _sum := 0.0
var _count := 0
var _normal := 0.0
var _music_mark := 0.0
var _hum_mark := 0.0
var _mark_usec := 0
var _heard := false


func _initialize() -> void:
	var analyzer := AudioEffectSpectrumAnalyzer.new()
	analyzer.buffer_length = 0.1
	AudioServer.add_bus_effect(0, analyzer)
	_spectrum = AudioServer.get_bus_effect_instance(0, AudioServer.get_bus_effect_count(0) - 1)
	change_scene_to_file("res://game.tscn")


func _process(_delta: float) -> bool:
	if current_scene == null:
		return false
	var now := Time.get_ticks_msec()
	if _start == 0:
		_start = now
	var t := now - _start
	var music := current_scene.find_child("Music", true, false) as AudioStreamPlayer
	var hum := current_scene.find_child("Hum", true, false) as AudioStreamPlayer2D
	if music == null or hum == null:
		print("VERIFY FAIL: 找不到 Music 或 Hum 播放器")
		quit()
		return true
	match _step:
		0:
			if t > 300:
				_mute_sfx(true)
				_step = 1
		1:
			if t > 600:
				_sample()
			if t > 1000:
				_normal = _average()
				_mute_sfx(false)
				_step = 2
		2:
			if t > 1300:
				current_scene.find_child("PauseMenu", true, false).call("toggle")
				if not paused:
					print("VERIFY FAIL: PauseMenu.toggle() 之后没有暂停")
				_step = 3
		3:
			if t > 1500:
				_music_mark = music.get_playback_position()
				_hum_mark = hum.get_playback_position()
				_mark_usec = Time.get_ticks_usec()
				_step = 4
		4:
			if t > 2000:
				_sample()
			if t > 2400:
				var seconds := (Time.get_ticks_usec() - _mark_usec) / 1000000.0
				var rate := (music.get_playback_position() - _music_mark) / seconds
				var lost := _normal - _average()
				if not music.playing or rate < 0.8:
					print("VERIFY FAIL: 暂停时音乐没有继续播放 速度 %.2f 倍" % rate)
				elif lost < 6.0:
					print("VERIFY FAIL: 暂停时音乐没有变闷 高频只少了 %.1f dB" % lost)
				if hum.get_playback_position() - _hum_mark > 0.1:
					print("VERIFY FAIL: 暂停时游戏内音效还在播放")
				(current_scene.find_child("Settings", true, false) as Button).pressed.emit()
				_step = 5
		5:
			_heard = _heard or AudioServer.get_bus_peak_volume_left_db(AudioServer.get_bus_index(&"UI"), 0) > -50.0
			if t > 2550:
				if not _heard:
					print("VERIFY FAIL: 暂停时点击暂停菜单按钮 UI 总线上没有声音")
				current_scene.find_child("PauseMenu", true, false).call("toggle")
				_mark_usec = Time.get_ticks_usec()
				_mute_sfx(true)
				_step = 6
		6:
			if t > 3300:
				_sample()
			if t > 3700:
				var still_lost := _normal - _average()
				if still_lost > 3.0:
					print("VERIFY FAIL: 恢复后音乐仍然发闷 高频少了 %.1f dB" % still_lost)
				var resumed := hum.get_playback_position() - _hum_mark
				var seconds := (Time.get_ticks_usec() - _mark_usec) / 1000000.0
				if not hum.playing or resumed < seconds - 0.3 or resumed > seconds + 0.3:
					print("VERIFY FAIL: 恢复后游戏内音效没有从原处接着放 位置差 %.2f 秒 应约 %.2f 秒" % [resumed, seconds])
				quit()
				return true
	return false


func _mute_sfx(mute: bool) -> void:
	AudioServer.set_bus_mute(AudioServer.get_bus_index(&"SFX"), mute)


func _sample() -> void:
	var high := _spectrum.get_magnitude_for_frequency_range(8000.0, 16000.0).length()
	var low := _spectrum.get_magnitude_for_frequency_range(100.0, 1000.0).length()
	if low > 0.0 and high > 0.0:
		_sum += linear_to_db(high / low)
		_count += 1


func _average() -> float:
	var out := _sum / _count if _count > 0 else -100.0
	_sum = 0.0
	_count = 0
	return out
