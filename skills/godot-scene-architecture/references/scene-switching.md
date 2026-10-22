# 场景切换

## 选哪个

| 需求 | 用这个 |
|---|---|
| 整屏换关卡，旧的全部丢弃 | `SceneTree.change_scene_to_file(path)` |
| 已经有 `PackedScene`（预加载过） | `SceneTree.change_scene_to_packed(scene)` |
| 切换前要先建好场景、传参数 | `SceneTree.change_scene_to_node(node)`，4.6+，`node` 不能已在树里 |
| 重开当前关 | `SceneTree.reload_current_scene()` |
| 菜单、对话框、小游戏叠在当前场景上 | `instantiate()` 后 `add_child`，不切换 |
| 要保留旧场景状态再回来 | 自己管：旧场景 `remove_child` 不释放，或叠加方式 |
| 切换要转场动画和加载进度 | 自己写切换器，见下 |

`change_scene_to_file` 内部做 `load` 再实例化，同步阻塞，大场景会卡一帧以上。

## 行为

以下按 4.7 的行为写。

- 调用后旧场景立即从树里移除，`get_tree()` 对旧场景返回 `null`，`current_scene` 为 `null`
- 帧末旧场景释放，新场景加入。同一帧里拿不到新场景
- 要拿新场景：`await get_tree().scene_changed`，4.5+，须在 autoload 这类不会被切走的节点里等，旧场景里的函数随节点释放不会恢复
- 在被切换掉的场景脚本里，调用 `change_scene_to_file` 之后的代码仍会运行，但 `get_tree()` 已经为 `null`。把它放在函数最后一行，或先取 `var tree := get_tree()`
- Autoload 节点不受影响，留在 `/root` 下
- `change_scene_to_node` 之后 `SceneTree` 接管该节点，之后再切换会释放它，别保留引用

4.6+ 用 `change_scene_to_node` 给新场景传参数，切换前就能设好：

```gdscript
extends Node

@export var next_scene: PackedScene

func go(level_index: int) -> void:
	var level := next_scene.instantiate()
	level.set("index", level_index)
	get_tree().change_scene_to_node(level)
```

4.5 及以下参数放在 autoload 的字段里，新场景 `_ready` 里读。

## 自己做切换器

场景切换需要淡入淡出、加载界面时，在 autoload 里做一个切换器，自带一个 `CanvasLayer` 放遮罩。`scene_changed` 是 4.5+，更低版本改成 `await get_tree().process_frame`：

```gdscript
extends CanvasLayer

signal finished

@onready var fade: ColorRect = $Fade

func change_to(path: String) -> void:
	var tween := create_tween()
	tween.tween_property(fade, "modulate:a", 1.0, 0.3)
	await tween.finished
	ResourceLoader.load_threaded_request(path)
	var status := ResourceLoader.load_threaded_get_status(path)
	while status == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
		await get_tree().process_frame
		status = ResourceLoader.load_threaded_get_status(path)
	if status == ResourceLoader.THREAD_LOAD_LOADED:
		get_tree().change_scene_to_packed(ResourceLoader.load_threaded_get(path) as PackedScene)
		await get_tree().scene_changed
	else:
		push_error("场景加载失败 %s" % path)
	tween = create_tween()
	tween.tween_property(fade, "modulate:a", 0.0, 0.3)
	await tween.finished
	finished.emit()
```

- 遮罩 `CanvasLayer` 的 `layer` 设大于 HUD，`process_mode` 设 `PROCESS_MODE_ALWAYS` 让暂停时也能转场
- 带进度条的加载见 godot-resources-data 的带进度的异步加载一节
- 不要手动 `current_scene.free()` 再 `add_child` 新场景再赋值 `current_scene`。`change_scene_to_*` 已经处理了释放时机和 `current_scene`
- 切换前先把 `get_tree().paused` 恢复，暂停状态会带到新场景

## 叠加而非切换

小游戏、设置页、商店这类能回到原界面的，不切换：

```gdscript
extends Node

@export var shop_scene: PackedScene

func open_shop() -> void:
	var shop := shop_scene.instantiate()
	add_child(shop)
	get_tree().paused = true
	shop.tree_exited.connect(_on_shop_closed)

func _on_shop_closed() -> void:
	get_tree().paused = false
```

商店根节点 `process_mode` 设 `WHEN_PAUSED` 或 `ALWAYS`，关闭时 `queue_free`。
