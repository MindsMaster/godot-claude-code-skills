# godot-gdscript

## SKILL.md `func take_damage`

<!-- check: prepare -->
```gdscript
var enum_file := FileAccess.open("res://enum_probe.gd", FileAccess.WRITE)
enum_file.store_string("extends RefCounted\nenum State { IDLE, RUN, JUMP }\n")
enum_file.close()
```

```gdscript
expect(node.take_damage(3) == false and node.hp == 7, "没扣光返回 false")
expect(node.take_damage(7) == true and node.hp == 0, "扣光返回 true")
await frames(2)

var typed: Array[int] = [1, 2, 3]
var mapped := typed.map(func(x: int) -> int: return x * 2)
expect(not mapped.is_typed(), "map 返回无类型 Array")
var converted: Array[int] = []
converted.assign(mapped)
expect(converted == [2, 4, 6], "assign 转成类型化数组")
var filtered := typed.filter(func(x: int) -> bool: return x > 1)
expect(filtered.is_typed() and filtered.get_typed_builtin() == TYPE_INT, "filter 保留元素类型")
var nested: Dictionary[String, Dictionary] = {"a": {"b": 1}}
expect(nested["a"]["b"] == 1, "Dictionary[String, Dictionary] 可用")
var nodes: Array[Node] = [Node.new()]
for n: Node in nodes:
	expect(n is Node, "循环变量写类型")
	n.free()
var raw: Dictionary = {"k": 1}
var value: int = raw["k"]
expect(value == 1, "无类型字典取值显式写类型")

var state_enum: Dictionary = (load("res://enum_probe.gd") as GDScript).get_script_constant_map()["State"]
expect(state_enum.keys() == ["IDLE", "RUN", "JUMP"], "keys 给出名字")
expect(state_enum.find_key(1) == "RUN", "find_key 由值找名字")
expect(state_enum["RUN"] == 1, "State[名字] 由名字找值")
```

## SKILL.md `@export_flags_2d_physics var hit_mask: int`

<!-- check: prepare -->
```gdscript
var order_file := FileAccess.open("res://order_probe.gd", FileAccess.WRITE)
order_file.store_string("\n".join([
	"extends Node",
	"var trace: Array[String] = []",
	"var saw_child: Variant = 'unset'",
	"@export var value: int = 1:",
	"\tset(v):",
	"\t\tvalue = v",
	"\t\ttrace.append('setter %d' % v)",
	"\t\tsaw_child = child",
	"@onready var child: Node = $Child",
	"func _init() -> void:",
	"\ttrace.append('init %d' % value)",
	"func _ready() -> void:",
	"\ttrace.append('ready %d' % value)",
]) + "\n")
order_file.close()
var scene_file := FileAccess.open("res://order_probe.tscn", FileAccess.WRITE)
scene_file.store_string("\n".join([
	'[gd_scene load_steps=2 format=3]',
	'[ext_resource type="Script" path="res://order_probe.gd" id="1"]',
	'[node name="Probe" type="Node"]',
	'script = ExtResource("1")',
	'value = 5',
	'[node name="Child" type="Node" parent="."]',
]) + "\n")
scene_file.close()
```

```gdscript
await frames(2)
expect(node.label.text == "200.0", "_ready 里 @onready 变量可用")
expect(not node.timer.is_stopped(), "timer.start() 已调用")
var props: Dictionary = {}
for info: Dictionary in node.get_property_list():
	props[info["name"]] = info
expect(props["ratio"]["hint"] == PROPERTY_HINT_RANGE and props["ratio"]["hint_string"] == "0.0,1.0,0.01", "export_range 提示")
expect(props["mode"]["hint"] == PROPERTY_HINT_ENUM and props["mode"]["hint_string"] == "Idle,Run", "export_enum 提示")
expect(props["next_scene"]["hint"] == PROPERTY_HINT_FILE and props["next_scene"]["hint_string"] == "*.tscn", "export_file 提示")
expect(props["bullet_scene"]["hint"] == PROPERTY_HINT_RESOURCE_TYPE and props["bullet_scene"]["hint_string"] == "PackedScene", "PackedScene 提示")
expect(props["spawn_point"]["hint"] == PROPERTY_HINT_NODE_TYPE and props["spawn_point"]["hint_string"] == "Marker2D", "节点类型提示")
expect(props["hit_mask"]["hint"] == PROPERTY_HINT_LAYERS_2D_PHYSICS, "物理层提示")
expect(props["Loot"]["usage"] & PROPERTY_USAGE_GROUP != 0, "export_group 生成分组条目")
expect(props["speed"]["usage"] & PROPERTY_USAGE_EDITOR != 0 and props["speed"]["type"] == TYPE_FLOAT, "类型来自标注")

var probe := (load("res://order_probe.tscn") as PackedScene).instantiate()
expect(probe.get("trace") == ["init 1", "setter 5"], "先声明初值和 _init，再赋场景里的值")
expect(probe.get("saw_child") == null, "setter 触发时 @onready 变量是 null")
expect(probe.get("value") == 5, "场景里保存的值生效")
root.add_child(probe)
expect(probe.get("trace") == ["init 1", "setter 5", "ready 5"], "_ready 最后")
probe.queue_free()
```

## SKILL.md `damaged.connect(_log_damage.bind("player"))`

<!-- check: prepare -->
```gdscript
var holder_file := FileAccess.open("res://holder.gd", FileAccess.WRITE)
holder_file.store_string("\n".join([
	"extends Node",
	"var hits := 0",
	"func hook(sig: Signal) -> void:",
	"\tsig.connect(func() -> void: hits += 1)",
	"func hook_method(sig: Signal) -> void:",
	"\tsig.connect(on_tick)",
	"func on_tick() -> void:",
	"\thits += 1",
]) + "\n")
holder_file.close()
```

```gdscript
await frames(2)
var got: Array = []
node.damaged.connect(func(amount: int, source: Node) -> void: got.append([amount, source]))
node.button.pressed.emit()
expect(got == [[3, node]], "按钮 pressed 发出 damaged(3, self)")
var bound: Array = []
for info: Dictionary in node.damaged.get_connections():
	var callable: Callable = info["callable"]
	if callable.get_bound_arguments_count() > 0:
		bound = callable.get_bound_arguments()
expect(bound == ["player"], "bind 的参数追加在发射参数之后")
node._log_damage(3, node, "player")
var tail: Array[int] = []
var amounts := func(amount: int) -> void: tail.append(amount)
node.damaged.connect(amounts.unbind(1))
node.damaged.emit(4, node)
expect(tail == [4], "unbind(1) 丢掉末尾 1 个发射参数")
expect(node.damaged.is_connected(amounts.unbind(1)), "is_connected 判断重复连接")

var deferred_seen: Array[int] = []
node.damaged.connect(func(amount: int, _source: Node) -> void: deferred_seen.append(amount), CONNECT_DEFERRED)
node.damaged.emit(9, node)
expect(deferred_seen.is_empty(), "CONNECT_DEFERRED 当帧不执行")
await frames(2)
expect(deferred_seen == [9], "CONNECT_DEFERRED 帧末执行")

var emitter := Node.new()
emitter.add_user_signal("tick")
var lambda_holder := Node.new()
lambda_holder.set_script(load("res://holder.gd"))
lambda_holder.call("hook", Signal(emitter, "tick"))
var method_holder := Node.new()
method_holder.set_script(load("res://holder.gd"))
method_holder.call("hook_method", Signal(emitter, "tick"))
emitter.emit_signal("tick")
expect(lambda_holder.get("hits") == 1 and method_holder.get("hits") == 1, "连接生效")
lambda_holder.free()
method_holder.free()
expect(emitter.get_signal_connection_list("tick").is_empty(), "接收者释放后连接自动断开，lambda 捕获 self 也一样")
emitter.free()

for info: Dictionary in node.damaged.get_connections():
	node.damaged.disconnect(info["callable"])
var loose: Array = []
node.damaged.connect(func(first: Variant, second: Variant) -> void: loose.append([first, second]))
node.damaged.emit("text", 1.5)
expect(loose == [["text", 1.5]], "emit 不检查参数类型")

expect(node.died.is_connected(node.queue_free), "died 连了 queue_free")
node.died.emit()
expect(not node.died.is_connected(node.queue_free), "CONNECT_ONE_SHOT 触发后断开")
expect(node.is_queued_for_deletion(), "died 触发 queue_free")
```

## SKILL.md `var bump := func() -> void:`

```gdscript
var stats: Dictionary = {"count": 0}
var bump := func() -> void:
	stats["count"] += 1
bump.call()
bump.call()
expect(stats["count"] == 2, "捕获字典，改内容可回写")
var number := 0
var snapshot := func() -> int: return number
number = 5
expect(snapshot.call() == 0, "局部变量在创建 lambda 时按值捕获")
var increment := func() -> void:
	@warning_ignore("confusable_capture_reassignment")
	number += 1
increment.call()
increment.call()
expect(number == 5, "lambda 里 += 1 只改副本，外面不变")
```

## SKILL.md `func open_door`

<!-- check: prepare -->
```gdscript
var waiter_file := FileAccess.open("res://waiter.gd", FileAccess.WRITE)
waiter_file.store_string("\n".join([
	"extends Node",
	"var stage := 0",
	"func wait_timer() -> void:",
	"\tawait get_tree().create_timer(0.05).timeout",
	"\tstage = 1",
]) + "\n")
waiter_file.close()
```

```gdscript
var door := Node3D.new()
root.add_child(door)
await node.open_door(door)
expect(not door.visible, "await 之后门隐藏")
var door_nowait := Node3D.new()
root.add_child(door_nowait)
node.open_door(door_nowait)
expect(door_nowait.visible, "不 await 时调用者继续往下")
await frames(70)
expect(not door_nowait.visible, "协程在计时结束后跑完")
var door_freed := Node3D.new()
root.add_child(door_freed)
node.open_door(door_freed)
door_freed.free()
var door_orphan := Node3D.new()
root.add_child(door_orphan)
node.open_door(door_orphan)
root.remove_child(node)
await frames(70)
expect(door_orphan.visible, "自己出树后恢复，被 is_inside_tree 守卫拦下")
root.add_child(node)

create_timer(0.05).timeout.connect(func() -> void: node.answered.emit(2))
var choice: int = await node.ask()
expect(choice == 2, "单参数信号 await 得到该值")
node.add_user_signal("pair", [{"name": "a", "type": TYPE_INT}, {"name": "b", "type": TYPE_INT}])
node.add_user_signal("none")
create_timer(0.02).timeout.connect(func() -> void: node.emit_signal("pair", 1, 2))
var pair: Variant = await Signal(node, "pair")
expect(pair is Array and pair == [1, 2], "多参数信号 await 得到 Array")
create_timer(0.02).timeout.connect(func() -> void: node.emit_signal("none"))
var none: Variant = await Signal(node, "none")
expect(none == null, "无参数信号 await 得到 null")

var doomed := Node.new()
doomed.set_script(load("res://waiter.gd"))
root.add_child(doomed)
doomed.call("wait_timer")
doomed.free()
await frames(10)

var temp := Node.new()
var temp_ref: WeakRef = weakref(temp)
expect(temp_ref.get_ref() == temp, "weakref 取到对象")
temp.free()
expect(temp_ref.get_ref() == null and not is_instance_valid(temp), "释放后 get_ref 为 null，is_instance_valid 为 false")
var queued := Node.new()
root.add_child(queued)
queued.queue_free()
expect(is_instance_valid(queued) and queued.is_queued_for_deletion(), "queue_free 后帧末前有效但标记待删")
await frames(2)
expect(not is_instance_valid(queued), "帧末释放")
```

## SKILL.md `add_child.call_deferred(child)`

```gdscript
expect(node.get_child_count() == 0, "call_deferred 当帧不执行")
expect(node.process_mode == Node.PROCESS_MODE_INHERIT, "set_deferred 当帧不生效")
await frames(2)
expect(node.get_child_count() == 1, "add_child.call_deferred 帧末执行")
expect(node.process_mode == Node.PROCESS_MODE_DISABLED, "set_deferred 帧末生效")
var sorted: Array[int] = [3, 1, 2]
sorted.sort_custom(func(a: int, b: int) -> bool: return a > b)
expect(sorted == [3, 2, 1], "sort_custom 返回 true 表示 a 排在 b 前")
var returned: Variant = node.call_deferred("get_child_count")
expect(returned == null, "call_deferred 返回 null")
var temp := Node.new()
var callable := Callable(temp, "get_name")
expect(callable.is_valid(), "对象存在时 Callable 有效")
temp.free()
expect(not callable.is_valid(), "对象释放后 Callable 无效")
```

## references/annotations.md `@export_category("Main")`

```gdscript
var entries: Dictionary = {}
for info: Dictionary in node.get_property_list():
	entries[info["name"]] = info
expect(entries["Main"]["usage"] & PROPERTY_USAGE_CATEGORY != 0, "export_category 生成分类条目")
expect(entries["Combat"]["usage"] & PROPERTY_USAGE_GROUP != 0 and entries["Combat"]["hint_string"] == "combat_", "export_group 带前缀")
expect(entries["Ranged"]["usage"] & PROPERTY_USAGE_SUBGROUP != 0 and entries["Ranged"]["hint_string"] == "combat_ranged_", "export_subgroup 带前缀")
expect(node.combat_damage == 1 and is_equal_approx(node.combat_ranged_range, 5.0), "导出变量默认值")
var names: Array = entries.keys()
expect(names.find("Combat") < names.find("combat_damage") and names.find("combat_damage") < names.find("Ranged") and names.find("Ranged") < names.find("combat_ranged_range"), "属性顺序跟声明")
```

## references/syntax.md `func describe`

```gdscript
expect(node.describe(node.State.IDLE) == "ground", "IDLE 匹配 ground")
expect(node.describe(node.State.RUN) == "ground", "RUN 与 IDLE 同分支")
expect(node.describe(node.State.JUMP) == "air", "JUMP 匹配 air")
expect(node.classify([1, 2]) == "pair 1 2", "数组结构绑定")
expect(node.classify({"type": "hit", "damage": 7}) == "hit 7", "字典结构绑定")
expect(node.classify({"type": "hit", "damage": 7, "extra": 1}) == "other", "字典模式要求键数相同")
expect(node.classify(11) == "big", "when 守卫为真")
expect(node.classify(5) == "other", "when 守卫为假落到通配")
expect(node.classify("text") == "other", "通配兜底")
var key: StringName = &"run"
var matched := ""
match key:
	"run":
		matched = "string"
	_:
		matched = "none"
expect(matched == "string", "StringName 能匹配 String 常量")
var open_dict := {"type": "hit", "damage": 7, "extra": 1}
var dict_open := false
match open_dict:
	{"type": "hit", "damage": var damage, ..}:
		dict_open = damage == 7
expect(dict_open, "字典模式末尾写 .. 匹配多余的键")
var open_array := [1, 2, 3]
var array_exact := false
var array_open := false
match open_array:
	[1, 2]:
		array_exact = true
	[1, ..]:
		array_open = true
expect(not array_exact and array_open, "数组模式要求长度相同，末尾写 .. 才匹配更长的数组")
```

## references/syntax.md `static func make`

<!-- check: prepare -->
```gdscript
var sub_file := FileAccess.open("res://sub.gd", FileAccess.WRITE)
sub_file.store_string("extends 'res://s1.gd'\n")
sub_file.close()
var init_file := FileAccess.open("res://static_init.gd", FileAccess.WRITE)
init_file.store_string("\n".join([
	"extends RefCounted",
	"static var base: int = 5",
	"static var derived: int = 0",
	"static func _static_init() -> void:",
	"\tderived = base * 2",
]) + "\n")
init_file.close()
```

```gdscript
var hit := Snippet.make(5)
expect(hit.damage == 5 and hit is RefCounted, "内部类默认 RefCounted，_init 收参数")
Snippet.make(6)
expect(Snippet.created == 2, "static var 计数")
var sub: GDScript = load("res://sub.gd")
sub.set("created", 10)
expect(Snippet.created == 10, "子类改静态变量等于改基类同一份")
var init_script: GDScript = load("res://static_init.gd")
expect(init_script.get("derived") == 10, "_static_init 在静态变量初始化完成后调用")
```

## references/syntax.md `signal health_changed`

<!-- check: prepare -->
```gdscript
var probe_file := FileAccess.open("res://setter_probe.gd", FileAccess.WRITE)
probe_file.store_string("\n".join([
	"extends RefCounted",
	"var calls := 0",
	"var stored := 0",
	"var x: int:",
	"\tset = set_x, get = get_x",
	"var y: int = 5:",
	"\tset(value):",
	"\t\tcalls += 1",
	"\t\ty = value",
	"func set_x(value: int) -> void:",
	"\tstored = value * 2",
	"func get_x() -> int:",
	"\treturn stored + 1",
]) + "\n")
probe_file.close()
```

```gdscript
var seen: Array[int] = []
node.health_changed.connect(func(value: int) -> void: seen.append(value))
expect(node.health == 100 and seen.is_empty(), "声明初值不调 setter")
node.health = 500
expect(node.health == 100 and seen == [100], "setter 里 clamp 上限")
node.health = -5
expect(node.health == 0 and seen == [100, 0], "setter 里 clamp 下限")
node.health = 50
expect(is_equal_approx(node.ratio, 0.5), "只写 get 是计算属性")
var probe: RefCounted = (load("res://setter_probe.gd") as GDScript).new()
expect(probe.get("calls") == 0 and probe.get("y") == 5, "声明初值不触发 setter")
probe.set("y", 7)
expect(probe.get("calls") == 1 and probe.get("y") == 7, "类外赋值调 setter，setter 内赋值不递归")
probe.set("x", 3)
expect(probe.get("stored") == 6 and probe.get("x") == 7, "set = 方法, get = 方法")
```

## references/syntax.md `class Boss extends Enemy`

<!-- check: prepare -->
```gdscript
var super_file := FileAccess.open("res://super_probe.gd", FileAccess.WRITE)
super_file.store_string("\n".join([
	"extends Node",
	"class Base extends Node:",
	"\tvar trace: Array[String] = []",
	"\tfunc _init() -> void:",
	"\t\ttrace.append('base init')",
	"\tfunc _ready() -> void:",
	"\t\ttrace.append('base ready')",
	"\tfunc name_of() -> String:",
	"\t\treturn 'base'",
	"class Plain extends Base:",
	"\tfunc _init() -> void:",
	"\t\ttrace.append('plain init')",
	"\tfunc _ready() -> void:",
	"\t\ttrace.append('plain ready')",
	"class Chained extends Base:",
	"\tfunc _init() -> void:",
	"\t\tsuper()",
	"\t\ttrace.append('chained init')",
	"\tfunc _ready() -> void:",
	"\t\tsuper()",
	"\t\ttrace.append('chained ready')",
	"\tfunc name_of() -> String:",
	"\t\treturn super.name_of() + '+chained'",
]) + "\n")
super_file.close()
```

```gdscript
var enemy := Snippet.Enemy.new()
expect(enemy.hp == 10, "默认参数")
var custom := Snippet.Enemy.new(25)
expect(custom.hp == 25, "构造参数")
var boss := Snippet.Boss.new()
expect(boss.hp == 500, "super(500) 传给父类 _init")
root.add_child(enemy)
root.add_child(boss)
await frames(2)
enemy.queue_free()
boss.queue_free()
custom.free()

var probe_script: GDScript = load("res://super_probe.gd")
var holder := Node.new()
holder.set_script(probe_script)
var plain: Node = holder.get_script().get_script_constant_map()["Plain"].new()
var chained: Node = holder.get_script().get_script_constant_map()["Chained"].new()
root.add_child(plain)
root.add_child(chained)
expect(plain.get("trace") == ["plain init", "plain ready"], "子类写了 _init 和 _ready，没写 super 就不调父类")
expect(chained.get("trace") == ["base init", "chained init", "base ready", "chained ready"], "显式 super() 调父类")
expect(chained.call("name_of") == "base+chained", "super.other() 调父类方法")
plain.queue_free()
chained.queue_free()
holder.free()
```

## references/syntax.md `@abstract class Shape:`

```gdscript
expect(is_equal_approx(Snippet.Square.new().area(), 4.0), "子类实现抽象方法")
expect(is_equal_approx(node.total(1.0, 2.5, 3.0), 6.5), "可变参数收成 Array")
expect(is_equal_approx(node.callv("total", [1.0, 2.0]), 3.0), "callv 传数组")
expect(is_equal_approx(node.total(), 0.0), "可变参数可以为空")
```
