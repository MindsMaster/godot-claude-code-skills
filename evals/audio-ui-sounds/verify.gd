extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头
# 用 UI 总线的实时峰值判断按钮音是否在响 不依赖具体实现

const QUIET_MS := 700
const LISTEN_MS := 120

var _menu: Control
var _pause: Node
var _start := 0
var _step := 0
var _heard := false
var _label := ""


# 第一帧才加主菜单 此时 autoload 已就绪 与正常启动顺序一致
func _process(_delta: float) -> bool:
	var now := Time.get_ticks_msec()
	if _menu == null:
		_menu = (load("res://main_menu.tscn") as PackedScene).instantiate()
		root.add_child(_menu)
		_start = now
		return false
	if _label != "":
		_heard = _heard or _peak() > -50.0
		if now - _start > LISTEN_MS:
			if not _heard:
				print("VERIFY FAIL: %s 时 UI 总线上没有声音" % _label)
			_label = ""
			_start = now
		return false
	if now - _start < QUIET_MS:
		return false
	match _step:
		0:
			if _peak() > -50.0:
				print("VERIFY FAIL: 没操作按钮时 UI 总线有声音")
			(_menu.get_node("%Options") as Button).pressed.emit()
			_listen("点击主菜单按钮")
		1:
			(_menu.get_node("%Quit") as Button).mouse_entered.emit()
			_listen("鼠标悬停主菜单按钮")
		2:
			(_menu.get_node("%Options") as Button).grab_focus()
			_listen("键盘焦点移到主菜单按钮")
		3:
			var extra := Button.new()
			_menu.get_node("VBox").add_child(extra)
			extra.pressed.emit()
			_listen("点击运行时新加的按钮")
		4:
			_pause = (load("res://pause_menu.tscn") as PackedScene).instantiate()
			root.add_child(_pause)
			paused = true
			_start = now
		5:
			(_pause.get_node("%Settings") as Button).pressed.emit()
			_listen("暂停时点击暂停菜单按钮")
		6:
			quit()
			return true
	_step += 1
	return false


func _listen(label: String) -> void:
	_label = label
	_heard = false
	_start = Time.get_ticks_msec()


func _peak() -> float:
	var bus := AudioServer.get_bus_index(&"UI")
	return AudioServer.get_bus_peak_volume_left_db(bus, 0) if bus >= 0 else -200.0
