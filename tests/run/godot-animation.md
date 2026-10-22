# godot-animation

## SKILL.md `func _on_animation_finished`

<!-- check: setup -->
```gdscript
var player := node.get_node("AnimationPlayer") as AnimationPlayer
var library := AnimationLibrary.new()
var attack := Animation.new()
attack.length = 0.2
var attack_track := attack.add_track(Animation.TYPE_VALUE)
attack.track_set_path(attack_track, ^".:position:x")
attack.track_insert_key(attack_track, 0.0, 10.0)
attack.track_insert_key(attack_track, 0.2, 50.0)
var idle := Animation.new()
idle.length = 1.0
idle.loop_mode = Animation.LOOP_LINEAR
var idle_track := idle.add_track(Animation.TYPE_VALUE)
idle.track_set_path(idle_track, ^".:rotation")
idle.track_insert_key(idle_track, 0.0, 0.0)
idle.track_insert_key(idle_track, 1.0, 1.0)
library.add_animation(&"attack", attack)
library.add_animation(&"idle", idle)
player.add_animation_library(&"", library)
```

```gdscript
await frames(2)
var player := node.get_node("AnimationPlayer") as AnimationPlayer
expect(player.current_animation == "attack", "_ready 里开始播 attack")
expect(node.position.x > 10.0, "attack 的属性轨道在驱动 position")
await frames(30)
expect(player.current_animation == "idle", "attack 结束后切到 idle")

var finished: Array[StringName] = []
player.animation_finished.connect(finished.append)
await frames(90)
expect(finished.is_empty(), "循环动画不发 animation_finished")

player.seek(0.4, true)
var before := player.current_animation_position
player.play(&"idle")
expect(is_equal_approx(player.current_animation_position, before), "对同名动画再调 play 不重置位置")
await frames(3)
expect(player.current_animation_position > before, "同名 play 后继续往前走")
player.seek(0.0, true)
expect(is_zero_approx(player.current_animation_position), "seek(0.0, true) 回到开头")

player.play(&"attack")
node.position.x = 0.0
expect(is_zero_approx(node.position.x), "play 之后属性还没应用")
player.advance(0.0)
expect(is_equal_approx(node.position.x, 10.0), "advance(0) 立即应用 play 的首帧")
player.stop()

var host := Node2D.new()
node.add_child(host)
var tester := AnimationPlayer.new()
host.add_child(tester)
tester.root_node = tester.get_path_to(host)
var test_library := AnimationLibrary.new()
var move_a := Animation.new()
move_a.length = 1.0
move_a.loop_mode = Animation.LOOP_LINEAR
var move_track := move_a.add_track(Animation.TYPE_VALUE)
move_a.track_set_path(move_track, ^".:position:x")
move_a.track_insert_key(move_track, 0.0, 100.0)
var fade_b := Animation.new()
fade_b.length = 1.0
fade_b.loop_mode = Animation.LOOP_LINEAR
var fade_track := fade_b.add_track(Animation.TYPE_VALUE)
fade_b.track_set_path(fade_track, ^".:modulate:a")
fade_b.track_insert_key(fade_track, 0.0, 0.5)
test_library.add_animation(&"move_a", move_a)
test_library.add_animation(&"fade_b", fade_b)
tester.add_animation_library(&"", test_library)

tester.play(&"move_a")
tester.advance(0.1)
tester.play(&"fade_b", 0.5)
tester.advance(1.0)
expect(is_equal_approx(host.position.x, 100.0), "deterministic 为 false 时缺轨道的动画不参与混合")
tester.deterministic = true
tester.play(&"move_a")
tester.advance(0.1)
tester.play(&"fade_b", 0.5)
tester.advance(1.0)
expect(absf(host.position.x) < 0.1, "deterministic 为 true 且没有 RESET 时拉向 0")
var reset := Animation.new()
reset.length = 0.01
var reset_track := reset.add_track(Animation.TYPE_VALUE)
reset.track_set_path(reset_track, ^".:position:x")
reset.track_insert_key(reset_track, 0.0, 5.0)
test_library.add_animation(&"RESET", reset)
tester.stop()
tester.play(&"move_a")
tester.advance(0.1)
tester.play(&"fade_b", 0.5)
tester.advance(1.0)
expect(absf(host.position.x - 5.0) < 0.1, "deterministic 为 true 时以 RESET 的值作初始值")
host.queue_free()

var sprite := AnimatedSprite2D.new()
var sprite_frames := SpriteFrames.new()
sprite_frames.add_animation(&"run")
for i in 3:
	sprite_frames.add_frame(&"run", make_texture())
sprite_frames.set_animation_speed(&"run", 30.0)
sprite_frames.set_animation_loop(&"run", true)
sprite.sprite_frames = sprite_frames
node.add_child(sprite)
var looped := [0]
var sprite_finished := [0]
sprite.animation_looped.connect(func() -> void: looped[0] += 1)
sprite.animation_finished.connect(func() -> void: sprite_finished[0] += 1)
sprite.play(&"run")
await frames(20)
expect(looped[0] > 0 and sprite_finished[0] == 0, "循环动画发 animation_looped 不发 animation_finished")
sprite.frame = 2
sprite.play(&"run")
expect(sprite.frame == 2, "对同名动画再调 play 不重启")
sprite.stop()
expect(sprite.frame == 0, "stop 把 frame 归零")
sprite_frames.set_animation_loop(&"run", false)
sprite.play(&"run")
await frames(20)
expect(sprite_finished[0] == 1, "非循环动画结束发 animation_finished")
sprite.queue_free()
```

## SKILL.md `parameters/Locomotion/Move/blend_position`

<!-- run: frames 60 -->

<!-- check: setup -->
```gdscript
var player := AnimationPlayer.new()
player.name = "AnimationPlayer"
node.add_child(player)
var library := AnimationLibrary.new()
for anim_name: StringName in [&"Idle", &"Walk", &"Run", &"Slash"]:
	var anim := Animation.new()
	anim.length = 0.5
	anim.loop_mode = Animation.LOOP_LINEAR
	var track := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(track, ^".:rotation")
	anim.track_insert_key(track, 0.0, 0.0)
	anim.track_insert_key(track, 0.5, 1.0)
	library.add_animation(anim_name, anim)
player.add_animation_library(&"", library)

var ground := AnimationNodeAnimation.new()
ground.animation = &"Idle"
var move := AnimationNodeBlendSpace2D.new()
for point: Array in [[&"Idle", Vector2.ZERO], [&"Walk", Vector2(0.5, 0.0)], [&"Run", Vector2(1.0, 0.0)]]:
	var animation_node := AnimationNodeAnimation.new()
	animation_node.animation = point[0]
	move.add_blend_point(animation_node, point[1], -1, point[0])
var machine := AnimationNodeStateMachine.new()
machine.add_node(&"Ground", ground)
machine.add_node(&"Move", move)
machine.add_transition(&"Start", &"Ground", AnimationNodeStateMachineTransition.new())
machine.add_transition(&"Ground", &"Move", AnimationNodeStateMachineTransition.new())
machine.add_transition(&"Move", &"Ground", AnimationNodeStateMachineTransition.new())

var blend_tree := AnimationNodeBlendTree.new()
blend_tree.add_node(&"Locomotion", machine)
var shot := AnimationNodeOneShot.new()
blend_tree.add_node(&"Attack", shot)
var slash := AnimationNodeAnimation.new()
slash.animation = &"Slash"
blend_tree.add_node(&"SlashAnim", slash)
blend_tree.connect_node(&"Attack", 0, &"Locomotion")
blend_tree.connect_node(&"Attack", 1, &"SlashAnim")
blend_tree.connect_node(&"output", 0, &"Attack")

var tree := node.get_node("AnimationTree") as AnimationTree
tree.anim_player = ^"../AnimationPlayer"
tree.tree_root = blend_tree
tree.active = true

var body := CollisionShape2D.new()
var circle := CircleShape2D.new()
circle.radius = 10.0
body.shape = circle
node.add_child(body)
```

```gdscript
await frames(2)
var state: AnimationNodeStateMachinePlayback = node._state
state.start(&"Move")
node.velocity = Vector2(100.0, 0.0)
await frames(2)
expect(node._tree["parameters/Locomotion/Move/blend_position"] == Vector2(0.5, 0.0), "blend_position 取 velocity / 200")
expect(state.get_current_node() == &"Move", "start 进入 Move")

var ground := StaticBody2D.new()
ground.position = Vector2(0.0, 40.0)
var ground_shape := CollisionShape2D.new()
var rect := RectangleShape2D.new()
rect.size = Vector2(400.0, 20.0)
ground_shape.shape = rect
ground.add_child(ground_shape)
node.get_parent().add_child(ground)
node.velocity = Vector2(0.0, 100.0)
for i in 40:
	node.move_and_slide()
	await frames(1)
expect(node.is_on_floor(), "落在地面上")
await frames(5)
expect(state.get_current_node() == &"Ground", "is_on_floor 时 travel 到 Ground")
ground.queue_free()

Input.action_press(&"attack")
await frames(3)
Input.action_release(&"attack")
expect(node._tree["parameters/Attack/active"], "attack 动作触发 OneShot")
```

## references/animation-tree.md `if not _state.is_playing`

<!-- check: setup -->
```gdscript
var player := AnimationPlayer.new()
player.name = "AnimationPlayer"
node.add_child(player)
var library := AnimationLibrary.new()
for anim_name: StringName in [&"Idle", &"Run", &"Slash"]:
	var anim := Animation.new()
	anim.length = 0.5
	anim.loop_mode = Animation.LOOP_LINEAR
	var track := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(track, ^".:rotation")
	anim.track_insert_key(track, 0.0, 0.0)
	anim.track_insert_key(track, 0.5, 1.0)
	library.add_animation(anim_name, anim)
player.add_animation_library(&"", library)

var machine := AnimationNodeStateMachine.new()
for state_name: StringName in [&"Idle", &"Run"]:
	var animation_node := AnimationNodeAnimation.new()
	animation_node.animation = state_name
	machine.add_node(state_name, animation_node)
machine.add_transition(&"Idle", &"Run", AnimationNodeStateMachineTransition.new())
machine.add_transition(&"Run", &"Idle", AnimationNodeStateMachineTransition.new())
var tree := node.get_node("AnimationTree") as AnimationTree
tree.anim_player = ^"../AnimationPlayer"
tree.tree_root = machine
tree.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
tree.active = true
```

```gdscript
await frames(3)
var state: AnimationNodeStateMachinePlayback = node._state
expect(state.is_playing(), "第一次物理帧里 start 之后在播")
expect(state.get_current_node() == &"Idle", "start 到 Idle")
node.velocity = Vector2(50.0, 0.0)
await frames(10)
expect(state.get_current_node() == &"Run", "速度大于 1 时 travel 到 Run")

var player := node.get_node("AnimationPlayer") as AnimationPlayer
var blend_tree := AnimationNodeBlendTree.new()
var idle := AnimationNodeAnimation.new()
idle.animation = &"Idle"
blend_tree.add_node(&"IdleAnim", idle)
var run := AnimationNodeAnimation.new()
run.animation = &"Run"
blend_tree.add_node(&"RunAnim", run)
var transition := AnimationNodeTransition.new()
transition.input_count = 2
blend_tree.add_node(&"Switch", transition)
var scale_node := AnimationNodeTimeScale.new()
blend_tree.add_node(&"Speed", scale_node)
var seek := AnimationNodeTimeSeek.new()
blend_tree.add_node(&"Seek", seek)
var blend2 := AnimationNodeBlend2.new()
blend_tree.add_node(&"Mix", blend2)
var walk := AnimationNodeBlendSpace1D.new()
blend_tree.add_node(&"Walk", walk)
blend_tree.connect_node(&"Switch", 0, &"IdleAnim")
blend_tree.connect_node(&"Switch", 1, &"RunAnim")
blend_tree.connect_node(&"Speed", 0, &"Switch")
blend_tree.connect_node(&"Seek", 0, &"Speed")
blend_tree.connect_node(&"output", 0, &"Seek")
var other := AnimationTree.new()
node.add_child(other)
other.anim_player = other.get_path_to(player)
other.tree_root = blend_tree
other.active = true
await frames(2)
other["parameters/Switch/transition_request"] = "state_1"
other["parameters/Mix/blend_amount"] = 0.5
other["parameters/Speed/scale"] = 0.5
other["parameters/Walk/blend_position"] = 100.0
other["parameters/Seek/seek_request"] = 0.2
await frames(2)
expect(other["parameters/Switch/current_state"] == "state_1", "transition_request 切换后 current_state 是目标名")
expect(is_equal_approx(other["parameters/Mix/blend_amount"], 0.5), "blend_amount 可写")
expect(is_equal_approx(other["parameters/Speed/scale"], 0.5), "scale 可写")
expect(is_equal_approx(other["parameters/Walk/blend_position"], 100.0), "BlendSpace1D 的 blend_position 是 float")
expect(is_equal_approx(other["parameters/Seek/seek_request"], -1.0), "seek_request 处理后复位")
other.queue_free()
```

## references/animation-tree.md `func attack`

<!-- check: setup -->
```gdscript
var player := AnimationPlayer.new()
player.name = "AnimationPlayer"
node.add_child(player)
var library := AnimationLibrary.new()
for anim_name: StringName in [&"Idle", &"Slash"]:
	var anim := Animation.new()
	anim.length = 0.3
	var track := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(track, ^".:rotation")
	anim.track_insert_key(track, 0.0, 0.0)
	anim.track_insert_key(track, 0.3, 1.0)
	library.add_animation(anim_name, anim)
player.add_animation_library(&"", library)

var blend_tree := AnimationNodeBlendTree.new()
var shot := AnimationNodeOneShot.new()
blend_tree.add_node(&"AttackShot", shot)
var base := AnimationNodeAnimation.new()
base.animation = &"Idle"
blend_tree.add_node(&"Base", base)
var slash := AnimationNodeAnimation.new()
slash.animation = &"Slash"
blend_tree.add_node(&"Slash", slash)
blend_tree.connect_node(&"AttackShot", 0, &"Base")
blend_tree.connect_node(&"AttackShot", 1, &"Slash")
blend_tree.connect_node(&"output", 0, &"AttackShot")
var tree := node.get_node("AnimationTree") as AnimationTree
tree.anim_player = ^"../AnimationPlayer"
tree.tree_root = blend_tree
tree.active = true
```

```gdscript
await frames(3)
expect(not node._tree["parameters/AttackShot/active"], "开始时没在攻击")
node.attack()
await frames(3)
expect(node._tree["parameters/AttackShot/active"], "FIRE 之后 active 为 true")
node.attack()
await frames(1)
expect(node._tree["parameters/AttackShot/active"], "攻击中再调 attack 直接返回")
await frames(30)
expect(not node._tree["parameters/AttackShot/active"], "播完后 active 为 false")
node.attack()
await frames(3)
node._tree["parameters/AttackShot/request"] = AnimationNodeOneShot.ONE_SHOT_REQUEST_ABORT
await frames(10)
expect(not node._tree["parameters/AttackShot/active"], "ABORT 停止攻击")
```

## SKILL.md `func pop`

<!-- check: setup -->
```gdscript
node.size = Vector2(100.0, 40.0)
```

```gdscript
node.pop()
var first: Tween = node._tween
await frames(3)
expect(node.scale.x > 1.0, "第一段放大")
node.pop()
expect(not first.is_valid(), "再次 pop 时旧 Tween 已 kill")
expect(node.pivot_offset == Vector2(50.0, 20.0), "pivot_offset 取 size 的一半")
await frames(30)
expect(node.scale.is_equal_approx(Vector2.ONE), "最终回到原大小")

var holder := Node.new()
node.add_child(holder)
var bound := holder.create_tween()
bound.tween_interval(10.0)
var unbound := node.get_tree().create_tween()
unbound.tween_interval(10.0)
holder.free()
await frames(2)
expect(not bound.is_valid(), "节点释放时绑定的 Tween 自动 kill")
expect(unbound.is_valid(), "get_tree().create_tween() 不随节点释放")
unbound.kill()

var parked := Node2D.new()
node.add_child(parked)
var parked_tween := parked.create_tween()
parked_tween.tween_property(parked, "position:x", 100.0, 1.0)
await frames(10)
var at_remove := parked.position.x
node.remove_child(parked)
await frames(10)
expect(is_equal_approx(parked.position.x, at_remove), "节点出树时 Tween 暂停")
node.add_child(parked)
await frames(10)
expect(parked.position.x > at_remove, "回树后继续")
parked.queue_free()

var waited := [false]
var timer := node.create_tween()
timer.tween_interval(0.05)
await timer.tween_interval(0.05).finished
waited[0] = true
expect(waited[0], "await tween_interval(...).finished 能返回")
```

## SKILL.md `func cutscene`

<!-- run: frames 120 -->

```gdscript
node.cutscene()
await frames(120)
expect(is_equal_approx(node.position.x, 600.0), "走完第一步后停在 AwaitTweener 上")
node.dialogue_closed.emit()
await frames(120)
expect(is_zero_approx(node.position.x), "信号发出后继续走完最后一步")
```

## SKILL.md `func hit_flash`

<!-- run: mode render; frames 40 -->

<!-- check: setup -->
```gdscript
var shader := Shader.new()
shader.code = """shader_type canvas_item;

instance uniform float flash : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	COLOR.rgb = mix(COLOR.rgb, vec3(1.0), flash);
}
"""
var material := ShaderMaterial.new()
material.shader = shader
node.material = material
node.texture = make_texture(32, 32, Color(1.0, 0.0, 0.0))
node.position = Vector2(64.0, 64.0)
```

```gdscript
await frames(3)
await RenderingServer.frame_post_draw
var image := node.get_viewport().get_texture().get_image()
expect(image.get_pixel(64, 64).g < 0.05, "闪白前保持原色")
node.hit_flash()
await RenderingServer.frame_post_draw
await RenderingServer.frame_post_draw
image = node.get_viewport().get_texture().get_image()
expect(image.get_pixel(64, 64).g > 0.5, "闪白开始时偏白")
var mid: float = node.get_instance_shader_parameter(&"flash")
expect(mid > 0.0 and mid <= 1.0, "instance uniform 在被 tween 驱动")
await frames(20)
await RenderingServer.frame_post_draw
image = node.get_viewport().get_texture().get_image()
expect(image.get_pixel(64, 64).g < 0.05, "闪白结束后还原")
expect(is_zero_approx(node.get_instance_shader_parameter(&"flash")), "tween 结束时为 0")
```

## references/tween-recipes.md `func squash`

```gdscript
node.squash()
await frames(3)
expect(node.scale.x > 1.0 and node.scale.y < 1.0, "先压扁")
node.squash()
expect(node.scale == Vector2.ONE, "重播前重置 scale")
await frames(60)
expect(node.scale.is_equal_approx(Vector2.ONE), "最终回到原大小")

var holder := Node.new()
node.add_child(holder)
var count := [0]
var killed := holder.create_tween()
killed.tween_interval(0.1)
killed.finished.connect(func() -> void: count[0] += 1)
killed.kill()
var freed := holder.create_tween()
freed.tween_interval(0.1)
freed.finished.connect(func() -> void: count[0] += 1)
holder.free()
await frames(15)
expect(count[0] == 0, "kill 与节点释放都不发 finished")
```

## references/tween-recipes.md `func vanish`

```gdscript
var seen := [-1.0]
node.tree_exiting.connect(func() -> void: seen[0] = node.modulate.a)
node.vanish()
await frames(10)
expect(node.modulate.a < 1.0 and node.modulate.a > 0.0, "淡出中")
await frames(30)
expect(not is_instance_valid(node), "淡出后销毁")
expect(is_zero_approx(seen[0]), "销毁时 alpha 为 0")
```

## references/tween-recipes.md `func pop`

```gdscript
node.position = Vector2(0.0, 100.0)
var seen := [0.0]
node.tree_exiting.connect(func() -> void: seen[0] = node.position.y)
node.pop(25)
expect(node.text == "25", "文本是伤害数")
await frames(10)
expect(node.position.y < 100.0 and node.modulate.a == 1.0, "先上飘 后淡出")
await frames(50)
expect(not is_instance_valid(node), "收尾销毁")
expect(is_equal_approx(seen[0], 60.0), "as_relative 终点是偏移量")
```

## references/tween-recipes.md `func set_score`

```gdscript
node.set_score(100)
await frames(10)
node.set_score(250)
await frames(60)
expect(node.text == "250", "数字滚动到终值")
expect(node._shown == 250, "_shown 记录当前值")
```

## references/tween-recipes.md `func change_to`

<!-- run: frames 120 -->

<!-- check: prepare -->
```gdscript
var target := Node2D.new()
target.name = "Target"
var packed := PackedScene.new()
packed.pack(target)
ResourceSaver.save(packed, "res://target.tscn")
target.free()
```

```gdscript
var tree := node.get_tree()
var fade := node.get_node("Fade") as ColorRect
node.change_to("res://target.tscn")
await frames(5)
expect(fade.mouse_filter == Control.MOUSE_FILTER_STOP, "淡出期间挡点击")
await frames(100)
expect(tree.current_scene != null and tree.current_scene.name == "Target", "场景已切换")
expect(is_zero_approx(fade.modulate.a), "淡入完成")
expect(fade.mouse_filter == Control.MOUSE_FILTER_IGNORE, "平时放行点击")
expect(is_instance_valid(node), "转场层不随场景切换释放")
tree.current_scene.queue_free()
```

## references/tween-recipes.md `set_loops()`

```gdscript
node.position = Vector2.ZERO
var low := 0.0
var high := 0.0
for i in 120:
	await frames(1)
	low = minf(low, node.position.y)
	high = maxf(high, node.position.y)
expect(low < -5.5, "往上到约 -6")
expect(high > 5.5 or node.position.y > -6.0, "第二段往回走")
var parent := node.get_parent()
parent.remove_child(node)
var at_remove := node.position.y
await frames(10)
expect(is_equal_approx(node.position.y, at_remove), "离树时暂停")
parent.add_child(node)
await frames(20)
expect(not is_equal_approx(node.position.y, at_remove), "回树继续")
```

## references/tween-recipes.md `func respawn`

```gdscript
node.position = Vector2(80.0, 80.0)
node.respawn()
var lowest := 1.0
for i in 60:
	await frames(1)
	lowest = minf(lowest, node.modulate.a)
expect(node.position.is_zero_approx(), "位移 Tween 走完")
expect(lowest < 0.3, "子 Tween 的闪烁在执行")
expect(is_equal_approx(node.modulate.a, 1.0), "闪烁结束 alpha 回到 1")
```

## references/tween-recipes.md `func ask`

<!-- run: frames 150 -->

```gdscript
node.ask()
node.dialogue_closed.emit()
await frames(90)
expect(is_equal_approx(node.position.x, 400.0), "AwaitTweener 开始前发的信号收不到，停在 400")
node.dialogue_closed.emit()
await frames(90)
expect(is_zero_approx(node.position.x), "信号发出后继续")

var count := [0]
node.dialogue_closed.connect(func() -> void: count[0] += 1)
node.wait_and_emit()
await frames(5)
expect(count[0] == 1, "同一步里等待并发信号")
expect(node.get_tree().get_processed_tweens().is_empty(), "等待的 Tween 已结束")
```

## references/tween-recipes.md `func open`

<!-- run: frames 60 -->

```gdscript
var tree := node.get_tree()
Engine.time_scale = 0.1
tree.paused = true
node.open()
await frames(20)
expect(is_equal_approx(node.modulate.a, 1.0), "暂停且慢放时仍然走完")
tree.paused = false
Engine.time_scale = 1.0
```

## references/tween-recipes.md `func start_manual`

```gdscript
node.start_manual()
await frames(5)
expect(is_zero_approx(node.position.x), "pause 之后不自己走")
node.tick(0.5)
expect(is_equal_approx(node.position.x, 50.0), "custom_step 推进")
var tween: Tween = node._tween
var done := [0]
tween.finished.connect(func() -> void: done[0] += 1)
expect(tween.custom_step(0.5), "走完的那次调用仍返回 true")
expect(is_equal_approx(node.position.x, 100.0), "到达终点")
expect(not tween.custom_step(0.1), "下一次才返回 false")
await frames(2)
expect(done[0] == 1, "finished 信号发出")

node.position.x = 0.0
node.start_manual()
node.tick(0.25)
node.tick(0.25)
expect(is_equal_approx(node.position.x, 50.0), "累计 custom_step")
```
