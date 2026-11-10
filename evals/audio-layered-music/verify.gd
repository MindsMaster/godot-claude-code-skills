extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头


var _main: Node


func _initialize() -> void:
	_main = (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(_main)


# 第一帧才检查 节点此时已进场景树 _ready 已跑过
func _process(_delta: float) -> bool:
	var players := _main.find_children("*", "AudioStreamPlayer", true, false)
	if _main is AudioStreamPlayer:
		players.append(_main)
	if players.is_empty():
		print("VERIFY FAIL: 场景里没有 AudioStreamPlayer")
	for n in players:
		var player := n as AudioStreamPlayer
		if player.bus != &"Music":
			print("VERIFY FAIL: %s 走 %s" % [player.name, player.bus])
		if not player.autoplay and not player.playing:
			print("VERIFY FAIL: %s 开始时不播放" % player.name)
		_check_loop(player.stream)
	quit()
	return true


func _check_loop(stream: AudioStream) -> void:
	if stream is AudioStreamSynchronized:
		var sync := stream as AudioStreamSynchronized
		for i in sync.stream_count:
			_check_loop(sync.get_sync_stream(i))
	elif stream is AudioStreamWAV:
		if (stream as AudioStreamWAV).loop_mode == AudioStreamWAV.LOOP_DISABLED:
			print("VERIFY FAIL: %s 不循环" % stream.resource_path)
