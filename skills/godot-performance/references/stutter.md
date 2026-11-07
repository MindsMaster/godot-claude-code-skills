# 物理插值与卡顿

物理 tick 与插值的细节、线程加载的注意点、着色器管线编译卡顿的预热办法。

## 物理 tick

- 降 `physics/common/physics_ticks_per_second` 直接减少物理与 `_physics_process` 的 CPU
- 代价是模拟更粗、输入延迟更大，属于降效果
- 官方建议有实时玩家移动的游戏保持 60
- 改 tick 率会改变 `linear_damp` 一类阻尼的手感，要重调
- `physics/common/max_physics_steps_per_frame` 防止卡顿越滚越大
- tick 率高于 60 较多时同步调高步数上限，否则游戏变慢
- 碰撞体用简化形状，区域外的物体移出物理或复用
- 大量射线查询复用 `PhysicsRayQueryParameters2D` 对象

## 物理插值

开启 `physics/common/physics_interpolation` 后，渲染在物理帧之间插值。

| 间接移动 | 设为物理处理 |
|---|---|
| Tween | `set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)` |
| AnimationPlayer | `callback_mode_process` 设 `ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS` |
| 移动父节点 | 父节点的移动也放 `_physics_process()` |

- 两者默认都跟随 idle，在 `_process()` 里移动会抖
- 必须在 `_process()` 里动的节点设 `physics_interpolation_mode` 为 OFF
- 瞬移顺序：先设变换，再 `reset_physics_interpolation()`，反了会拖尾
- 3D 读 `Node3D.get_global_transform_interpolated()` 4.4+
- 2D 没有对应方法，用 `Engine.get_physics_interpolation_fraction()` 自己算
- 新建的 canvas item 摆好后调 `RenderingServer.canvas_item_reset_physics_interpolation()`

## 线程加载

- `use_sub_threads` 为 `true` 加载更快，可能拖慢主线程
- `progress` 数组返回一个元素，0 到 1
- 大场景可在一个线程里实例化，再 `add_child.call_deferred()`
- 多个线程不要同时碰同一个资源
- `@export` 的 `Resource` 随场景一起加载，大引用改存路径
- 直接改共享资源的属性会污染缓存，需要独立副本先 `duplicate()`

## 着色器编译卡顿

| 情况 | 做法 |
|---|---|
| 3D 特效运行中才实例化 | 加载关卡时实例化一次，隐藏或放屏幕外，关掉其脚本 |
| 2D 节点首次绘制 | 在视野内真画一帧，全屏 `ColorRect` 盖住 |
| Compatibility 渲染器 | 加载时每种网格和特效在相机前显示一帧 |
| 渲染特性中途开关 | 反射探针、SDFGI、VoxelGI、TAA、SSAO 尽早出现 |
| MSAA 级别 | 运行中不改，各视口用同一级别 |

- 2D 编译对应 `Performance.PIPELINE_COMPILATIONS_CANVAS`
- `rendering/rendering_device/pipeline_cache/enable` 默认开，二次运行更快
- 模拟首次运行才关管线缓存，并清驱动缓存
- 导出预设的 Shader Baker 4.5+ 缩短首次启动，不解决运行中的编译卡顿
- Shader Baker 默认关闭，只对 Forward+ 与 Mobile 有效
- `--headless` 导出不支持 Shader Baker
