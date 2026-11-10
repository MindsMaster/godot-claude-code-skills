extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头
# 压低按 Music 播放器所在总线的实测电平判 任何机制都算

const MIN_DUCK_DB := 3.0

var _main: Node
var _music: AudioStreamPlayer
var _start := 0
var _frame := 0
var _spoke := false
var _sums := {&"base": [0.0, 0], &"duck": [0.0, 0], &"back": [0.0, 0]}


func _initialize() -> void:
	if AudioServer.bus_count < 4:
		print("VERIFY FAIL: 总线少于 Master 加三类")
	for bus in AudioServer.bus_count:
		var send := AudioServer.get_bus_send(bus)
		if bus > 0 and AudioServer.get_bus_index(send) < 0:
			print("VERIFY FAIL: %s 发送到不存在的总线 %s" % [AudioServer.get_bus_name(bus), send])


# autoload 在 _initialize 时还没就绪 第一帧再实例化
func _process(_delta: float) -> bool:
	_frame += 1
	if _frame == 1:
		_main = (load("res://main.tscn") as PackedScene).instantiate()
		root.add_child(_main)
		return false
	if _frame == 2:
		_check_routing()
		_music = _main.get_node_or_null("Music") as AudioStreamPlayer
		if _music == null:
			print("VERIFY FAIL: 找不到 Music 播放器")
			quit()
			return true
		if not _music.playing:
			_music.play()
		_start = Time.get_ticks_msec()
		return false
	var t := Time.get_ticks_msec() - _start
	# 素材不足一秒 播完就重播 均值按线性幅度算 重播那帧影响很小
	if not _music.playing:
		_music.play()
	var peak := AudioServer.get_bus_peak_volume_left_db(AudioServer.get_bus_index(_music.bus), 0)
	if t >= 300 and t < 600:
		_add(&"base", peak)
	elif t >= 600 and not _spoke:
		_spoke = true
		_main.get_node("Npc").speak(load("res://line.wav"))
	elif t >= 1000 and t < 1400:
		_add(&"duck", peak)
	elif t >= 3500 and t < 4000:
		_add(&"back", peak)
	elif t >= 4000:
		_report()
		quit()
		return true
	return false


func _check_routing() -> void:
	var buses := {}
	for path: String in ["Music", "Player/JumpSound", "Npc/Voice"]:
		var player := _main.get_node_or_null(path) as AudioStreamPlayer
		if player == null:
			continue
		if player.bus == &"Master":
			print("VERIFY FAIL: %s 仍走 Master 滑条管不到" % path)
		buses[player.bus] = true
	if buses.size() < 3 and not buses.is_empty():
		print("VERIFY FAIL: 音乐 音效 语音没有分到三条总线")


func _add(key: StringName, db: float) -> void:
	_sums[key][0] += db_to_linear(db)
	_sums[key][1] += 1


func _avg(key: StringName) -> float:
	var s: Array = _sums[key]
	return linear_to_db(s[0] / maxi(s[1], 1))


func _report() -> void:
	var base := _avg(&"base")
	var duck := _avg(&"duck")
	var back := _avg(&"back")
	if base < -60.0:
		print("VERIFY FAIL: 说话前音乐总线就没有声音 %.1f dB" % base)
		return
	print("VERIFY INFO: 说话前 %.1f 说话时 %.1f 说完 %.1f dB" % [base, duck, back])
	if base - duck < MIN_DUCK_DB:
		print("VERIFY FAIL: NPC 说话时音乐只压低 %.1f dB" % (base - duck))
	if base - back > 2.0:
		print("VERIFY FAIL: 说完 2 秒后音乐还低 %.1f dB 没有恢复" % (base - back))
