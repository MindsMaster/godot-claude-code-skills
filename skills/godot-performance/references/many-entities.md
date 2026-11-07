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

```csharp
public partial class EntityManager : Node
{
    private readonly List<Node2D> _members = new();

    public void Register(Node2D member)
    {
        member.SetPhysicsProcess(false);
        _members.Add(member);
        member.TreeExiting += () => _members.Remove(member);
    }

    public override void _PhysicsProcess(double delta)
    {
        var step = new Vector2(60.0f * (float)delta, 0.0f);
        foreach (Node2D member in _members)
        {
            member.Position += step;
        }
    }
}
```

- 实体关掉自己的 `_physics_process`，由管理器一个回调遍历
- N 次引擎到脚本的分派变成 1 次，C# 省得更多
- 更新频率不变，每个实体每帧仍然处理一次
- 管理器之间的顺序用 `process_physics_priority`，小的先跑
- 引擎只排序不建依赖图
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

```csharp
public partial class Swarm : MultiMeshInstance2D
{
    private const int Capacity = 4096;

    private readonly Vector2[] _positions = new Vector2[Capacity];
    private readonly Vector2[] _velocities = new Vector2[Capacity];
    private readonly List<int> _doomed = new();
    private int _count;

    public override void _Ready()
    {
        Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform2D,
            Mesh = new QuadMesh { Size = new Vector2(4.0f, 4.0f) },
            InstanceCount = Capacity,
            VisibleInstanceCount = 0,
        };
    }

    public bool Spawn(Vector2 pos, Vector2 vel)
    {
        if (_count == Capacity)
        {
            return false;
        }
        _positions[_count] = pos;
        _velocities[_count] = vel;
        _count++;
        return true;
    }

    public void Kill(int index)
    {
        _doomed.Add(index);
    }

    public override void _PhysicsProcess(double delta)
    {
        float dt = (float)delta;
        for (int i = 0; i < _count; i++)
        {
            _positions[i] += _velocities[i] * dt;
            if (_positions[i].Y < -1000.0f)
            {
                Kill(i);
            }
        }
        FlushDoomed();
        for (int i = 0; i < _count; i++)
        {
            Multimesh.SetInstanceTransform2D(i, new Transform2D(0.0f, _positions[i]));
        }
        Multimesh.VisibleInstanceCount = _count;
    }

    private void FlushDoomed()
    {
        _doomed.Sort();
        for (int k = _doomed.Count - 1; k >= 0; k--)
        {
            if (k + 1 < _doomed.Count && _doomed[k] == _doomed[k + 1])
            {
                continue;
            }
            _count--;
            _positions[_doomed[k]] = _positions[_count];
            _velocities[_doomed[k]] = _velocities[_count];
        }
        _doomed.Clear();
    }
}
```

- 删除时把末尾元素搬进空位，O(1)
- 按下标从大到小删，搬来的元素不会是待删的
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

```csharp
public partial class SpatialHash : Node
{
    private const float Cell = 64.0f;

    private readonly Dictionary<Vector2I, List<int>> _cells = new();

    public void Rebuild(Vector2[] positions, int count)
    {
        foreach (List<int> bucket in _cells.Values)
        {
            bucket.Clear();
        }
        for (int i = 0; i < count; i++)
        {
            var key = (Vector2I)(positions[i] / Cell).Floor();
            if (!_cells.TryGetValue(key, out List<int> bucket))
            {
                bucket = new List<int>();
                _cells[key] = bucket;
            }
            bucket.Add(i);
        }
    }

    public void Query(Vector2 center, float radius, Vector2[] positions, List<int> found)
    {
        found.Clear();
        var span = new Vector2(radius, radius);
        var lo = (Vector2I)((center - span) / Cell).Floor();
        var hi = (Vector2I)((center + span) / Cell).Floor();
        float radiusSq = radius * radius;
        for (int y = lo.Y; y <= hi.Y; y++)
        {
            for (int x = lo.X; x <= hi.X; x++)
            {
                if (!_cells.TryGetValue(new Vector2I(x, y), out List<int> bucket))
                {
                    continue;
                }
                foreach (int i in bucket)
                {
                    if (positions[i].DistanceSquaredTo(center) <= radiusSq)
                    {
                        found.Add(i);
                    }
                }
            }
        }
    }
}
```

- 两两比较是 N 乘 N，格子把候选限制在附近几格
- 格子边长取查询半径左右，一次查询扫 3 乘 3 格
- 每帧整体重建最简单，DetourCrowd 也这样做
- 实体多且大多静止时，只在跨格时改登记，UE Mass 这样做
- 比较距离用 `distance_squared_to`，不开方
- 候选设上限：UE Mass 收 24 个取最近 6 个，DetourCrowd 上限 6
- 一次性查询不想维护网格时用 `PhysicsDirectSpaceState2D.intersect_shape`，把 `max_results` 设成需要的数，默认 32。每个结果都建一个 Dictionary
- 每颗子弹挂 `Area2D`，物理每步都维护重叠表与进出事件
- 只在需要时查询，或用上面的网格

## 对象池的上限与预热

[hotspots.md](hotspots.md) 有基本的池。UE 的 Niagara 组件池多做了三件事：

- 上限：池满时归还的对象直接释放，不让池无限增长
- 预热：关卡加载时先建好常用数量，第一次用时不卡
- 复位：归还时复位缩放、可见性、计时器、速度
- 留在树里只关回调和碰撞，或摘出树省掉每帧开销
- 重新 `add_child()` 再调 `_enter_tree()`，`_ready()` 只调一次
- 要重跑 `_ready()` 先 `request_ready()`

粒子特效不必池化节点：同类一次性特效用一个 `GPUParticles3D` 的 `emit_particle()` 在任意位置发射，Compatibility 渲染器不支持。改 `amount` 会重启粒子系统，按强度调数量用 `amount_ratio`。
