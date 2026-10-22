# godot-scene-architecture

## SKILL.md `class_name Bullet`

```gdscript
node.direction = Vector2.DOWN
await frames(30)
expect(node.position.x == 0.0 and absf(node.position.y - 200.0) < 14.0, "每物理帧移动 direction * speed * delta")
```

## SKILL.md `class_name Spawner`

<!-- check: setup -->
```gdscript
node.bullet_scene = make_scene(Bullet.new())
```

```gdscript
node.position = Vector2(100, 50)
node.fire(Vector2.LEFT)
var bullets := root.get_children().filter(func(n: Node) -> bool: return n is Bullet)
expect(bullets.size() == 1, "生成一发子弹")
var bullet := bullets[0] as Bullet
expect(bullet.direction == Vector2.LEFT, "add_child 前设的方向")
expect(bullet.global_position == Vector2(100, 50), "add_child 后设 global_position")
var holder := Node2D.new()
holder.position = Vector2(100, 0)
root.add_child(holder)
var early := Node2D.new()
early.global_position = Vector2(5, 5)
holder.add_child(early)
expect(early.global_position == Vector2(105, 5), "add_child 前设 global_position 当成本地坐标")
holder.queue_free()
bullet.queue_free()
```

## SKILL.md `@export_node_path("Marker2D")`

<!-- check: prepare -->
```gdscript
var script_file := FileAccess.open("res://probe.gd", FileAccess.WRITE)
script_file.store_string("\n".join([
	"extends Node2D",
	"@export var target: Node2D",
	"var seen: Dictionary = {}",
	"func _init() -> void:",
	"\tseen['init'] = target",
	"func _enter_tree() -> void:",
	"\tseen['enter'] = target",
	"func _ready() -> void:",
	"\tseen['ready'] = target",
]) + "\n")
script_file.close()
var scene_file := FileAccess.open("res://probe.tscn", FileAccess.WRITE)
scene_file.store_string("\n".join([
	'[gd_scene load_steps=2 format=3]',
	'[ext_resource type="Script" path="res://probe.gd" id="1"]',
	'[node name="Root" type="Node2D"]',
	'[node name="Probe" type="Node2D" parent="." node_paths=PackedStringArray("target")]',
	'script = ExtResource("1")',
	'target = NodePath("../Other")',
	'[node name="Other" type="Node2D" parent="."]',
]) + "\n")
scene_file.close()
```

<!-- check: setup -->
```gdscript
var marker := Marker2D.new()
marker.name = "Spawn"
node.add_child(marker)
node.spawn_path = ^"Spawn"
```

```gdscript
await frames(2)
expect(node.score is Label and node.score.name == &"ScoreLabel", "%ScoreLabel 取到 Label")
expect(node.sprite is Sprite2D, "$Sprite2D 取到 Sprite2D")
expect(node.spawn == node.get_node("Spawn"), "get_node(spawn_path) 取到 Marker2D")
var other := Node2D.new()
other.position = Vector2(0, 100)
root.add_child(other)
node.target = other
await frames(2)
expect(is_equal_approx(node.rotation, PI / 2.0), "look_at 朝向 target")
node.target = null
other.free()
var inst := (load("res://probe.tscn") as PackedScene).instantiate()
var probe := inst.get_node("Probe")
expect(probe.get("target") == inst.get_node("Other"), "instantiate 返回时 @export 节点已解析")
root.add_child(inst)
var seen: Dictionary = probe.get("seen")
expect(seen["init"] == null, "_init 里 @export 节点是 null")
expect(seen["enter"] == inst.get_node("Other"), "_enter_tree 里 @export 节点可用")
expect(seen["ready"] == inst.get_node("Other"), "_ready 里 @export 节点可用")
inst.queue_free()
```

## SKILL.md `class_name Health`

<!-- check: prepare -->
```gdscript
var script_file := FileAccess.open("res://export_probe.gd", FileAccess.WRITE)
script_file.store_string("\n".join([
	"extends Node",
	"@export var maximum: int = 100",
	"var snapshot: int = maximum",
	"@onready var late: int = maximum",
]) + "\n")
script_file.close()
var scene_file := FileAccess.open("res://export_probe.tscn", FileAccess.WRITE)
scene_file.store_string("\n".join([
	'[gd_scene load_steps=2 format=3]',
	'[ext_resource type="Script" path="res://export_probe.gd" id="1"]',
	'[node name="Probe" type="Node"]',
	'script = ExtResource("1")',
	'maximum = 50',
]) + "\n")
scene_file.close()
```

<!-- check: setup -->
```gdscript
node.maximum = 50
```

```gdscript
expect(node.current == 50, "@onready 初值取到改过的 maximum")
var changes: Array = []
var deaths: Array[int] = [0]
node.changed.connect(func(current: int, maximum: int) -> void: changes.append([current, maximum]))
node.died.connect(func() -> void: deaths[0] += 1)
node.damage(20)
expect(node.current == 30 and changes == [[30, 50]], "changed 带当前值和上限")
expect(deaths[0] == 0, "没扣光不发 died")
node.damage(100)
expect(node.current == 0 and changes.size() == 2 and deaths[0] == 1, "扣光后 current 为 0 且发一次 died")
var probe := (load("res://export_probe.tscn") as PackedScene).instantiate()
root.add_child(probe)
expect(probe.get("snapshot") == 100, "成员初始化器读到脚本默认值")
expect(probe.get("late") == 50, "@onready 读到场景里设的值")
probe.queue_free()
```

## SKILL.md `health.died.connect(queue_free)`

```gdscript
await frames(2)
expect(node.health.maximum == 100, "$Health 取到 Health 子节点")
node.health.damage(30)
expect(not node.is_queued_for_deletion(), "没死不释放")
node.health.damage(100)
expect(node.is_queued_for_deletion(), "died 触发 queue_free")
expect(is_instance_valid(node), "queue_free 后帧末前仍有效")
await frames(2)
expect(not is_instance_valid(node), "帧末释放")
```

## SKILL.md `func raise_alarm`

<!-- check: prepare -->
```gdscript
var script_file := FileAccess.open("res://guard.gd", FileAccess.WRITE)
script_file.store_string("\n".join([
	"extends Node2D",
	"var got := Vector2.INF",
	"func alert(pos: Vector2) -> void:",
	"\tgot = pos",
]) + "\n")
script_file.close()
```

```gdscript
var guard := Node2D.new()
guard.set_script(load("res://guard.gd"))
guard.add_to_group("guards")
root.add_child(guard)
node.position = Vector2(7, 9)
node.raise_alarm()
expect(guard.get("got") == Vector2(7, 9), "call_group 把 global_position 传给 alert")
guard.set("got", Vector2.INF)
call_group_flags(SceneTree.GROUP_CALL_DEFERRED, "guards", "alert", Vector2(1, 1))
expect(guard.get("got") == Vector2.INF, "GROUP_CALL_DEFERRED 当帧不执行")
await frames(2)
expect(guard.get("got") == Vector2(1, 1), "GROUP_CALL_DEFERRED 帧末执行")
var player := Node2D.new()
player.add_to_group("player")
root.add_child(player)
expect(get_first_node_in_group("player") == player, "get_first_node_in_group 取到唯一对象")
player.free()
guard.free()
```

## SKILL.md `class_name HurtBox`

<!-- check: setup -->
```gdscript
var shape := CollisionShape2D.new()
shape.shape = CircleShape2D.new()
node.add_child(shape)
```

```gdscript
await frames(2)
expect(node.health.current == 100, "HurtBox 持有 Health")
var hit := HitBox.new()
hit.damage = 7
var hit_shape := CollisionShape2D.new()
hit_shape.shape = CircleShape2D.new()
hit.add_child(hit_shape)
root.add_child(hit)
await frames(4)
expect(node.health.current == 93, "HitBox 进入后扣 damage")
hit.queue_free()
```

## SKILL.md `class_name HitBox`

```gdscript
expect(node.damage == 1, "damage 默认 1")
node.damage = 5
expect(node.damage == 5, "damage 可改")
```

## SKILL.md `enum State { IDLE, RUN, JUMP }`

<!-- check: setup -->
```gdscript
var shape := CollisionShape2D.new()
shape.shape = CircleShape2D.new()
node.add_child(shape)
var ground := StaticBody2D.new()
ground.position = Vector2(0, 15)
var ground_shape := CollisionShape2D.new()
var rect := RectangleShape2D.new()
rect.size = Vector2(2000, 10)
ground_shape.shape = rect
ground.add_child(ground_shape)
root.add_child(ground)
```

```gdscript
await frames(3)
expect(node.is_on_floor(), "站在地面上")
expect(node.state == node.State.IDLE, "初始 IDLE")
Input.action_press("move_right")
await frames(2)
expect(node.state == node.State.RUN, "有输入进 RUN")
expect(node.velocity.x == 200.0, "RUN 时水平速度为 SPEED")
Input.action_release("move_right")
await frames(2)
expect(node.state == node.State.IDLE, "无输入回 IDLE")
var start_y: float = node.position.y
Input.action_press("jump")
await frames(2)
Input.action_release("jump")
expect(node.state == node.State.JUMP, "按跳跃进 JUMP")
expect(node.position.y < start_y, "起跳后离开地面")
var landed := false
for i in 120:
	await frames(1)
	if node.state == node.State.IDLE:
		landed = true
		break
expect(landed, "落地回 IDLE")
expect(node.is_on_floor(), "落地后在地面上")
```

## SKILL.md `func _unhandled_input`

<!-- check: prepare -->
```gdscript
var script_file := FileAccess.open("res://counter.gd", FileAccess.WRITE)
script_file.store_string("\n".join([
	"extends Node",
	"var proc := 0",
	"var phys := 0",
	"func _process(_delta: float) -> void:",
	"\tproc += 1",
	"func _physics_process(_delta: float) -> void:",
	"\tphys += 1",
]) + "\n")
script_file.close()
```

```gdscript
var counter_script: GDScript = load("res://counter.gd")
var normal := Node.new()
normal.set_script(counter_script)
var always := Node.new()
always.set_script(counter_script)
always.process_mode = Node.PROCESS_MODE_ALWAYS
var when_paused := Node.new()
when_paused.set_script(counter_script)
when_paused.process_mode = Node.PROCESS_MODE_WHEN_PAUSED
var disabled_parent := Node.new()
disabled_parent.process_mode = Node.PROCESS_MODE_DISABLED
var disabled_child := Node.new()
disabled_child.set_script(counter_script)
disabled_parent.add_child(disabled_child)
var no_process := Node.new()
no_process.set_script(counter_script)
for n: Node in [normal, always, when_paused, disabled_parent, no_process]:
	root.add_child(n)
no_process.set_process(false)
await frames(5)
expect(node.process_mode == Node.PROCESS_MODE_ALWAYS and not node.visible, "菜单 ALWAYS 且初始隐藏")
expect(normal.get("proc") > 0 and normal.get("phys") > 0, "未暂停时普通节点运行")
expect(when_paused.get("proc") == 0, "WHEN_PAUSED 未暂停时不处理")
expect(disabled_child.get("proc") == 0 and disabled_child.get("phys") == 0, "DISABLED 关掉整棵子树")
expect(no_process.get("proc") == 0 and no_process.get("phys") > 0, "set_process(false) 只关 _process")

var press := InputEventAction.new()
press.action = &"pause"
press.pressed = true
Input.parse_input_event(press)
await frames(2)
expect(paused and node.visible, "pause 动作暂停并显示菜单")
var normal_proc: int = normal.get("proc")
var normal_phys: int = normal.get("phys")
var always_phys: int = always.get("phys")
var paused_proc: int = when_paused.get("proc")
var timer_fired: Array[bool] = [false, false]
create_timer(0.05).timeout.connect(func() -> void: timer_fired[0] = true)
create_timer(0.05, false).timeout.connect(func() -> void: timer_fired[1] = true)
await frames(15)
expect(normal.get("proc") == normal_proc and normal.get("phys") == normal_phys, "暂停时普通节点停 _process 和 _physics_process")
expect(always.get("phys") > always_phys, "ALWAYS 暂停时照常运行")
expect(when_paused.get("proc") > paused_proc, "WHEN_PAUSED 暂停时运行")
expect(timer_fired[0] and not timer_fired[1], "create_timer 默认暂停时也走，process_always 为 false 时停")

var release := InputEventAction.new()
release.action = &"pause"
release.pressed = true
Input.parse_input_event(release)
await frames(15)
expect(not paused and not node.visible, "再按一次恢复并隐藏菜单")
expect(timer_fired[1], "恢复后受暂停影响的计时器继续走")
normal.queue_free()
always.queue_free()
when_paused.queue_free()
disabled_parent.queue_free()
no_process.queue_free()
```

## references/lifecycle.md `func spawn`

<!-- check: prepare -->
```gdscript
var probe_file := FileAccess.open("res://label_probe.gd", FileAccess.WRITE)
probe_file.store_string("\n".join([
	"extends Node",
	"var label_text := ''",
	"var seen_enter := ''",
	"var seen_ready := ''",
	"func _enter_tree() -> void:",
	"\tseen_enter = label_text",
	"func _ready() -> void:",
	"\tseen_ready = label_text",
]) + "\n")
probe_file.close()
var order_file := FileAccess.open("res://order.gd", FileAccess.WRITE)
order_file.store_string("\n".join([
	"extends Node",
	"func _enter_tree() -> void:",
	"\tEngine.get_meta('events').append('enter ' + name)",
	"func _ready() -> void:",
	"\tEngine.get_meta('events').append('ready ' + name)",
	"func _exit_tree() -> void:",
	"\tEngine.get_meta('events').append('exit ' + name)",
]) + "\n")
order_file.close()
```

<!-- check: setup -->
```gdscript
var scene_root := Node.new()
scene_root.name = "Probe"
scene_root.set_script(load("res://label_probe.gd"))
node.scene = make_scene(scene_root)
```

```gdscript
node.spawn(root, "hello")
var spawned := root.get_child(root.get_child_count() - 1)
expect(spawned.get("seen_enter") == "hello", "add_child 前设的值 _enter_tree 能读到")
expect(spawned.get("seen_ready") == "hello", "add_child 前设的值 _ready 能读到")
var late := node.scene.instantiate()
root.add_child(late)
late.set("label_text", "late")
expect(late.get("seen_ready") == "", "add_child 之后设，_ready 已经跑完")
spawned.queue_free()
late.queue_free()

var events: Array = []
Engine.set_meta("events", events)
var order_script: GDScript = load("res://order.gd")
var a := Node.new()
var b := Node.new()
var c := Node.new()
for pair: Array in [[a, "A"], [b, "B"], [c, "C"]]:
	pair[0].name = pair[1]
	pair[0].set_script(order_script)
a.add_child(b)
a.add_child(c)
root.add_child(a)
expect(events == ["enter A", "enter B", "enter C", "ready B", "ready C", "ready A"], "_enter_tree 父先于子，_ready 子先于父")
events.clear()
b.reparent(c)
expect(events == ["exit B", "enter B"], "reparent 走一次 exit 和 enter，不走 _ready")
events.clear()
a.remove_child(c)
expect(events == ["exit B", "exit C"], "_exit_tree 子先于父")
events.clear()
a.add_child(c)
expect(events == ["enter C", "enter B"], "再次进树不走 _ready")
a.remove_child(c)
c.request_ready()
events.clear()
a.add_child(c)
expect(events == ["enter C", "enter B", "ready C"], "request_ready 只让请求的节点再走 _ready")
a.queue_free()
await frames(2)
Engine.remove_meta("events")
```

## references/lifecycle.md `func build`

```gdscript
var packed := node.build()
var inst := packed.instantiate()
expect(inst.get_child_count() == 1 and inst.get_child(0) is Sprite2D, "设了 owner 的子节点被打包")
expect(inst.get_child(0).owner == inst, "实例化后 owner 是场景根")
inst.free()

var bare_root := Node.new()
bare_root.add_child(Node.new())
var bare := PackedScene.new()
bare.pack(bare_root)
var bare_inst := bare.instantiate()
expect(bare_inst.get_child_count() == 0, "owner 为 null 的子节点不被打包")
bare_inst.free()
bare_root.free()

var deep_root := Node.new()
var mid := Node.new()
mid.add_child(Node.new())
deep_root.add_child(mid)
mid.owner = deep_root
var deep := PackedScene.new()
deep.pack(deep_root)
var deep_inst := deep.instantiate()
expect(deep_inst.get_child_count() == 1 and deep_inst.get_child(0).get_child_count() == 0, "孙节点没设 owner 就丢")
deep_inst.free()
deep_root.free()

var holder := Node.new()
var target := Node.new()
target.name = "Target"
holder.add_child(target)
target.unique_name_in_owner = true
expect(holder.get_node_or_null("%Target") == null, "owner 为 null 时 %Name 查不到")
target.owner = holder
expect(holder.get_node_or_null("%Target") == target, "设了 owner 后 %Name 生效")
var late_holder := Node.new()
var late_target := Node.new()
late_target.name = "Target"
late_holder.add_child(late_target)
late_target.owner = late_holder
late_target.unique_name_in_owner = true
expect(late_holder.get_node_or_null("%Target") == late_target, "先设 owner 再开 unique_name_in_owner 同样生效")
holder.free()
late_holder.free()
var inner_root := Node.new()
var deep_node := Node.new()
deep_node.name = "Deep"
inner_root.add_child(deep_node)
deep_node.owner = inner_root
deep_node.unique_name_in_owner = true
var inner_packed := PackedScene.new()
inner_packed.pack(inner_root)
inner_root.free()
var outer_root := Node.new()
var inner_inst := inner_packed.instantiate()
outer_root.add_child(inner_inst)
inner_inst.owner = outer_root
expect(outer_root.get_node_or_null("%Deep") == null, "%Name 跨实例化子场景取不到")
expect(inner_inst.get_node_or_null("%Deep") != null, "%Name 在子场景自己的 owner 内取得到")
outer_root.free()
var tree_holder := Node.new()
var tree_child := Node.new()
tree_holder.add_child(tree_child)
tree_child.owner = tree_holder
root.add_child(tree_holder)
tree_holder.remove_child(tree_child)
expect(tree_child.owner == null, "树内 remove_child 后 owner 不再是祖先时清成 null")
tree_child.free()
tree_holder.queue_free()
```

## references/lifecycle.md `func _on_body_entered`

<!-- check: prepare -->
```gdscript
var ref_file := FileAccess.open("res://ref_probe.gd", FileAccess.WRITE)
ref_file.store_string("\n".join([
	"extends Node",
	"@export var player: Node",
	"@export var other: Node",
	"@export var targets: Array[Node] = []",
]) + "\n")
ref_file.close()
var wait_file := FileAccess.open("res://waiter.gd", FileAccess.WRITE)
wait_file.store_string("\n".join([
	"extends Node",
	"signal ping",
	"var stage := 0",
	"func wait_ping() -> void:",
	"\tawait ping",
	"\tstage = 1",
	"func wait_other(other: Node) -> void:",
	"\tawait Signal(other, 'ping')",
	"\tstage = 3",
	"func wait_timer() -> void:",
	"\tawait get_tree().create_timer(0.05).timeout",
	"\tstage = 2",
]) + "\n")
wait_file.close()
var scene_a := FileAccess.open("res://refs_ok.tscn", FileAccess.WRITE)
scene_a.store_string("\n".join([
	'[gd_scene load_steps=2 format=3]',
	'[ext_resource type="Script" path="res://ref_probe.gd" id="1"]',
	'[node name="Root" type="Node"]',
	'[node name="Hud" type="Node" parent="." node_paths=PackedStringArray("player", "targets")]',
	'script = ExtResource("1")',
	'player = NodePath("../Player")',
	'targets = [NodePath("../Player"), NodePath("../Enemy")]',
	'[node name="Player" type="Node" parent="."]',
	'[node name="Enemy" type="Node" parent="."]',
]) + "\n")
scene_a.close()
var scene_b := FileAccess.open("res://refs_missing.tscn", FileAccess.WRITE)
scene_b.store_string("\n".join([
	'[gd_scene load_steps=2 format=3]',
	'[ext_resource type="Script" path="res://ref_probe.gd" id="1"]',
	'[node name="Root" type="Node"]',
	'[node name="Hud" type="Node" parent="."]',
	'script = ExtResource("1")',
	'player = NodePath("../Player")',
	'[node name="Player" type="Node" parent="."]',
]) + "\n")
scene_b.close()
var scene_c := FileAccess.open("res://refs_partial.tscn", FileAccess.WRITE)
scene_c.store_string("\n".join([
	'[gd_scene load_steps=2 format=3]',
	'[ext_resource type="Script" path="res://ref_probe.gd" id="1"]',
	'[node name="Root" type="Node"]',
	'[node name="Hud" type="Node" parent="." node_paths=PackedStringArray("player")]',
	'script = ExtResource("1")',
	'player = NodePath("../Player")',
	'other = NodePath("../Player")',
	'[node name="Player" type="Node" parent="."]',
]) + "\n")
scene_c.close()
var hud_root := Node.new()
hud_root.name = "Hud"
hud_root.set_script(load("res://ref_probe.gd"))
var hud_packed := PackedScene.new()
hud_packed.pack(hud_root)
ResourceSaver.save(hud_packed, "res://hud_scene.tscn")
hud_root.free()
var host_ok := FileAccess.open("res://host_ok.tscn", FileAccess.WRITE)
host_ok.store_string("\n".join([
	'[gd_scene load_steps=2 format=3]',
	'[ext_resource type="PackedScene" path="res://hud_scene.tscn" id="1"]',
	'[node name="Host" type="Node"]',
	'[node name="Player" type="Node" parent="."]',
	'[node name="Hud" parent="." node_paths=PackedStringArray("player") instance=ExtResource("1")]',
	'player = NodePath("../Player")',
]) + "\n")
host_ok.close()
var host_missing := FileAccess.open("res://host_missing.tscn", FileAccess.WRITE)
host_missing.store_string("\n".join([
	'[gd_scene load_steps=2 format=3]',
	'[ext_resource type="PackedScene" path="res://hud_scene.tscn" id="1"]',
	'[node name="Host" type="Node"]',
	'[node name="Player" type="Node" parent="."]',
	'[node name="Hud" parent="." instance=ExtResource("1")]',
	'player = NodePath("../Player")',
]) + "\n")
host_missing.close()
```

<!-- check: setup -->
```gdscript
node.position = Vector2(30, 40)
var shape := CollisionShape2D.new()
shape.shape = CircleShape2D.new()
node.add_child(shape)
var drop_root := Node2D.new()
drop_root.name = "Drop"
node.drop_scene = make_scene(drop_root)
```

```gdscript
await frames(2)
var body := CharacterBody2D.new()
body.position = Vector2(30, 40)
var body_shape := CollisionShape2D.new()
body_shape.shape = CircleShape2D.new()
body.add_child(body_shape)
root.add_child(body)
await frames(4)
expect(not node.monitoring, "set_deferred 关掉 monitoring")
var drop := root.get_node_or_null("Drop") as Node2D
expect(drop != null, "call_deferred 把掉落物加进父节点")
expect(drop.global_position == Vector2(30, 40), "set_deferred 设 global_position 在 add_child 之后")
drop.queue_free()
body.queue_free()

var ok_scene := (load("res://refs_ok.tscn") as PackedScene).instantiate()
var ok_hud := ok_scene.get_node("Hud")
expect(ok_hud.get("player") == ok_scene.get_node("Player"), "写了 node_paths 属性有值")
var ok_targets: Array = ok_hud.get("targets")
expect(ok_targets == [ok_scene.get_node("Player"), ok_scene.get_node("Enemy")], "Array[Node] 写了 node_paths 有值")
ok_scene.free()
var missing_scene := (load("res://refs_missing.tscn") as PackedScene).instantiate()
expect(missing_scene.get_node("Hud").get("player") == null, "漏写 node_paths 属性为 null")
missing_scene.free()
var partial_scene := (load("res://refs_partial.tscn") as PackedScene).instantiate()
expect(partial_scene.get_node("Hud").get("player") == partial_scene.get_node("Player"), "node_paths 列出的属性正常")
expect(partial_scene.get_node("Hud").get("other") == null, "node_paths 少列的属性为 null")
partial_scene.free()
var host_ok := (load("res://host_ok.tscn") as PackedScene).instantiate()
expect(host_ok.get_node("Hud").get("player") == host_ok.get_node("Player"), "实例覆盖写了 node_paths 有值")
host_ok.free()
var host_missing := (load("res://host_missing.tscn") as PackedScene).instantiate()
expect(host_missing.get_node("Hud").get("player") == null, "实例覆盖漏写 node_paths 为 null")
host_missing.free()

var victim := Node.new()
root.add_child(victim)
victim.queue_free()
expect(is_instance_valid(victim) and victim.is_queued_for_deletion(), "queue_free 后帧末前有效且标记待删")
await frames(2)
expect(not is_instance_valid(victim), "帧末释放")
var parent := Node.new()
for i in 3:
	parent.add_child(Node.new())
root.add_child(parent)
for child in parent.get_children():
	child.queue_free()
await frames(2)
expect(parent.get_child_count() == 0, "get_children 返回副本，边遍历边释放不跳项")
parent.queue_free()

var waiter_script: GDScript = load("res://waiter.gd")
var moved := Node.new()
moved.set_script(waiter_script)
root.add_child(moved)
moved.wait_ping()
root.remove_child(moved)
moved.ping.emit()
expect(moved.get("stage") == 1, "只是出树，await 恢复")
moved.free()
var doomed := Node.new()
doomed.set_script(waiter_script)
root.add_child(doomed)
doomed.wait_timer()
doomed.free()
var emitter := Node.new()
emitter.set_script(waiter_script)
var hung := Node.new()
hung.set_script(waiter_script)
root.add_child(hung)
hung.wait_other(emitter)
emitter.free()
await frames(10)
expect(hung.get("stage") == 0, "被等待的信号所属对象释放后函数一直挂起")
hung.queue_free()
```

## references/scene-switching.md `func go`

<!-- check: prepare -->
```gdscript
var level_file := FileAccess.open("res://level.gd", FileAccess.WRITE)
level_file.store_string("extends Node\nvar index := 0\n")
level_file.close()
var switcher_file := FileAccess.open("res://switcher.gd", FileAccess.WRITE)
switcher_file.store_string("\n".join([
	"extends Node",
	"var ran_after := false",
	"var in_tree_after := true",
	"func go(path: String) -> void:",
	"\tvar tree := get_tree()",
	"\ttree.change_scene_to_file(path)",
	"\tin_tree_after = is_inside_tree()",
	"\tran_after = true",
]) + "\n")
switcher_file.close()
for scene_name: String in ["SceneA", "SceneB"]:
	var scene_root := Node.new()
	scene_root.name = scene_name
	var packed := PackedScene.new()
	packed.pack(scene_root)
	ResourceSaver.save(packed, "res://%s.tscn" % scene_name.to_lower())
	scene_root.free()
```

<!-- check: setup -->
```gdscript
var level_root := Node.new()
level_root.name = "Level"
level_root.set_script(load("res://level.gd"))
node.next_scene = make_scene(level_root)
```

```gdscript
var old := Node.new()
old.name = "Old"
root.add_child(old)
current_scene = old
node.go(3)
expect(current_scene == null, "调用后 current_scene 为 null")
expect(not old.is_inside_tree(), "旧场景立即出树")
expect(is_instance_valid(old), "旧场景到帧末才释放")
await scene_changed
expect(current_scene.name == &"Level" and current_scene.get("index") == 3, "scene_changed 后拿到带参数的新场景")
expect(not is_instance_valid(old), "旧场景已释放")
expect(node.is_inside_tree(), "切换不影响 autoload 一类的常驻节点")

expect(change_scene_to_file("res://scenea.tscn") == OK, "change_scene_to_file 成功")
expect(current_scene == null, "change_scene_to_file 调用后 current_scene 为 null")
await scene_changed
expect(current_scene.name == &"SceneA", "切到文件里的场景")
var before := current_scene
expect(reload_current_scene() == OK, "reload_current_scene 成功")
await scene_changed
expect(current_scene != before and current_scene.name == &"SceneA", "重开得到新实例")
expect(change_scene_to_packed(load("res://sceneb.tscn")) == OK, "change_scene_to_packed 成功")
await scene_changed
expect(current_scene.name == &"SceneB", "切到 PackedScene")

var leaving := Node.new()
leaving.name = "Leaving"
leaving.set_script(load("res://switcher.gd"))
root.add_child(leaving)
current_scene = leaving
leaving.go("res://scenea.tscn")
expect(leaving.get("ran_after") and not leaving.get("in_tree_after"), "切换调用之后的代码仍运行，但节点已出树")
await scene_changed
expect(current_scene.name == &"SceneA", "切回 SceneA")
```

## references/scene-switching.md `func change_to`

<!-- check: prepare -->
```gdscript
var target_root := Node.new()
target_root.name = "Target"
var packed := PackedScene.new()
packed.pack(target_root)
ResourceSaver.save(packed, "res://target.tscn")
target_root.free()
```

<!-- check: setup -->
```gdscript
(node.get_node("Fade") as ColorRect).modulate = Color(1, 1, 1, 0)
```

```gdscript
node.change_to("res://target.tscn")
await frames(10)
expect(node.fade.modulate.a > 0.0, "淡出进行中")
await node.finished
expect(current_scene != null and current_scene.name == &"Target", "finished 之前已切到目标场景")
expect(is_zero_approx(node.fade.modulate.a), "切换后遮罩淡回透明")
```

## references/scene-switching.md `func open_shop`

<!-- check: prepare -->
```gdscript
var counter_file := FileAccess.open("res://counter.gd", FileAccess.WRITE)
counter_file.store_string("extends Node\nvar proc := 0\nfunc _process(_delta: float) -> void:\n\tproc += 1\n")
counter_file.close()
```

<!-- check: setup -->
```gdscript
var shop_root := Node.new()
shop_root.name = "Shop"
shop_root.process_mode = Node.PROCESS_MODE_WHEN_PAUSED
shop_root.set_script(load("res://counter.gd"))
node.shop_scene = make_scene(shop_root)
```

```gdscript
node.open_shop()
var shop := node.get_node("Shop")
expect(paused, "打开商店后暂停")
var before: int = shop.get("proc")
await frames(5)
expect(shop.get("proc") > before, "WHEN_PAUSED 的商店在暂停时运行")
shop.queue_free()
await frames(2)
expect(not paused, "商店关闭后恢复")
```

## references/state-machine.md `signal transition_requested`

```gdscript
var requested: Array[StringName] = []
node.transition_requested.connect(func(state_name: StringName) -> void: requested.append(state_name))
node.enter()
node.exit()
node.physics_update(0.016)
expect(requested.is_empty(), "基类的虚方法什么都不做")
node.transition_requested.emit(&"Run")
expect(requested == [&"Run"], "transition_requested 带目标状态名")
```

## references/state-machine.md `class_name StateMachine`

<!-- check: prepare -->
```gdscript
var idle_file := FileAccess.open("res://idle.gd", FileAccess.WRITE)
idle_file.store_string("\n".join([
	"extends State",
	"var entered := 0",
	"var exited := 0",
	"var updates := 0",
	"func enter() -> void:",
	"\tentered += 1",
	"func exit() -> void:",
	"\texited += 1",
	"func physics_update(_delta: float) -> void:",
	"\tupdates += 1",
	"\tif Input.get_axis('move_left', 'move_right') != 0.0:",
	"\t\ttransition_requested.emit(&'Run')",
]) + "\n")
idle_file.close()
```

<!-- check: setup -->
```gdscript
node.initial.free()
var idle: State = (load("res://idle.gd") as GDScript).new()
idle.name = "Idle"
var run_state: State = (load("res://s2.gd") as GDScript).new()
run_state.name = "Run"
node.add_child(idle)
node.add_child(run_state)
node.initial = idle
```

```gdscript
await frames(2)
var idle := node.get_node("Idle")
var run_state := node.get_node("Run")
var body := CharacterBody2D.new()
root.add_child(body)
run_state.set("body", body)
expect(node.current == idle and idle.get("entered") == 1, "_ready 进入 initial 并调 enter")
Input.action_press("move_right")
await frames(3)
expect(node.current == run_state, "输入后切到 Run")
expect(idle.get("exited") == 1, "离开时调 exit")
expect(body.velocity.x == 200.0 and body.position.x > 0.0, "Run 推动宿主")
Input.action_release("move_right")
await frames(3)
expect(node.current == idle and idle.get("entered") == 2, "松开输入回 Idle")
idle.transition_requested.emit(&"Nope")
idle.transition_requested.emit(&"Idle")
expect(node.current == idle and idle.get("entered") == 2 and idle.get("exited") == 1, "未知状态名和当前状态都不切换")
var updates: int = idle.get("updates")
paused = true
await frames(5)
expect(idle.get("updates") == updates, "暂停时状态机停止")
paused = false
Input.action_release("move_left")
body.queue_free()
```

## references/state-machine.md `@export var body: CharacterBody2D`

```gdscript
var requested: Array[StringName] = []
node.transition_requested.connect(func(state_name: StringName) -> void: requested.append(state_name))
node.physics_update(0.016)
expect(requested == [&"Idle"], "没有输入请求 Idle")
Input.action_press("move_left")
node.physics_update(0.016)
expect(node.body.velocity.x == -200.0, "按 speed 设横向速度")
expect(node.body.position.x < 0.0, "move_and_slide 推动宿主")
expect(requested.size() == 1, "有输入时不请求切换")
Input.action_release("move_left")
```

## references/state-machine.md `AnimationNodeStateMachinePlayback`

<!-- check: setup -->
```gdscript
var player := AnimationPlayer.new()
player.name = "AnimationPlayer"
var library := AnimationLibrary.new()
for anim_name: StringName in [&"idle", &"run", &"jump"]:
	var anim := Animation.new()
	anim.length = 1.0
	anim.loop_mode = Animation.LOOP_LINEAR
	library.add_animation(anim_name, anim)
player.add_animation_library(&"", library)
node.add_child(player)
var machine := AnimationNodeStateMachine.new()
for anim_name: StringName in [&"idle", &"run", &"jump", &"landed"]:
	var anim_node := AnimationNodeAnimation.new()
	anim_node.animation = &"idle" if anim_name == &"landed" else anim_name
	machine.add_node(anim_name, anim_node)
var start := AnimationNodeStateMachineTransition.new()
start.advance_mode = AnimationNodeStateMachineTransition.ADVANCE_MODE_AUTO
machine.add_transition(&"Start", &"idle", start)
machine.add_transition(&"idle", &"run", AnimationNodeStateMachineTransition.new())
machine.add_transition(&"run", &"idle", AnimationNodeStateMachineTransition.new())
var land := AnimationNodeStateMachineTransition.new()
land.advance_mode = AnimationNodeStateMachineTransition.ADVANCE_MODE_AUTO
land.advance_condition = &"on_floor"
machine.add_transition(&"jump", &"landed", land)
var tree := node.get_node("AnimationTree") as AnimationTree
tree.tree_root = machine
tree.anim_player = NodePath("../AnimationPlayer")
var shape := CollisionShape2D.new()
shape.shape = CircleShape2D.new()
node.add_child(shape)
```

```gdscript
await frames(5)
expect(node.tree.active, "AnimationTree.active 默认 true")
expect(node.playback.get_current_node() == &"jump", "空中 travel 到 jump，没有路径时直接跳过去")
var ground := StaticBody2D.new()
ground.position = Vector2(0, 17)
var ground_shape := CollisionShape2D.new()
var rect := RectangleShape2D.new()
rect.size = Vector2(200, 10)
ground_shape.shape = rect
ground.add_child(ground_shape)
root.add_child(ground)
await frames(2)
node.velocity = Vector2(50, 300)
node.move_and_slide()
await frames(5)
expect(node.playback.get_current_node() == &"run", "地面上有横向速度 travel 到 run")
node.velocity.x = 0.0
await frames(5)
expect(node.playback.get_current_node() == &"idle", "地面上静止 travel 到 idle")
node.set_physics_process(false)
node.playback.start(&"jump")
await frames(2)
expect(node.playback.get_current_node() == &"jump", "start 直接跳到目标状态")
node.tree.set("parameters/conditions/on_floor", true)
await frames(5)
expect(node.playback.get_current_node() == &"landed", "AUTO 转移在 advance_condition 为真时触发")
ground.queue_free()
```
