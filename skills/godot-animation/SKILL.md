---
name: godot-animation
description: Godot 4 动画选型与做法，AnimationPlayer AnimationLibrary RESET 方法调用轨道 音频轨道 bezier 轨道，AnimationTree 状态机 BlendSpace OneShot travel advance_expression，Tween create_tween 链式 parallel tween_method kill SubtweenTweener AwaitTweener，AnimatedSprite2D SpriteFrames，Tween 驱动 shader 参数，按帧 seek 与确定性回放，Curve 与 bezier 代替手写插值。在写动画 缓动 角色状态动画 UI 动效 转场 精灵帧动画 时用。animation tween state machine blend sprite frames.
---

# Godot 动画

选对动画节点，用引擎的 Animation 资源和 Tween 代替手写插值器和曲线播放器。不管 shader 本身的写法（见 `godot-shaders-vfx`），不管 UI 控件的血条结构（见 `godot-ui`）。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 一次性动效 弹出 淡入 转场 | Tween | 在 `_process` 里累计时间再 lerp |
| 多属性多轨道编排 带关键帧编辑 | AnimationPlayer 加 Animation 资源 | 手写关键帧数组与播放器 |
| 动画里触发代码 音效 生成特效 | Animation 的方法调用轨道 音频轨道 | 在 `_process` 里按时间判断 |
| 角色状态切换 混合 | AnimationTree 的 StateMachine BlendSpace2D | 一堆 bool 加 `if` 切 `play()` |
| 攻击叠加在移动上 | AnimationNodeOneShot 加骨骼过滤 | 手动停止与恢复 |
| 逐帧精灵动画 | AnimatedSprite2D 加 SpriteFrames，或 Sprite2D 的 `frame` 轨道 | 自己按 FPS 换贴图 |
| 缓动曲线 | `Tween.TRANS_*` 与 `Tween.EASE_*`，Curve 资源，Animation 的 bezier 轨道 | 手写 smoothstep 与弹性函数 |
| 任意起止值的插值 | `Tween.interpolate_value`，`lerp`，`Curve.sample` | 自制 Lerp 工具类 |
| 数字滚动 血量残影 | `tween_method` | 每帧手动逼近 |
| 命中闪白 受击染色 | shader 的 `instance uniform` 加 Tween | `modulate` 超过 1 的取巧值 |
| 镜头相机运动 | Camera2D 的内置平滑与 FastNoiseLite 抖动 | 手写 SmoothDamp |
| 2D 骨骼 | Skeleton2D Bone2D Polygon2D | 手写层级变换 |
| 3D 骨骼看向目标 IK 头发尾巴摆动 | `SkeletonModifier3D` 系列，见 `godot-3d` | 脚本里逐帧改骨骼姿势 |

## 选哪个

| 场景 | 选 |
|---|---|
| 终点运行时才知道 如缩放到某个计算出的值 | Tween |
| 简单的短动效 UI 弹出 受击抖动 | Tween |
| 美术或策划要在编辑器里调关键帧 | AnimationPlayer |
| 要同时驱动多个节点 音频 方法调用 | AnimationPlayer |
| 需要按帧 seek 回放 | AnimationPlayer，见确定性一节 |
| 状态多 要混合 | AnimationPlayer 加 AnimationTree |
| 画面效果随时间变化 溶解 描边 闪白 | shader uniform，由 Tween 或 AnimationPlayer 驱动 |
| 纯逐帧像素动画 | AnimatedSprite2D |

## AnimationPlayer

- 动画存在 AnimationLibrary 里，一个播放器可以挂多个库。默认库名是空字符串，播放时直接写动画名；命名库用 `库名/动画名`，如 `play(&"enemy/attack")`
- 轨道类型：属性（`Animation.TYPE_VALUE`），方法调用（`TYPE_METHOD`），音频（`TYPE_AUDIO`），贝塞尔（`TYPE_BEZIER`），动画播放（`TYPE_ANIMATION`，播放其他 AnimationPlayer 的动画），3D 位置旋转缩放，混合形状
- 方法调用轨道在关键帧上调用目标节点的方法。给判定帧开关命中盒，触发脚步声，生成特效，都放在这里，时间由动画决定
- 音频轨道驱动场景里的 AudioStreamPlayer 节点播放 AudioStream，复音上限由 `audio_max_polyphony` 控制，不用另写音效触发
- 命中盒用属性轨道动画 `CollisionShape2D:disabled` 或 `Area2D:monitoring`，开关时间在动画里直观可见

```gdscript
extends CharacterBody2D

@onready var _anim: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
	_anim.animation_finished.connect(_on_animation_finished)
	_anim.play(&"attack")

func _on_animation_finished(anim_name: StringName) -> void:
	if anim_name == &"attack":
		_anim.play(&"idle")
```

### RESET

动画库里名为 `RESET`（区分大小写）的动画保存默认姿态，每条轨道只有 0 秒一个关键帧。它有两个作用：

- `reset_on_save` 为 true 时，场景保存时以 RESET 的姿态存盘，避免编辑动画后把节点留在动画中间状态存进 `.tscn`
- `deterministic` 为 true 时，混合中缺轨道的动画以 RESET 的值作初始值，没有 RESET 按 0 处理。一个动画改了位置另一个没有，没有 RESET 就会在混合时拉向 `Vector2(0, 0)`。`deterministic` 默认 false，缺轨道的动画不参与该属性的混合

RESET 不用来播放。给属性点关键帧图标时编辑器会提示自动创建。

### 回调与处理模式

在 `AnimationMixer` 上，AnimationPlayer 和 AnimationTree 都有：

| 属性 | 值 | 用途 |
|---|---|---|
| `callback_mode_process` | `ANIMATION_CALLBACK_MODE_PROCESS_IDLE` 默认 | 普通视觉动画 |
| | `ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS` | 动画驱动物理体 命中盒 平台 |
| | `ANIMATION_CALLBACK_MODE_PROCESS_MANUAL` | 自己调 `advance(delta)`，用于确定性回放与暂停时手动推进 |
| `callback_mode_method` | `ANIMATION_CALLBACK_MODE_METHOD_DEFERRED` 默认 | 方法调用延到事件处理后，安全删节点 |
| | `ANIMATION_CALLBACK_MODE_METHOD_IMMEDIATE` | 到点立即调用，需要与同帧逻辑严格排序时用 |

`AnimationPlayer.set_process_callback` 与 `set_method_call_mode` 已弃用，用上面两个属性。

### 播放细节

- 对正在播放的同名动画再调 `play()` 不会重头开始，也不会重置位置。要重播先 `stop()` 或 `seek(0.0, true)`
- `play()` 的效果在下一次处理时才生效，同帧要立即看到用 `advance(0)`
- `animation_finished` 对循环动画不发。循环由 Animation 资源的 `loop_mode` 决定，在编辑器里设，不在运行时改，Animation 是共享资源
- 淡入淡出用 `playback_default_blend_time` 或 `set_blend_time()`，不写手动插值
- 4.4+ 一次播动画的一段用 `play_section()` 或按标记的 `play_section_with_markers()`，播放中改区间用 `set_section()`
- 运行时建 Animation 只用于程序生成的情况，常规动画在编辑器里做

## AnimationTree

AnimationTree 驱动一个 AnimationPlayer 的动画。设 `anim_player`，建 `tree_root`，`active = true`。播放器此时不要再自己 `play()`。

| 节点 | 用途 |
|---|---|
| AnimationNodeStateMachine | 状态与转场，脚本用 `travel()` |
| AnimationNodeBlendSpace1D 2D | 按速度或方向混合 idle walk run |
| AnimationNodeOneShot | 叠加一次性动作，攻击 受击 |
| AnimationNodeTransition | 简化版状态切换，按名字 `transition_request` |
| AnimationNodeBlend2 | 两路按比例混合 |
| AnimationNodeTimeScale TimeSeek | 变速与跳转 |

```gdscript
extends CharacterBody2D

@onready var _tree: AnimationTree = $AnimationTree
@onready var _state: AnimationNodeStateMachinePlayback = _tree["parameters/Locomotion/playback"]

func _physics_process(_delta: float) -> void:
	_tree["parameters/Locomotion/Move/blend_position"] = velocity / 200.0
	if Input.is_action_just_pressed(&"attack"):
		_tree["parameters/Attack/request"] = AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE
	if is_on_floor():
		_state.travel(&"Ground")
```

- 参数路径在 Inspector 的 Parameters 里悬停可见，格式 `parameters/<节点名>/<参数>`。上例的 `tree_root` 是 AnimationNodeBlendTree，内含状态机 Locomotion 与 OneShot 节点 Attack，Move 是状态机里的 BlendSpace2D 状态。状态机直接做 `tree_root` 时路径是 `parameters/playback`，OneShot 要放进 BlendTree 连 `in` 与 `shot`
- 状态机转场的 Advance Mode 为 Auto 时才按条件自动走。Advance Condition 只能判断变量为 true，不能判断取反。需要比较和取反用 Advance Expression，并把 `advance_expression_base_node` 指到持有变量的脚本节点。表达式区分大小写
- `travel()` 沿转场图寻路，没有路径就直接跳。状态机必须已经运行，连了 Start 或调 `start()`
- 转场的 Priority 与 `travel()` 配合，数值小的优先
- 动画节点是共享资源，同一个 `.tres` 的多个实例共享节点，参数却按 AnimationTree 实例分开。运行时不要改节点资源本身，改参数
- 混合行为要确定时开 `deterministic`，缺轨道的动画以 RESET 或 0 作初始值，默认 false
- 详细节点用法与状态机代码见 `references/animation-tree.md`

## Tween

```gdscript
extends Control

var _tween: Tween

func pop() -> void:
	if _tween:
		_tween.kill()
	pivot_offset = size / 2.0
	_tween = create_tween()
	_tween.tween_property(self, "scale", Vector2.ONE * 1.2, 0.08).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_tween.tween_property(self, "scale", Vector2.ONE, 0.12)
```

- 用 `create_tween()` 创建，绑定到节点。节点出树时 Tween 暂停，节点释放时 Tween 自动 kill。`get_tree().create_tween()` 不绑定，不随节点停止，要自己 `kill()`
- 用 `Tween` 的构造函数直接 new 出来的无效。Tween 不复用，每次播放新建，结束后丢弃
- 默认顺序执行。`set_parallel(true)` 让后续全部并行，或在单个步骤前调 `parallel()`，之后用 `chain()` 回到顺序
- 同一个对象的同一个属性不要同时有两个 Tween，后创建的覆盖先创建的。要打断重播，存引用并 `kill()`
- `tween_property(...).from(v)` 指定起点，`.from_current()` 取创建时的值，`.as_relative()` 终点当偏移量
- `tween_method(callable, from, to, duration)` 驱动没有属性的目标：调 setter，数字滚动，shader 参数
- `tween_callback()` 在序列中调函数，`tween_interval()` 做延时，也可以单独当计时器：`await create_tween().tween_interval(2.0).finished`
- `set_loops()` 不带参数是无限循环，必须有非零时长，否则被引擎截断
- 暂停：默认 `Tween.TWEEN_PAUSE_BOUND` 跟随绑定节点的 `process_mode`。暂停菜单里的动画设 `set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)`
- `set_ignore_time_scale(true)` 让慢动作期间的 UI 动画照常走
- 物理节点的位置动画用 `set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)`
- `tween_subtween()` 4.4+ 把另一个 Tween 当一步嵌进来，组合复杂序列
- `tween_await()` 4.7+ 等一个信号再走下一步，做过场和对话，配 `set_timeout()` 兜底：

```gdscript
extends Node2D

signal dialogue_closed

func cutscene() -> void:
	var tween := create_tween()
	tween.tween_property(self, "position:x", 600.0, 1.5)
	tween.tween_callback(print.bind("Hello"))
	tween.tween_await(dialogue_closed).set_timeout(30.0)
	tween.tween_property(self, "position:x", 0.0, 1.5)
```

更多食谱：打断重播，飘字，数字滚动，转场，Subtween，等信号，手动推进，见 `references/tween-recipes.md`。

## AnimatedSprite2D 与 AnimatedSprite3D

- 帧在 SpriteFrames 资源里，下方 SpriteFrames 面板导入图片或切 sprite sheet，每个动画单独设 FPS 与循环
- `play(&"run")`，`speed_scale` 整体变速。`animation_finished` 对循环动画不发，`animation_looped` 才发
- `frame_changed` 信号做脚步声和判定。更复杂的触发改用 Sprite2D 的 `frame` 属性轨道加 AnimationPlayer，这样判定和精灵帧在同一条时间线上
- 对正在播放的同名动画再调 `play()` 不重启，`stop()` 会把 `frame` 归零。SpriteFrames 是共享资源，需要独立改动时 `duplicate()`
- 一个角色既要换帧又要移动骨骼，用 Sprite2D 的 `hframes` `vframes` `frame` 加 AnimationPlayer，不用 AnimatedSprite2D

## 命中闪白

```glsl
shader_type canvas_item;

instance uniform float flash : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	COLOR.rgb = mix(COLOR.rgb, vec3(1.0), flash);
}
```

```gdscript
extends Sprite2D

var _tween: Tween

func hit_flash() -> void:
	if _tween != null:
		_tween.kill()
	set_instance_shader_parameter(&"flash", 1.0)
	_tween = create_tween()
	_tween.tween_property(self, "instance_shader_parameters/flash", 0.0, 0.12)
```

`instance uniform` 每个实例独立，同一材质的敌人不会一起闪。普通 `uniform` 改的是共享材质。3D 网格与 C# 的写法见 `godot-shaders-vfx`。

## 确定性与按帧 seek

锁步联机、回放这类要逐帧复现表现的场景：

- AnimationPlayer 把 `callback_mode_process` 设成 `ANIMATION_CALLBACK_MODE_PROCESS_MANUAL`，每个模拟 tick 调 `advance(delta)`。任意时刻跳转用 `seek(秒, true)`，`update` 为 true 才立即应用。`seek` 不逐个触发中间的方法调用，只调用目标时刻之前最近的一个方法键，`update_only` 为 true 时方法与音频轨道都不处理，到末尾也不发 `animation_finished`，要逐个触发用 `advance`
- Tween 没有 seek，只能前进。`pause()` 之后用 `custom_step(delta)` 手动推进，走完的那次调用仍返回 true，下一次才返回 false，判断结束用 `finished` 信号。回到更早的时刻要重建 Tween 再从零 `custom_step`
- 动画只影响表现。模拟状态不要读 AnimationPlayer 的位置或 Tween 的值，模拟用自己的定点数计时

## 曲线

- 缓动用 `Tween.TRANS_*` 加 `Tween.EASE_*`，不手写缓动函数
- 自定义形状的缓动：做一个 Curve 资源，用 `tween_method` 把 t 从 0 到 1，回调里 `curve.sample(t)`
- 一次性计算插值用 `Tween.interpolate_value(initial, delta, elapsed, duration, trans, ease)`
- AnimationPlayer 里需要曲线时用 bezier 轨道，运行时取值 `Animation.bezier_track_interpolate()`
- 渐变色用 Gradient 资源的 `sample()`

## 外部来源

- 3D 角色动画：导出 glTF，导入后得到带 AnimationPlayer 的场景，在高级导入设置里拆分剪辑与设循环；骨架不同时看 Retargeting
- 2D 骨骼：引擎内置 Skeleton2D 加 Bone2D 加 Polygon2D，动画仍然是 AnimationPlayer
- Aseprite 引擎没有内置导入，先导出 sprite sheet，在 SpriteFrames 面板用 Add frames from a Sprite Sheet 切图，或用社区导入插件
- Spine 引擎没有内置支持，走厂商的 Godot 运行时。引擎文档只在 2D 骨骼一节提到 Spine 是第三方工具，没有导入说明，用之前核对运行时支持的 Godot 版本

## 陷阱

- 手写 Unity 风格的曲线播放器，属于重写 Animation 加 AnimationPlayer，两者能做的更多且有编辑器
- `modulate` 取大于 1 的值做闪白：modulate 是乘法，暗部乘大数仍然偏暗，到不了纯白。换 shader 的 `mix`
- 在 Container 的子节点上 Tween `position`，会被容器重新排版覆盖
- 不绑定节点的 Tween，带 `tween_callback()` 的循环在目标释放后仍留在 SceneTree 里，用 `create_tween()` 绑定，或销毁时 `kill()`
- 同一属性上 AnimationPlayer 与 Tween 同时写，后写的赢，造成抖动
- AnimationTree 激活后又在代码里调 AnimationPlayer 的 `play()`，两边抢轨道
- 方法调用轨道用默认 DEFERRED，调用延到本次处理结束后执行，读到的可能是处理之后的状态
- 动画里的方法调用轨道，目标节点路径写错只在运行时静默失败
- 修改 Animation 或 SpriteFrames 的资源属性会影响所有使用它的实例

## 参考

- `references/animation-tree.md`：AnimationTree 各节点参数路径与状态机、BlendSpace、OneShot 代码
- `references/tween-recipes.md`：Tween 食谱
- [Animation 文档](https://docs.godotengine.org/en/stable/tutorials/animation/index.html)
- [AnimationTree](https://docs.godotengine.org/en/stable/tutorials/animation/animation_tree.html)
- [2D 精灵动画](https://docs.godotengine.org/en/stable/tutorials/2d/2d_sprite_animation.html)
