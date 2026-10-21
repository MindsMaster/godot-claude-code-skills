# 热点的内置解法

SKILL.md 讲了选择，这里是 Server 绕过节点与对象池的完整示例，以及 MultiMesh 的补充细节。

## 用 Server 画 2D 子弹

数千个需要每帧处理的对象，场景树的节点开销成为瓶颈时，绕过节点直接调服务器。

```gdscript
extends Node2D

var _items: Array[RID] = []
var _positions := PackedVector2Array()

func spawn(texture: Texture2D, pos: Vector2) -> void:
	var item := RenderingServer.canvas_item_create()
	var size := texture.get_size()
	RenderingServer.canvas_item_set_parent(item, get_canvas_item())
	RenderingServer.canvas_item_add_texture_rect(item, Rect2(-size * 0.5, size), texture.get_rid())
	RenderingServer.canvas_item_set_transform(item, Transform2D(0.0, pos))
	_items.append(item)
	_positions.append(pos)

func _process(delta: float) -> void:
	for i in _items.size():
		_positions[i] += Vector2(0.0, -300.0) * delta
		RenderingServer.canvas_item_set_transform(_items[i], Transform2D(0.0, _positions[i]))

func _exit_tree() -> void:
	for item in _items:
		RenderingServer.free_rid(item)
```

- 服务器对象用 `RID` 引用，没有引用计数，必须 `free_rid()`，漏掉就是泄漏
- 碰撞用 `PhysicsServer2D.body_create()` 加 `body_add_shape()` 加 `body_set_space()`，`body_set_state()` 设位置。只要进出事件时用 `area_create()` 加 `area_set_monitor_callback()`。官方示例是 Bullet Shower 演示项目，用 body 加一个节点的 `_draw()` 画全部子弹
- 开了物理插值时，新建 canvas item 摆好位置后调 `RenderingServer.canvas_item_reset_physics_interpolation()`，否则出现时有瞬移
- 服务器可在线程里调用。`PhysicsServer2D` 与 `PhysicsServer3D` 要开 `physics/2d/run_on_separate_thread` 或 `physics/3d/run_on_separate_thread`，开启后 API 只能在物理处理期间访问。`RenderingServer` 的 `rendering/driver/threads/thread_model` 默认 Safe
- 状态存进 `PackedVector2Array` 等紧凑数组，不为每个对象建 `RefCounted`
- 先试 MultiMesh 与对象池，它们够用就不要上服务器

### 对象池

```gdscript
extends Node

@export var bullet_scene: PackedScene
var _pool: Array[Node2D] = []

func acquire() -> Node2D:
	var bullet: Node2D
	if _pool.is_empty():
		bullet = bullet_scene.instantiate() as Node2D
	else:
		bullet = _pool.pop_back()
	add_child(bullet)
	return bullet

func release(bullet: Node2D) -> void:
	remove_child(bullet)
	_pool.append(bullet)

func _exit_tree() -> void:
	for bullet in _pool:
		bullet.free()
	_pool.clear()
```

- 池里的节点摘出了场景树，不会随父节点释放，`_exit_tree()` 里手动 `free()`
- 复用时重置速度、计时器、碰撞状态，旧状态残留是对象池常见 bug
- 只隐藏不摘出的话，碰撞仍然生效，回调仍在跑


## MultiMesh 一次写入全部实例

每个实例的数据是紧凑的 float 序列，Transform2D 占 8 个，按行主序 `x.x, y.x, 0, origin.x, x.y, y.y, 0, origin.y`。启用颜色再加 4 个，启用自定义数据再加 4 个。Transform3D 占 12 个。

<!-- check: extends MultiMeshInstance2D -->
```gdscript
func fill(count: int) -> void:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_2D
	mm.mesh = QuadMesh.new()
	mm.instance_count = count
	var data := PackedFloat32Array()
	data.resize(count * 8)
	for i in count:
		var base := i * 8
		data[base] = 1.0
		data[base + 3] = float(i) * 10.0
		data[base + 5] = 1.0
	mm.buffer = data
	multimesh = mm
```

- 数组长度必须等于实例数乘每实例 float 数，不符时打印错误且什么都不画
- 开启物理插值且实例顺序每 tick 会变时，用 `MultiMesh.set_buffer_interpolated()` 同时传当前与上一 tick 的数据。顺序不变时直接设 `buffer` 即可。新摆放的实例调 `MultiMesh.reset_instance_physics_interpolation()`
- 逐个 `set_instance_transform_2d()` 每次一次调用，上千个实例每帧更新时改用 `buffer`
- 位置由 shader 计算的场景（草、鱼群、星空），实例只存起点，时间推进在顶点着色器里，用 `INSTANCE_ID` 与 `INSTANCE_CUSTOM`

## 查找与缓存

<!-- check: extends Node -->
```gdscript
var _boss: Node2D
var _enemies_by_id: Dictionary[int, Node2D] = {}

func _ready() -> void:
	_boss = get_tree().get_first_node_in_group(&"boss") as Node2D

func register(enemy: Node2D, id: int) -> void:
	_enemies_by_id[id] = enemy
	enemy.tree_exited.connect(func() -> void: _enemies_by_id.erase(id))
```

- `get_first_node_in_group()` 在 `_ready()` 里取一次，不在 `_process()` 里每帧找
- 动画或事件按 id 找目标，用 Dictionary 索引，不对每个条目线性扫描全部对象
- 目标会被释放时连 `tree_exited` 清理引用，用之前 `is_instance_valid()`
- `get_nodes_in_group()` 每次返回新数组，每帧遍历前先问是否真的每帧都需要

## 调试信息只在调试构建

<!-- check: extends Node -->
```gdscript
@export var debug_label: Label

func _process(_delta: float) -> void:
	if not OS.is_debug_build() or not debug_label.is_visible_in_tree():
		return
	debug_label.text = "nodes %d" % get_tree().get_node_count()
```

- `OS.is_debug_build()` 在编辑器和调试导出模板里为真，release 模板里为假
- 统计、哈希、字符串格式化只为显示时，放在这个判断后面，面板不可见时也跳过
- 想在 release 里保留调试开关，用 `OS.has_feature("template")` 区分是否导出模板，配合自己的开关
