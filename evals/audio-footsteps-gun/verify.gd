extends SceneTree
# 由 evals/load_check.py 在运行后的工程里执行 失败行以 VERIFY FAIL 开头


var _main: Node


func _initialize() -> void:
	_main = (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(_main)


# 第一帧才检查 节点此时已进场景树 _ready 已跑过
func _process(_delta: float) -> bool:
	for path: String in ["Player/Step", "Player/Gun"]:
		var player := _main.get_node_or_null(path) as AudioStreamPlayer
		# 节点改名或改由脚本创建时 总线由盲评检查
		if player != null and player.bus != &"SFX":
			print("VERIFY FAIL: %s 走 %s" % [path, player.bus])
	quit()
	return true
