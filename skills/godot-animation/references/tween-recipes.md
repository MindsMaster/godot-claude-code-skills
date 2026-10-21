# Tween 食谱

每个例子都是完整脚本，挂在对应节点上直接用。Tween 不复用，下面每个函数都新建。

## 打断重播

同一属性只留一个 Tween，重播前 `kill()` 旧的：

```gdscript
extends Sprite2D

var _tween: Tween

func squash() -> void:
	if _tween:
		_tween.kill()
	scale = Vector2.ONE
	_tween = create_tween()
	_tween.tween_property(self, "scale", Vector2(1.3, 0.7), 0.06)
	_tween.tween_property(self, "scale", Vector2.ONE, 0.2).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
```

`kill()` 与节点释放都不会发 `finished`，`await tween.finished` 的协程永远不会恢复。需要可靠的收尾，用 `tween_callback()` 放在序列末尾，或给等待加超时。

## 淡出后销毁

```gdscript
extends Node2D

func vanish() -> void:
	var tween := create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.3)
	tween.tween_callback(queue_free)
```

属性路径可以写子分量：`"position:y"` `"modulate:a"` `"scale:x"`。

## 飘字

多个属性并行，再收尾：

```gdscript
extends Label

func pop(amount: int) -> void:
	text = str(amount)
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(self, "position:y", -40.0, 0.6).as_relative().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "modulate:a", 0.0, 0.3).set_delay(0.3)
	tween.chain().tween_callback(queue_free)
```

`set_parallel(true)` 之后所有步骤同时开始，`chain()` 让后一步等前面全部结束。

## 数字滚动

没有现成属性可动时用 `tween_method`：

```gdscript
extends Label

var _shown: int = 0
var _tween: Tween

func set_score(value: int) -> void:
	if _tween:
		_tween.kill()
	_tween = create_tween()
	_tween.tween_method(_show, _shown, value, 0.5)

func _show(value: int) -> void:
	_shown = value
	text = str(value)
```

`tween_method` 的回调参数类型要和 from/to 的类型一致，这里是 int。

## 转场

```gdscript
extends CanvasLayer

@onready var _fade: ColorRect = $Fade

func change_to(path: String) -> void:
	_fade.mouse_filter = Control.MOUSE_FILTER_STOP
	var tween := create_tween()
	tween.tween_property(_fade, "modulate:a", 1.0, 0.3)
	await tween.finished
	get_tree().change_scene_to_file(path)
	var back := create_tween()
	back.tween_property(_fade, "modulate:a", 0.0, 0.3)
	await back.finished
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
```

转场层挂成 Autoload 或常驻 CanvasLayer，Tween 绑定在它上面，场景切换不会中断。淡入淡出期间用 `MOUSE_FILTER_STOP` 挡点击，平时 IGNORE。

## 循环往返

```gdscript
extends Sprite2D

func _ready() -> void:
	var tween := create_tween().set_loops()
	tween.tween_property(self, "position:y", -6.0, 0.8).as_relative().set_trans(Tween.TRANS_SINE)
	tween.tween_property(self, "position:y", 6.0, 0.8).as_relative().set_trans(Tween.TRANS_SINE)
```

无限循环要求每圈有非零时长。节点离树时 Tween 暂停，回树继续。

## Subtween 组合

4.4+。把可复用的片段做成独立 Tween，再拼进主序列。子 Tween 的暂停与处理模式由父 Tween 覆盖，对子 Tween 调 `pause()` 与 `stop()` 或 `set_loops()` 可能让父 Tween 卡在该步骤。

```gdscript
extends Node2D

func _blink() -> Tween:
	var blink := create_tween()
	blink.tween_property(self, "modulate:a", 0.2, 0.05)
	blink.tween_property(self, "modulate:a", 1.0, 0.05)
	return blink

func respawn() -> void:
	var tween := create_tween()
	tween.tween_property(self, "position", Vector2.ZERO, 0.4)
	tween.tween_subtween(_blink())
	tween.tween_subtween(_blink())
```

## 等信号 AwaitTweener

4.7+。序列里等一个信号再继续，目标对象释放时也会继续。`set_timeout()` 给不一定会发的信号兜底。信号必须在 AwaitTweener 开始之后才发出。回调里发信号的情形，把等待和发信号放在同一步：

```gdscript
extends Node2D

signal dialogue_closed

func ask() -> void:
	var tween := create_tween()
	tween.tween_property(self, "position:x", 400.0, 1.0)
	tween.tween_await(dialogue_closed).set_timeout(30.0)
	tween.tween_property(self, "position:x", 0.0, 1.0)

func wait_and_emit() -> void:
	var tween := create_tween()
	tween.tween_await(dialogue_closed)
	tween.parallel().tween_callback(dialogue_closed.emit)
```

## 暂停菜单里的动画

```gdscript
extends Control

func open() -> void:
	modulate.a = 0.0
	var tween := create_tween().set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tween.set_ignore_time_scale(true)
	tween.tween_property(self, "modulate:a", 1.0, 0.15)
```

`TWEEN_PAUSE_PROCESS` 让 Tween 在树暂停时照常处理，默认的 `TWEEN_PAUSE_BOUND` 跟随绑定节点的 `process_mode`。`set_ignore_time_scale(true)` 让它不受 `Engine.time_scale` 影响。

## 手动推进

```gdscript
extends Node2D

var _tween: Tween

func start_manual() -> void:
	_tween = create_tween()
	_tween.pause()
	_tween.tween_property(self, "position:x", 100.0, 1.0)

func tick(delta: float) -> void:
	_tween.custom_step(delta)
```

`custom_step()` 只能前进，返回 false 表示所有步骤已结束。要回到更早的时刻，新建 Tween 再用累计时间一次 `custom_step()`。
