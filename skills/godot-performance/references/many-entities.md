# 大量同类实体

几百到几千个同类对象（子弹、拾取物、弹孔、群体单位）的组织方式。思路来自 UE 的 Mass 与 tick 合批：同类数据放紧凑数组，一个管理器一次循环处理全部，结构变更攒到帧末一次做。画面和更新频率都不变，省的是逐个调度和逐个查找。

## 选哪一层

| 层 | 适合 | 每个实体的代价 |
|---|---|---|
| 每个实体一个节点 | 要逐个碰撞响应、骨骼动画、复杂脚本，如几十到一两百个怪物 | 一次回调分派、一棵子树的变换传播、一个剔除对象 |
| 管理器 + 紧凑数组 + `MultiMesh` | 静态网格或精灵，几百个以上，逻辑简单统一 | 数组里几个元素，绘制合成一次 |
| 管理器 + `RenderingServer` `PhysicsServer3D` 的 RID | Profiler 证明场景树本身是瓶颈 | 自己管 RID 释放 |

分界数量是经验值，引擎源码和文档没有给数字。`RenderingServer` 类文档原话是场景系统不是瓶颈时直接用服务器不会更快。

## 管理器统一驱动

<!-- check: extends Node -->
```gdscript
var _members: Array[Node2D] = []

func register(member: Node2D) -> void:
	member.set_physics_process(false)
	_members.append(member)
	member.tree_exiting.connect(func() -> void: _members.erase(member))

func _physics_process(delta: float) -> void:
	for member in _members:
		member.position.x += 60.0 * delta
```

- 实体关掉自己的 `_physics_process`，由管理器一个回调遍历。N 次引擎到脚本的分派变成 1 次，C# 里省得更多，每次分派都是一次跨界
- 更新频率不变，每个实体每帧仍然处理一次
- 顺序有要求时用 `process_physics_priority` 排管理器之间的先后，数值小的先跑。引擎只排序不建依赖图，排序结果缓存到优先级改变为止
- 遍历中途可能释放实体时，先把要删的记下，循环结束再删

## 紧凑数组与 swap-remove

<!-- check: extends MultiMeshInstance2D -->
```gdscript
const CAPACITY := 4096
var _positions := PackedVector2Array()
var _velocities := PackedVector2Array()
var _count: int = 0
var _doomed := PackedInt32Array()

func _ready() -> void:
	var quad := QuadMesh.new()
	quad.size = Vector2(4.0, 4.0)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_2D
	mm.mesh = quad
	mm.instance_count = CAPACITY
	mm.visible_instance_count = 0
	multimesh = mm
	_positions.resize(CAPACITY)
	_velocities.resize(CAPACITY)

func spawn(pos: Vector2, vel: Vector2) -> bool:
	if _count == CAPACITY:
		return false
	_positions[_count] = pos
	_velocities[_count] = vel
	_count += 1
	return true

func kill(index: int) -> void:
	_doomed.append(index)

func _physics_process(delta: float) -> void:
	for i in _count:
		_positions[i] += _velocities[i] * delta
		if _positions[i].y < -1000.0:
			kill(i)
	_flush_doomed()
	for i in _count:
		multimesh.set_instance_transform_2d(i, Transform2D(0.0, _positions[i]))
	multimesh.visible_instance_count = _count

func _flush_doomed() -> void:
	_doomed.sort()
	for k in range(_doomed.size() - 1, -1, -1):
		if k + 1 < _doomed.size() and _doomed[k] == _doomed[k + 1]:
			continue
		_count -= 1
		_positions[_doomed[k]] = _positions[_count]
		_velocities[_doomed[k]] = _velocities[_count]
	_doomed.clear()
```

- 删除时把末尾元素搬进空位，O(1)，数组不移动。按下标从大到小删，搬来的元素不会是还没删的
- 下标会变，外部要长期引用某个实体时另存一个 id 到下标的 Dictionary，搬移时同步改
- 一次分配到容量上限，用 `visible_instance_count` 表示活跃数量。改它不重建缓冲，只画前 n 个
- 生成和销毁先进队列，物理循环结束后一次应用。循环里改数组长度会跳过或重复处理元素
- 每帧上千个实例时用 `buffer` 一次写入，见 [hotspots.md](hotspots.md)。设好 `MultiMesh.custom_aabb`，否则每次上传都遍历全部实例重算包围盒

## 空间哈希找邻居

<!-- check: extends Node -->
```gdscript
const CELL := 64.0
var _cells: Dictionary[Vector2i, PackedInt32Array] = {}

func rebuild(positions: PackedVector2Array, count: int) -> void:
	_cells.clear()
	for i in count:
		var key := Vector2i((positions[i] / CELL).floor())
		var bucket: PackedInt32Array = _cells.get(key, PackedInt32Array())
		bucket.append(i)
		_cells[key] = bucket

func query(center: Vector2, radius: float, positions: PackedVector2Array) -> PackedInt32Array:
	var found := PackedInt32Array()
	var lo := Vector2i(((center - Vector2(radius, radius)) / CELL).floor())
	var hi := Vector2i(((center + Vector2(radius, radius)) / CELL).floor())
	var radius_sq := radius * radius
	for y in range(lo.y, hi.y + 1):
		for x in range(lo.x, hi.x + 1):
			var key := Vector2i(x, y)
			if not _cells.has(key):
				continue
			for i in _cells[key]:
				if positions[i].distance_squared_to(center) <= radius_sq:
					found.append(i)
	return found
```

- N 个对象两两比较是 N 乘 N，格子把候选限制在附近几格。格子边长取查询半径左右，一次查询扫 3 乘 3 格
- 每帧整体重建最简单，DetourCrowd 也是这么做的。UE Mass 的网格只在实体跨格时才改登记，实体多且大多静止时用这种
- 比较距离用 `distance_squared_to`，不开方
- 候选设上限：UE Mass 避让最多收 24 个候选取最近 6 个，DetourCrowd 邻居上限 6。上限之外的远处邻居对结果影响很小
- 一次性查询不想维护网格时用 `PhysicsDirectSpaceState2D.intersect_shape`，把 `max_results` 设成需要的数，默认 32。每个结果都建一个 Dictionary
- 大量子弹或拾取物每个挂一个 `Area2D`，物理每步都要维护重叠表和进出事件。只在需要时查询，或用上面的网格

## 对象池的上限与预热

[hotspots.md](hotspots.md) 有基本的池。UE 的 Niagara 组件池多做了三件事：

- 上限：池满时归还的对象直接释放，不让池无限增长
- 预热：关卡加载时先建好常用数量，第一次用时不卡
- 复位：归还时复位缩放、可见性、计时器、速度，组件保持注册只设隐藏。Godot 里对应保持在树里只关回调和碰撞，或者摘出树。摘出树省掉每帧开销，重新 `add_child()` 会再调 `_enter_tree()`，`_ready()` 只在第一次进树时调用，要重跑先 `request_ready()`

粒子特效不必池化节点：同类一次性特效用一个 `GPUParticles3D` 的 `emit_particle()` 在任意位置发射，Compatibility 渲染器不支持。改 `amount` 会重启粒子系统，按强度调数量用 `amount_ratio`。
