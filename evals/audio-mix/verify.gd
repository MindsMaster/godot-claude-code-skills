extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头
# 压低量公式由 skills/godot-audio 的 4.7.2 实测表验证

const ATTACK_PEAK_DB := -12.0


func _initialize() -> void:
	var sfx := AudioServer.get_bus_index(&"SFX")
	for name: StringName in [&"Weapon", &"MonsterAttack", &"UI"]:
		var bus := AudioServer.get_bus_index(name)
		if bus < 0:
			print("VERIFY FAIL: 没有总线 %s" % name)
		elif AudioServer.get_bus_send(bus) != &"SFX" or bus < sfx:
			print("VERIFY FAIL: %s 没有真正发送到 SFX 序号 %d SFX %d" % [name, bus, sfx])
	if AudioServer.get_bus_index(&"Ambience") < 0:
		print("VERIFY FAIL: 没有总线 Ambience")
	_check_duck(&"Weapon")
	_check_duck(&"Music")
	quit()


func _check_duck(name: StringName) -> void:
	var bus := AudioServer.get_bus_index(name)
	if bus < 0:
		print("VERIFY FAIL: 没有总线 %s" % name)
		return
	for i in AudioServer.get_bus_effect_count(bus):
		var c := AudioServer.get_bus_effect(bus, i) as AudioEffectCompressor
		if c == null or c.sidechain == &"":
			continue
		var key := AudioServer.get_bus_index(c.sidechain)
		if key < 0:
			print("VERIFY FAIL: %s 的侧链总线不存在" % name)
			return
		# 侧链总线序号更大时读到的是乘过它自身音量之后的信号
		var peak := ATTACK_PEAK_DB + (AudioServer.get_bus_volume_db(key) if key > bus else 0.0)
		var duck := 2.08 * maxf(peak - c.threshold, 0.0) * (1.0 - 1.0 / c.ratio)
		if duck < 2.0 or duck > 6.0:
			print("VERIFY FAIL: %s 压低约 %.1f dB 不在 2 到 6 dB" % [name, duck])
		return
	print("VERIFY FAIL: %s 上没有侧链压缩器" % name)
