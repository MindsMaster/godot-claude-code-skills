extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头
# 只查引擎区域方案的静默失效 见 AudioStreamPlayer3D::_get_overriding_area 与 _calc_reverb_vol


var _main: Node


func _initialize() -> void:
	_main = (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(_main)


# 第一帧才检查 节点此时已进场景树 _ready 已跑过
func _process(_delta: float) -> bool:
	var zone := _main.find_child("CaveZone", true, false) as Area3D
	if zone == null:
		print("VERIFY FAIL: 没有 CaveZone Area3D")
	elif zone.reverb_bus_enabled or zone.audio_bus_override:
		var target: StringName = zone.reverb_bus_name if zone.reverb_bus_enabled else zone.audio_bus_name
		if not _has_reverb(target):
			print("VERIFY FAIL: 总线 %s 上没有混响效果" % target)
		if zone.reverb_bus_enabled and zone.reverb_bus_amount <= 0.0:
			print("VERIFY FAIL: reverb_bus_amount 为 0 混响送出量为 0")
		for n in _main.find_children("*", "AudioStreamPlayer3D", true, false):
			var player := n as AudioStreamPlayer3D
			if player.area_mask & zone.collision_layer == 0:
				print("VERIFY FAIL: %s 的 area_mask 与区域的层不相交 区域对它无效" % player.name)
	quit()
	return true


func _has_reverb(bus_name: StringName) -> bool:
	var bus := AudioServer.get_bus_index(bus_name)
	for i in AudioServer.get_bus_effect_count(bus):
		if AudioServer.get_bus_effect(bus, i) is AudioEffectReverb:
			return true
	return false
