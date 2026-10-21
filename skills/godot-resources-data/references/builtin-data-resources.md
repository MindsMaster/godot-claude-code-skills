# 内置数据资源

SKILL.md 的先查内置表指到这里时读。这些资源都能在 Inspector 里编辑，自带曲线编辑器和渐变编辑器。

## 对照

| 自写的东西 | 换成 | 说明 |
|---|---|---|
| 关键帧列表加线性插值的曲线类 | `Curve` | 带切线，编辑器里拖点 |
| 颜色数组加手写 lerp | `Gradient` | 多色标，三种插值模式 |
| shader 里写死的渐变或曲线函数 | `GradientTexture1D` `CurveTexture` | 在 shader 里当 `sampler2D` 采样 |
| 点数组加手算贝塞尔 | `Curve2D` `Curve3D` | `sample_baked` `get_baked_length` |
| 沿路径移动 | `Path2D` + `PathFollow2D` | 改 `progress_ratio` 即可 |
| 属性随时间变化的数据 | `Animation` | 不是只播一次的值才需要，一次性补间用 `Tween` |
| 震屏 地形高度噪声 | `FastNoiseLite` | `NoiseTexture2D` 可直接给 shader |
| 按权重随机 | `RandomNumberGenerator.rand_weighted` | 传权重数组，返回下标 |
| 自绘圆形渐变遮罩 | `GradientTexture2D` | `fill` 选 `FILL_RADIAL` |

## Curve

```gdscript
extends Node

@export var falloff: Curve

func damage_at(distance: float, max_distance: float) -> float:
	var t := clampf(distance / max_distance, 0.0, 1.0)
	return 100.0 * falloff.sample_baked(t)
```

- `sample(offset)` 现算，`sample_baked(offset)` 查预烘焙表，每帧大量采样用后者。`bake_resolution` 默认 100
- 横轴默认 0 到 1。需要别的横轴范围时改 `min_domain` 和 `max_domain`（4.4+），不要自己在外面做除法
- `min_value` `max_value` 限定纵轴，Inspector 里编辑时就有范围
- 曲线是资源，属于共享数据。运行时要改点位先 `duplicate()`

C#：

```csharp
public partial class Falloff : Node
{
    [Export] public Curve Curve { get; set; }

    public float DamageAt(float distance, float maxDistance)
    {
        float t = Mathf.Clamp(distance / maxDistance, 0f, 1f);
        return 100f * Curve.SampleBaked(t);
    }
}
```

## Gradient 与纹理

```gdscript
extends Sprite2D

@export var heat: Gradient

func show_heat(value: float) -> void:
	modulate = heat.sample(clampf(value, 0.0, 1.0))
```

给 shader 用时包成纹理，不要把曲线数据拆成 uniform 数组：

```glsl
uniform sampler2D heat_ramp : repeat_disable;
uniform sampler2D size_curve : repeat_disable;

void fragment() {
	float t = UV.x;
	COLOR = texture(heat_ramp, vec2(t, 0.0));
	float scale = texture(size_curve, vec2(t, 0.0)).r;
}
```

- `GradientTexture1D` 的 `width` 默认 256，决定精度
- shader 写法见 godot-shaders-vfx
- `CurveTexture` 只有红通道，`CurveXYZTexture` 三个通道各一条曲线
- 粒子的 `ParticleProcessMaterial` 的 `scale_curve` `color_ramp` `alpha_curve` 直接吃这些纹理，不用自己写随生命周期变化的逻辑

## Curve2D 与路径

```gdscript
extends Path2D

func point_at(ratio: float) -> Vector2:
	return curve.sample_baked(ratio * curve.get_baked_length())
```

- 巡逻和轨道移动：`PathFollow2D` 作为 `Path2D` 的子节点，每帧 `progress += speed * delta`，`loop` 默认 `true`，超出长度回绕，到头停住设 `false`
- 3D 同理：`Path3D` + `PathFollow3D`，`Curve3D.sample_baked_with_rotation` 取带朝向的变换

## Animation

- 在编辑器里的 `AnimationPlayer` 里做，存成 `AnimationLibrary`，多个角色共用同一个库，做法见 godot-animation
- 代码里只做简单一次性动画用 `create_tween()`，需要按帧 seek 或暂停回放的才用 `Animation`
- 运行时程序化生成 `Animation` 很少需要，`Animation.add_track` 与 `track_insert_key` 存在，但先确认 `Tween.tween_method` 做不到
