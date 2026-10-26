# 引擎里现成的快路径

脚本里的循环换成一次引擎调用，循环就在 C++ 里跑完。下面列常被手写的批量操作，以及 GDScript 虚拟机里同样逻辑快慢不同的写法。C# 的跨界开销见 godot-csharp 的 [runtime.md](../../godot-csharp/references/runtime.md)。

## 内置替代

| 手写 | 用这个 | 注意 |
|---|---|---|
| 逐点乘变换 | `transform * packed_array`，`Transform2D` 乘 `PackedVector2Array`，`Transform3D` 乘 `PackedVector3Array` | 数组在左是逆变换，只在正交基下等于 `affine_inverse()`。`Basis` 乘数组不支持 |
| 数组里查找、排序、计数 | Packed 数组的 `sort()` `bsearch()` `find()` `has()` `count()` `fill()` `reverse()` `slice()` | `bsearch()` 要先排好序，O(log n)。`has()` `find()` `count()` 仍是 O(n) |
| 逐个字节打包 | `to_byte_array()`、`PackedByteArray.to_float32_array()` 等 | 整块拷贝。字节数不是元素大小的整数倍时返回空数组并报错 |
| 点在多边形内、线段相交、最近点 | `Geometry2D.is_point_in_polygon()` `segment_intersects_segment()` `get_closest_point_to_segment()`、`Geometry3D.ray_intersects_triangle()` | 点在多边形内每次 O(n)，大量点先用包围盒筛 |
| 多边形布尔、扩边、凸包、三角化 | `Geometry2D.merge_polygons()` `clip_polygons()` `offset_polygon()` `convex_hull()` `triangulate_polygon()` | 布尔结果可能是多个多边形，孔洞用 `Geometry2D.is_polygon_clockwise()` 区分。三角化失败返回空数组 |
| 格子 A* | `AStarGrid2D`，空旷地图开 `jumping_enabled` | 改 `region` 后 `update()` 全量重建。开跳点后忽略 `weight_scale`。覆写 `_compute_cost` 等回调时每扩展一个点调一次脚本 |
| 主线程同步寻路卡帧 | 在 `WorkerThreadPool` 任务里调 `NavigationServer3D.query_path()` | 它是同步执行的，线程安全，同一地图并发数受 `navigation/pathfinding/max_threads` 限制。复用参数和结果对象 |
| 循环调用一组节点 | `get_tree().call_group()` | 不需要节点列表时不要 `get_nodes_in_group()`，它每次新建数组。只要数量用 `get_node_count_in_group()` |
| 批量改属性引发一串信号 | `set_block_signals(true)`，改完再打开 | 屏蔽这个对象的全部信号 |
| `set_pixel` 双重循环 | `Image.fill()` `fill_rect()` `blit_rect()` `blend_rect()` `set_data()` | 源和目标格式要相同，压缩格式不支持 |
| 每帧 `set_image()` 刷新贴图 | `ImageTexture.update()` | `set_image()` 每次新建纹理。`update()` 要求尺寸、格式、mipmap 与原来一致 |
| 曲线手算插值 | `Curve.sample_baked()`、`Gradient.sample()` | 见 godot-resources-data |

<!-- check: extends Node2D -->
```gdscript
func world_outline(local_points: PackedVector2Array) -> PackedVector2Array:
	return global_transform * local_points

func joined(names: PackedStringArray) -> String:
	return ", ".join(names)
```

## GDScript 写法快慢

GDScript 编译时知道类型就生成直接调用函数指针的指令，不知道就在运行时查。静态类型的意义主要在这里。

- 调引擎方法走快路径要同时满足：调用对象的类型已知、方法不是可变参数、实参个数等于形参个数、每个实参类型精确匹配。省略默认参数就退回慢路径，`int` 变量传给 `float` 形参也是。热循环里把默认参数写全，类型对齐
- 数学函数用带类型的版本：`lerpf` `clampf` `absf` `minf` `maxf`，整数用 `clampi` `absi` `mini` `maxi`。`lerp` `clamp` `abs` `min` `max` 的形参是 Variant，走通用路径
- 脚本自己声明的成员变量是直接地址访问。继承来的引擎属性如 `position` 每次读写都按属性名沿继承链查找再调用 setter，热循环里先读到局部变量，算完写回一次
- `for i in n` 与 `for i in range(a, b)` 直接写在 for 里不分配数组。先 `var r := range(n)` 再遍历会建一个 Array
- `map()` `filter()` `reduce()` `sort_custom()` 每个元素一次完整的脚本函数调用，不比 for 循环快。写在循环里的 lambda 每次求值都新建 Callable。不带回调的 `sort()` 是纯 C++
- 循环里 `s += x` 拼字符串每次复制整个字符串，是 O(n²)。攒进 `PackedStringArray` 再 `"".join()`，一次分配
- `arr += [x]` 逐元素复制出一个新数组，用 `append()` 或 `append_array()`
- Dictionary 用 `StringName` 作键时哈希是缓存的，`String` 键每次重算。固定的键写成 `&"name"`
- 传无类型 Array 给 `Array[T]` 形参会新建数组并逐个转换，引用也断开了。从源头就用同一种类型
- 每帧 `$A/B` 都按路径逐段查找。用 `@onready` 缓存，或用 `%Name`
- `print` 在调试构建里默认每行刷新标准输出，热路径别留

拿不准时用 [profiling.md](profiling.md) 的手动计时，同一段逻辑两种写法各跑 1000 次比较。
