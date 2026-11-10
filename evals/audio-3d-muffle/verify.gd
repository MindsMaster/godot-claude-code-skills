extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头
# 跑 main.tscn 点一次鼠标让玩家开枪 Master 上频谱分析比高低频 不依赖修法写在哪
# 4.7.2 实测 原工程玩家枪声低频 -47.3 到 -47.9 dB 高低频差 -29 dB 不滤波时约 -1 dB
# 同一解法两次实测差 1.5 dB 响度容差取 3 dB 听者挪到玩家身上会响 8 到 11 dB

const BASE_LOW_DB := -47.6
const CLEAR_TILT_DB := -1.0
const AVG := AudioEffectSpectrumAnalyzerInstance.MAGNITUDE_AVERAGE

var _start := 0
var _step := 0
var _spectrum: AudioEffectSpectrumAnalyzerInstance
var _tilt := 0.0
var _low := 0.0
var _count := 0


func _initialize() -> void:
	var analyzer := AudioEffectSpectrumAnalyzer.new()
	analyzer.buffer_length = 0.1
	AudioServer.add_bus_effect(0, analyzer)
	_spectrum = AudioServer.get_bus_effect_instance(0, AudioServer.get_bus_effect_count(0) - 1)
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
			if t > 200:
				var click := InputEventMouseButton.new()
				click.button_index = MOUSE_BUTTON_LEFT
				click.pressed = true
				root.push_input(click)
				_step = 1
		1:
			if t > 350:
				_sample()
			if t > 800:
				var tilt := _tilt / maxi(_count, 1)
				var low := _low / maxi(_count, 1)
				print("VERIFY INFO: 玩家枪声 高低频差 %.1f dB 低频 %.1f dB" % [tilt, low])
				if _count == 0 or low < -80.0:
					print("VERIFY FAIL: 点鼠标后没听到玩家开枪")
				elif tilt < CLEAR_TILT_DB - 6.0:
					print("VERIFY FAIL: 玩家枪声仍发闷 高频比清脆时少 %.1f dB" % (CLEAR_TILT_DB - tilt))
				if _count > 0 and absf(low - BASE_LOW_DB) > 3.0:
					print("VERIFY FAIL: 玩家枪声响度变了 %.1f dB 原来 %.1f dB" % [low, BASE_LOW_DB])
				_reset()
				_step = 2
		2:
			# 敌人计时器 1.5 秒首次开枪
			if t > 1650:
				_sample()
			if t > 2100:
				var tilt := _tilt / maxi(_count, 1)
				print("VERIFY INFO: 远处敌人枪声 高低频差 %.1f dB" % tilt)
				if _count == 0:
					print("VERIFY FAIL: 没听到远处敌人开枪")
				elif tilt > CLEAR_TILT_DB - 6.0:
					print("VERIFY FAIL: 远处敌人枪声不再发闷 高频只少 %.1f dB" % (CLEAR_TILT_DB - tilt))
				quit()
				return true
	return false


func _sample() -> void:
	var high := _spectrum.get_magnitude_for_frequency_range(8000.0, 16000.0, AVG).length()
	var low := _spectrum.get_magnitude_for_frequency_range(100.0, 1000.0, AVG).length()
	if low > 0.0 and high > 0.0:
		_tilt += linear_to_db(high / low)
		_low += linear_to_db(low)
		_count += 1


func _reset() -> void:
	_tilt = 0.0
	_low = 0.0
	_count = 0
