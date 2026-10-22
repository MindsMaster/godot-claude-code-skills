# godot-shaders-vfx

## SKILL.md `func hit`

<!-- run: mode render; frames 40 -->

<!-- check: setup -->
```gdscript
var shader := Shader.new()
shader.code = """shader_type canvas_item;

instance uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0);

void fragment() {
	COLOR.rgb = mix(COLOR.rgb, flash_color.rgb, flash);
}
"""
var material := ShaderMaterial.new()
material.shader = shader
node.material = material
node.texture = make_texture(32, 32, Color(1.0, 0.0, 0.0))
node.position = Vector2(64.0, 64.0)
```

```gdscript
var other := Sprite2D.new()
other.texture = node.texture
other.material = node.material
other.position = Vector2(160.0, 64.0)
node.get_parent().add_child(other)
await frames(3)
await RenderingServer.frame_post_draw
var image := root.get_texture().get_image()
expect(image.get_pixel(64, 64).g < 0.05 and image.get_pixel(160, 64).g < 0.05, "闪白前两个精灵都是红色")

node.hit()
node.hit()
await RenderingServer.frame_post_draw
await RenderingServer.frame_post_draw
image = root.get_texture().get_image()
expect(image.get_pixel(64, 64).g > 0.5, "受击的精灵偏白")
expect(image.get_pixel(160, 64).g < 0.05, "共用同一材质的另一个精灵不闪")
var mid: float = node.get_instance_shader_parameter(&"flash")
expect(mid > 0.0 and mid <= 1.0, "instance uniform 被 tween 驱动")
await frames(20)
expect(is_zero_approx(node.get_instance_shader_parameter(&"flash")), "tween 结束时为 0")
await RenderingServer.frame_post_draw
image = root.get_texture().get_image()
expect(image.get_pixel(64, 64).g < 0.05, "闪白结束后还原")

var shared := node.material as ShaderMaterial
expect(shared.get_shader_parameter(&"flash_color") == null, "没写过的 uniform 读出 null")
shared.set_shader_parameter(&"flash_color", Color.WHITE)
var tween := create_tween()
tween.tween_property(shared, "shader_parameter/flash_color", Color.BLACK, 0.05)
await tween.finished
expect(shared.get_shader_parameter(&"flash_color") == Color.BLACK, "写过初值后可以 tween 材质参数")
other.queue_free()
```

## SKILL.md `background_canvas_max_layer`

<!-- run: mode render; frames 20 -->

```gdscript
var sprite := Sprite2D.new()
sprite.texture = make_texture(64, 64, Color.WHITE)
sprite.position = Vector2(100.0, 100.0)
node.add_child(sprite)
var layer := CanvasLayer.new()
layer.layer = 1
var panel := ColorRect.new()
panel.color = Color.WHITE
panel.position = Vector2(400.0, 100.0)
panel.size = Vector2(64.0, 64.0)
layer.add_child(panel)
node.add_child(layer)
var env := (node.get_child(0) as WorldEnvironment).environment
expect(env.background_mode == Environment.BG_CANVAS, "背景模式是 Canvas")
env.background_mode = Environment.BG_CLEAR_COLOR
await frames(5)
await RenderingServer.frame_post_draw
var image := root.get_texture().get_image()
var clear := image.get_pixel(300, 400)
var around_sprite := 0
for y in range(40, 170):
	for x in range(30, 170):
		if x >= 64 and x < 136 and y >= 64 and y < 136:
			continue
		if absf(image.get_pixel(x, y).r - clear.r) > 0.002:
			around_sprite += 1
expect(around_sprite == 0, "背景为 Clear Color 时没有 glow")

env.background_mode = Environment.BG_CANVAS
await frames(5)
await RenderingServer.frame_post_draw
image = root.get_texture().get_image()
around_sprite = 0
var around_panel := 0
for y in range(40, 170):
	for x in range(30, 170):
		if x >= 64 and x < 136 and y >= 64 and y < 136:
			continue
		if absf(image.get_pixel(x, y).r - clear.r) > 0.002:
			around_sprite += 1
for y in range(40, 200):
	for x in range(330, 530):
		if x >= 396 and x < 468 and y >= 96 and y < 168:
			continue
		if absf(image.get_pixel(x, y).r - clear.r) > 0.002:
			around_panel += 1
expect(around_sprite > 0, "Canvas 背景下 2D 精灵周围出现 glow")
expect(around_panel == 0, "层号大于 background_canvas_max_layer 的 CanvasLayer 不发光")
```

## SKILL.md `finished.connect(queue_free)`

<!-- run: mode render; frames 120 -->

<!-- check: setup -->
```gdscript
node.process_material = ParticleProcessMaterial.new()
var quad := QuadMesh.new()
quad.size = Vector2(0.2, 0.2)
node.draw_pass_1 = quad
node.amount = 8
node.lifetime = 0.3
```

```gdscript
var camera := Camera3D.new()
camera.position = Vector3(0.0, 0.0, 5.0)
node.get_parent().add_child(camera)
expect(node.one_shot, "_ready 里设了 one_shot")
await frames(5)
expect(node.emitting, "restart 之后在发射")
await frames(110)
expect(not is_instance_valid(node), "one_shot 发完后 finished 触发 queue_free")
camera.queue_free()
```

## references/particles.md `func make_sparks`

<!-- run: mode render; frames 120 -->

```gdscript
var camera := Camera3D.new()
camera.position = Vector3(0.0, 0.0, 5.0)
node.add_child(camera)
await frames(2)
await RenderingServer.frame_post_draw
var empty := root.get_texture().get_image()
var clear := empty.get_pixel(5, 5)

var sparks := node.make_sparks()
expect(sparks.draw_passes == 1 and sparks.draw_pass_1 != null, "默认一个绘制通道")
expect(sparks.process_material is ParticleProcessMaterial, "有 process_material")
node.add_child(sparks)
sparks.restart()
await frames(5)
await RenderingServer.frame_post_draw
var image := root.get_texture().get_image()
var changed := 0
for y in image.get_height():
	for x in image.get_width():
		if not image.get_pixel(x, y).is_equal_approx(clear):
			changed += 1
expect(changed > 0, "粒子画出来了")
await frames(100)
expect(not is_instance_valid(sparks), "one_shot 发完后 finished 触发 queue_free")
camera.queue_free()
```

## references/particles.md `func spawn_hit`

<!-- run: mode render; frames 120 -->

<!-- check: setup -->
```gdscript
var effect := GPUParticles3D.new()
effect.process_material = ParticleProcessMaterial.new()
effect.draw_pass_1 = QuadMesh.new()
effect.amount = 4
effect.lifetime = 0.3
effect.one_shot = true
effect.emitting = false
node.hit_effect = make_scene(effect)
```

```gdscript
var tree := node.get_tree()
tree.current_scene = node
var camera := Camera3D.new()
camera.position = Vector3(0.0, 0.0, 8.0)
node.add_child(camera)
node.spawn_hit(Vector3(1.0, 2.0, 0.0), Vector3.UP)
var up_effect := node.get_child(1) as GPUParticles3D
expect(up_effect.global_position.is_equal_approx(Vector3(1.0, 2.0, 0.0)), "特效放在命中点")
expect((-up_effect.global_basis.z).is_equal_approx(Vector3.UP), "法线朝上时 -Z 指向法线")
node.spawn_hit(Vector3(0.0, 0.0, 0.0), Vector3.RIGHT)
var side_effect := node.get_child(2) as GPUParticles3D
expect((-side_effect.global_basis.z).is_equal_approx(Vector3.RIGHT), "法线朝右时 -Z 指向法线")
await frames(5)
expect(up_effect.emitting, "restart 之后在发射")
await frames(100)
expect(not is_instance_valid(up_effect) and not is_instance_valid(side_effect), "发完后销毁")
camera.queue_free()
tree.current_scene = null
```

## references/post-processing.md `env.glow_hdr_threshold`

<!-- run: mode render; driver opengl3; frames 20 -->

```gdscript
var sprite := Sprite2D.new()
sprite.texture = make_texture(64, 64, Color.WHITE)
sprite.position = Vector2(100.0, 100.0)
node.add_child(sprite)
var env := (node.get_child(0) as WorldEnvironment).environment
env.glow_intensity = 2.0
env.glow_bloom = 0.3
expect(env.background_mode == Environment.BG_CANVAS, "背景模式是 Canvas")
env.background_mode = Environment.BG_CLEAR_COLOR
await frames(5)
await RenderingServer.frame_post_draw
var image := root.get_texture().get_image()
var clear := image.get_pixel(300, 400)
var glow := 0
for y in range(40, 170):
	for x in range(30, 170):
		if x >= 64 and x < 136 and y >= 64 and y < 136:
			continue
		if absf(image.get_pixel(x, y).r - clear.r) > 0.002:
			glow += 1
expect(glow == 0, "Compatibility 下 Clear Color 背景没有 glow")

env.background_mode = Environment.BG_CANVAS
await frames(5)
await RenderingServer.frame_post_draw
image = root.get_texture().get_image()
glow = 0
for y in range(40, 170):
	for x in range(30, 170):
		if x >= 64 and x < 136 and y >= 64 and y < 136:
			continue
		if absf(image.get_pixel(x, y).r - clear.r) > 0.002:
			glow += 1
expect(glow > 0, "Compatibility 下 Canvas 背景出现 glow")
```

## references/post-processing.md `res://shaders/post.gdshader`

<!-- run: mode render; frames 20 -->

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://shaders")
var file := FileAccess.open("res://shaders/post.gdshader", FileAccess.WRITE)
file.store_string("""shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
	COLOR = vec4(vec3(1.0) - textureLod(screen_texture, SCREEN_UV, 0.0).rgb, 1.0);
}
""")
file.close()
```

```gdscript
var background := ColorRect.new()
background.color = Color(1.0, 0.0, 0.0)
background.set_anchors_preset(Control.PRESET_FULL_RECT)
node.get_parent().add_child(background)
node.get_parent().move_child(background, 0)
var overlay := CanvasLayer.new()
overlay.layer = 20
var hud := ColorRect.new()
hud.color = Color(0.0, 0.0, 1.0)
hud.position = Vector2(10.0, 10.0)
hud.size = Vector2(50.0, 50.0)
overlay.add_child(hud)
node.get_parent().add_child(overlay)
await frames(5)
await RenderingServer.frame_post_draw
var image := root.get_texture().get_image()
var inverted := image.get_pixel(576, 324)
expect(inverted.r < 0.05 and inverted.g > 0.95 and inverted.b > 0.95, "红色背景被反色成青色")
var rect := node.get_child(0) as ColorRect
expect(node.layer == 10, "全屏层在 HUD 之下")
expect(rect.mouse_filter == Control.MOUSE_FILTER_IGNORE, "全屏 ColorRect 不吞点击")
expect(rect.material is ShaderMaterial, "挂了 ShaderMaterial")
var hud_pixel := image.get_pixel(30, 30)
expect(hud_pixel.r < 0.05 and hud_pixel.g < 0.05 and hud_pixel.b > 0.95, "layer 更大的 CanvasLayer 不受效果影响")
var plain := ColorRect.new()
expect(plain.mouse_filter == Control.MOUSE_FILTER_STOP, "ColorRect 默认 mouse_filter 是 STOP")
plain.free()
background.queue_free()
overlay.queue_free()
```

## references/post-processing.md `InvertEffect`

<!-- run: mode render; frames 20 -->

```gdscript
var env := Environment.new()
env.background_mode = Environment.BG_COLOR
env.background_color = Color(1.0, 0.0, 0.0)
var effects: Array[CompositorEffect] = []
var compositor := Compositor.new()
compositor.compositor_effects = effects
var camera := Camera3D.new()
camera.environment = env
camera.compositor = compositor
camera.position = Vector3(0.0, 0.0, 3.0)
root.add_child(camera)
camera.make_current()
await frames(5)
await RenderingServer.frame_post_draw
var image := root.get_texture().get_image()
var plain := image.get_pixel(576, 324)
expect(plain.r > 0.95 and plain.g < 0.05 and plain.b < 0.05, "没挂效果时是红色背景")

effects.append(node)
compositor.compositor_effects = effects
await frames(5)
await RenderingServer.frame_post_draw
image = root.get_texture().get_image()
var inverted := image.get_pixel(576, 324)
expect(inverted.r < 0.05 and inverted.g > 0.95 and inverted.b > 0.95, "反色后是青色")

node.enabled = false
await frames(5)
await RenderingServer.frame_post_draw
image = root.get_texture().get_image()
expect(image.get_pixel(576, 324).r > 0.95, "enabled 为 false 时还原")
node.enabled = true
effects.clear()
compositor.compositor_effects = effects
camera.queue_free()
```

## references/shader-recipes.md `func hit`

<!-- run: mode render; frames 40 -->

<!-- check: setup -->
```gdscript
var shader := Shader.new()
shader.code = """shader_type spatial;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
instance uniform float flash : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	ALBEDO = texture(albedo_tex, UV).rgb;
	EMISSION = vec3(flash) * 2.0;
}
"""
var material := ShaderMaterial.new()
material.shader = shader
material.set_shader_parameter(&"albedo_tex", make_texture(8, 8, Color(0.2, 0.0, 0.0)))
var mesh := SphereMesh.new()
node.mesh = mesh
node.material_override = material
```

```gdscript
var camera := Camera3D.new()
camera.position = Vector3(0.0, 0.0, 3.0)
node.get_parent().add_child(camera)
camera.make_current()
await frames(5)
await RenderingServer.frame_post_draw
var image := root.get_texture().get_image()
var before := image.get_pixel(576, 324)
expect(before.g < 0.2, "闪白前偏暗红")
node.hit()
node.hit()
await RenderingServer.frame_post_draw
await RenderingServer.frame_post_draw
image = root.get_texture().get_image()
expect(image.get_pixel(576, 324).g > 0.5, "闪白开始时偏白")
var peak := image.get_pixel(576, 324).g
await frames(6)
await RenderingServer.frame_post_draw
image = root.get_texture().get_image()
var middle := image.get_pixel(576, 324).g
expect(middle < peak and middle > before.g, "闪白在衰减")
await frames(25)
await RenderingServer.frame_post_draw
image = root.get_texture().get_image()
expect(image.get_pixel(576, 324).g < 0.2, "闪白结束后还原")
camera.queue_free()
```

## references/shader-recipes.md `flash_shader`

<!-- run: mode render; frames 10 -->

<!-- check: setup -->
```gdscript
var shader := Shader.new()
shader.code = """shader_type canvas_item;

uniform vec4 flash_color : source_color = vec4(1.0);

void fragment() {
	COLOR.rgb = mix(COLOR.rgb, flash_color.rgb, 0.5);
}
"""
node.flash_shader = shader
```

```gdscript
var mat := node.material as ShaderMaterial
expect(mat != null and mat.shader == node.flash_shader, "_ready 挂上 ShaderMaterial")
expect(mat.get_shader_parameter(&"flash_color") == Color.WHITE, "set_shader_parameter 写入")

var scene_root := Node2D.new()
var first := Sprite2D.new()
first.name = "First"
var second := Sprite2D.new()
second.name = "Second"
var shared := ShaderMaterial.new()
shared.shader = node.flash_shader
first.material = shared
second.material = shared
scene_root.add_child(first)
scene_root.add_child(second)
var packed := make_scene(scene_root)
var one := packed.instantiate()
var two := packed.instantiate()
expect(one.get_node("First").material == two.get_node("First").material, "场景里的子资源在实例间共享")
expect(one.get_node("First").material == one.get_node("Second").material, "同一场景内的精灵共用一份材质")
one.free()
two.free()

var local_root := Node2D.new()
var local_sprite := Sprite2D.new()
local_sprite.name = "Sprite"
var local_material := ShaderMaterial.new()
local_material.shader = node.flash_shader
local_material.resource_local_to_scene = true
local_sprite.material = local_material
local_root.add_child(local_sprite)
var local_packed := make_scene(local_root)
var local_one := local_packed.instantiate()
var local_two := local_packed.instantiate()
expect(local_one.get_node("Sprite").material != local_two.get_node("Sprite").material, "resource_local_to_scene 每个实例一份")
local_one.free()
local_two.free()

RenderingServer.global_shader_parameter_add(&"wind_strength", RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.5)
RenderingServer.global_shader_parameter_set(&"wind_strength", 1.2)
RenderingServer.global_shader_parameter_remove(&"wind_strength")
```
