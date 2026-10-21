# 粒子

## 选节点

| 节点 | 说明 |
|---|---|
| `GPUParticles3D` `GPUParticles2D` | 默认选择。运动在 GPU 上算，靠 `ParticleProcessMaterial` 或自写粒子 shader 驱动 |
| `CPUParticles3D` `CPUParticles2D` | 运动在 CPU 上算，选项直接是节点属性。低端设备或 GPU 吃紧时用，少量粒子。功能追平 GPU 版，但不再加新功能 |

编辑器视口菜单能互相转换。GPU 转 CPU 会丢：多个绘制通道，湍流，子发射器，拖尾，吸引器，碰撞。

## 最小配置

```gdscript
extends Node3D

func make_sparks() -> GPUParticles3D:
	var gradient: Gradient = Gradient.new()
	gradient.set_color(0, Color(1.0, 0.9, 0.4, 1.0))
	gradient.set_color(1, Color(1.0, 0.2, 0.0, 0.0))
	var ramp: GradientTexture1D = GradientTexture1D.new()
	ramp.gradient = gradient

	var process: ParticleProcessMaterial = ParticleProcessMaterial.new()
	process.direction = Vector3.UP
	process.spread = 35.0
	process.initial_velocity_min = 4.0
	process.initial_velocity_max = 8.0
	process.gravity = Vector3(0.0, -9.8, 0.0)
	process.scale_min = 0.5
	process.scale_max = 1.0
	process.color_ramp = ramp

	var draw: StandardMaterial3D = StandardMaterial3D.new()
	draw.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	draw.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	draw.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	draw.vertex_color_use_as_albedo = true
	draw.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	draw.billboard_keep_scale = true

	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(0.1, 0.1)
	quad.material = draw

	var particles: GPUParticles3D = GPUParticles3D.new()
	particles.process_material = process
	particles.draw_pass_1 = quad
	particles.amount = 24
	particles.lifetime = 0.6
	particles.one_shot = true
	particles.explosiveness = 1.0
	particles.finished.connect(particles.queue_free)
	return particles
```

必须设 `process_material` 和至少一个绘制通道，否则看不到。最多 4 个通道：`draw_passes` 设数量，`draw_pass_1` 到 `draw_pass_4` 放网格，每个通道有自己的材质，共享同一份运动数据。

## 生成命中特效

```gdscript
extends Node3D

@export var hit_effect: PackedScene

func spawn_hit(point: Vector3, normal: Vector3) -> void:
	var effect: GPUParticles3D = hit_effect.instantiate() as GPUParticles3D
	get_tree().current_scene.add_child(effect)
	effect.global_position = point
	var up: Vector3 = Vector3.UP if absf(normal.y) < 0.99 else Vector3.RIGHT
	effect.look_at(point + normal, up)
	effect.finished.connect(effect.queue_free)
	effect.restart()
```

特效场景里把 `one_shot` 勾上，`emitting` 可以关掉，再由代码 `restart()`。不需要对象池。

## 节点属性

| 属性 | 说明 |
|---|---|
| `amount` 与 `lifetime` | 每秒发射数等于二者之比。改 `amount` 会重启，连续调节用 `amount_ratio` |
| `one_shot` | 发射 `amount` 个后停止，用 `finished` 信号收尾 |
| `explosiveness` | 0 依次发射，1 一次全发 |
| `randomness` | 发射间隔的随机度，`explosiveness` 为 1 时无效 |
| `preprocess` | 预热秒数，开场就是稳态的灰尘与雾 |
| `speed_scale` | 0 暂停，2 两倍速，运动与渲染一起 |
| `fixed_fps` 与 `interpolate` | 降低处理频率省性能，开插值保持平滑。有碰撞时低频会穿透，需要调高 |
| `local_coords` | 开：随节点旋转与移动。关：世界坐标，下永远是世界 -Y |
| `visibility_aabb`（3D）`visibility_rect`（2D） | 离屏判定框，超出相机视野整体停止渲染，框外粒子瞬间消失 |
| `draw_order` | Index Lifetime Reverse Lifetime View Depth |
| `transform_align`（3D） | Z-Billboard，Y to Velocity 等 |
| `collision_base_size` | 碰撞大小，粒子很小很快时调大 |
| `use_fixed_seed` `seed` | 4.4+ 固定随机序列 |
| `trail_enabled` `trail_lifetime` | 拖尾 |

`capture_aabb()` 与编辑器的 Generate AABB 工具量出实际范围。3D 粒子的 LOD 选择也依赖这个框。

## ParticleProcessMaterial 分组

| 分组 | 要点 |
|---|---|
| Emission | `emission_shape` 点 球 球面 盒 点集 方向点集 环，另有 `emission_shape_offset` `emission_shape_scale` |
| Direction 与 Velocity | `direction` `spread` `flatness` `initial_velocity_*` |
| Acceleration | `gravity` `linear_accel_*` `radial_accel_*` `tangential_accel_*` `damping_*` |
| Angle 与 Angular velocity | `angle_*` `angular_velocity_*` `orbit_velocity_*` |
| Scale | `scale_min` `scale_max` `scale_curve` |
| Color | `color` `color_ramp`（整个寿命内的渐变，用 `GradientTexture1D`）`color_initial_ramp` `hue_variation_*` `alpha_curve` |
| Animation | `anim_speed_*` `anim_offset_*` 配合序列帧 |
| Turbulence | `turbulence_enabled` 开销大，同时只开几个，移动端慎用 |
| Collision | `collision_mode`：`COLLISION_RIGID` 反弹，`COLLISION_HIDE_ON_CONTACT` 碰到就隐藏，`collision_bounce` `collision_friction` |
| Sub Emitter | `sub_emitter_mode` 与 `sub_emitter_amount_*` `sub_emitter_frequency` |
| Attractor | `attractor_interaction_enabled` |

带 `_curve` 后缀的属性是随寿命变化的曲线，类型是 `CurveTexture` 一类的 `Texture2D`。

## 子发射器

1. 场景里有父子两个粒子节点
2. 父节点的 `sub_emitter` 指向子节点（实例化的场景需要开 Editable Children）
3. 父节点的 `ParticleProcessMaterial.sub_emitter_mode` 改成非 Disabled：`SUB_EMITTER_CONSTANT` 按 `sub_emitter_frequency` 持续，`SUB_EMITTER_AT_END` `SUB_EMITTER_AT_COLLISION` 用对应的 `amount`，`SUB_EMITTER_AT_START` 是 4.4+

- 成为子发射器的节点自动停止自己的发射，`emitting` 也不能再勾上
- 子节点同时存在的总粒子数受它自己的 `amount` 限制，不够就调大
- 子节点的 `explosiveness` 无效
- 不能自己做自己的子发射器，也不能递归
- 可以链式嵌套任意深

## 拖尾

仅 Forward+ 与 Mobile。

1. 粒子节点勾 `trail_enabled`，设 `trail_lifetime`（`GPUParticles3D` 里叫 Length Secs），一般 0.8 左右
2. 绘制通道换成 `RibbonTrailMesh`（带状）或 `TubeTrailMesh`（管状）
3. 绘制材质开 `use_particle_trails`
4. 带状的 `shape` 选 Flat 配公告牌，选 Cross 不配公告牌；`sections` `section_length` `section_segments` 控制光滑度与总长，`curve` 控制宽度形状

2D 里 `GPUParticles2D` 有 `trail_enabled` `trail_lifetime` `trail_sections` `trail_section_subdivisions`。

## 碰撞

3D 粒子在 GPU 上，看不到物理世界，要放碰撞节点，不与 `PhysicsBody3D` 碰撞：

| 节点 | 用于 |
|---|---|
| `GPUParticlesCollisionBox3D` `GPUParticlesCollisionSphere3D` | 地面 墙 简单体。`size` 或 `radius` |
| `GPUParticlesCollisionHeightField3D` | 大型室外。动态生成高度场，`resolution` 低会穿，`update_mode` 默认 When Moved 只在它自己移动时重建，`follow_camera_enabled` 跟相机 |
| `GPUParticlesCollisionSDF3D` | 有洞与悬挑的静态场景。需要在编辑器烘焙，运行时不能改。Compatibility 不支持 |

- 碰撞节点有 `cull_mask`，与粒子节点的可见层相交才生效
- 只在 `visibility_aabb` 内发生碰撞
- 粒子快、碰撞体薄时会穿透，调高 `fixed_fps`
- 把碰撞节点作为 `PhysicsBody3D` 的子节点，就能让粒子与各种物体碰撞

2D 粒子只和 `LightOccluder2D` 碰撞，`LightOccluder2D.sdf_collision` 默认 true。

## 吸引器

3D 专用，2D 没有。`GPUParticlesAttractorBox3D` `GPUParticlesAttractorSphere3D` `GPUParticlesAttractorVectorField3D`。流程：材质开 `attractor_interaction_enabled`，场景里放吸引器。`strength` 正数吸引，负数排斥，`attenuation` 控制衰减。向量场吸引器配 `NoiseTexture3D` 可以替代湍流，在世界空间生效且多个粒子系统反应一致。

## 序列帧

3D：绘制材质 `billboard_mode` 选 `BILLBOARD_PARTICLES`，设 `particles_anim_h_frames` `particles_anim_v_frames`，需要循环就开 `particles_anim_loop`。2D：粒子节点的材质用 `CanvasItemMaterial`，开 `particles_animation` 并设 `particles_anim_h_frames` `particles_anim_v_frames`。动画速度和起始帧用 `ParticleProcessMaterial` 的 `anim_speed_*` `anim_offset_*`。

## 自定义运动

`process_material` 可以换成 `ShaderMaterial`，shader 写 `shader_type particles`，在 `start()` 与 `process()` 里改 `TRANSFORM` `VELOCITY` `COLOR` `CUSTOM`。数据在帧间保留。只有 GPU 粒子节点支持。绘制外观仍然在绘制通道网格的材质里，可以是 `spatial` 或 `canvas_item` shader，用 `INSTANCE_CUSTOM` 读粒子的 `CUSTOM`。

## 其他

- `emit_particle()` 手动发射一个粒子，仅 Forward+ 与 Mobile
- `request_particles_process()` 4.4+ 请求额外处理时间。4.7 里参数多了 `process_time_residual`

## 参考

- https://docs.godotengine.org/en/stable/tutorials/3d/particles/index.html
- https://docs.godotengine.org/en/stable/tutorials/2d/particle_systems_2d.html
