extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头
# 用 SFX 总线的实时峰值判断吼叫有没有真的混进输出 见 AudioStreamPlayer2D::_update_panning

var _start := 0
var _heard := false


func _initialize() -> void:
	change_scene_to_file("res://main.tscn")


func _process(_delta: float) -> bool:
	if current_scene == null:
		return false
	var now := Time.get_ticks_msec()
	if _start == 0:
		_start = now
	if now - _start < 300:
		return false
	_heard = _heard or AudioServer.get_bus_peak_volume_left_db(AudioServer.get_bus_index(&"SFX"), 0) > -50.0
	if now - _start < 900:
		return false
	if not _heard:
		print("VERIFY FAIL: 从 main.tscn 运行时 SFX 总线上听不到吼叫")
	var growl := current_scene.find_child("Growl", true, false)
	if not growl is AudioStreamPlayer2D:
		print("VERIFY FAIL: Growl 不再是 AudioStreamPlayer2D 失去位置衰减和声像")
	elif not (growl.get_viewport() is SubViewport):
		print("VERIFY FAIL: Growl 被挪出了 SubViewport")
	quit()
	return true
