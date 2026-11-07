# 2D 光照、HDR 与 glow

2D 光照最短搭法、遮挡与遮罩、法线贴图、HDR 2D 与 glow。

## 光照最短搭法

```ini
[node name="Dark" type="CanvasModulate" parent="."]
color = Color(0.2, 0.22, 0.35, 1)
```

<!-- check: extends PointLight2D -->
```gdscript
func _ready() -> void:
	var g := Gradient.new()
	g.set_color(0, Color.WHITE)
	g.set_color(1, Color(1, 1, 1, 0))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 256
	t.height = 256
	texture = t
	shadow_enabled = true
```

```csharp
public partial class Torch : PointLight2D
{
    public override void _Ready()
    {
        var gradient = new Gradient();
        gradient.SetColor(0, Colors.White);
        gradient.SetColor(1, new Color(1, 1, 1, 0));
        var texture = new GradientTexture2D
        {
            Gradient = gradient,
            Fill = GradientTexture2D.FillEnum.Radial,
            FillFrom = new Vector2(0.5f, 0.5f),
            FillTo = new Vector2(1.0f, 0.5f),
            Width = 256,
            Height = 256,
        };
        Texture = texture;
        ShadowEnabled = true;
    }
}
```

- `PointLight2D` 没有 `texture` 不发光，纹理尺寸决定光的大小
- 编辑器里 `texture` 选 New GradientTexture2D，Fill 设 Radial，不用写代码
- 没有 `CanvasModulate` 压暗时，亮场景里几乎看不出灯
- 一个画布只能有一个 `CanvasModulate`，用 `CanvasLayer` 隔开各自着色
- `DirectionalLight2D` 做日光月光，忽略 `range_item_cull_mask`
- 阴影需要 `LightOccluder2D` 带 `OccluderPolygon2D`
- TileSet 建 Occlusion Layer 后瓦片自带遮挡
- `shadow_enabled` 逐灯收费，只给需要的灯开
- 光照按视口像素分辨率计算，块状光影见 pixel-art.md
- SubViewport 手搓光照、每灯复制节点的做法，改回内置灯

| 匹配 | 决定 |
|---|---|
| `CanvasItem.light_mask` 对灯的 `range_item_cull_mask` | 是否受光 |
| `LightOccluder2D.occluder_light_mask` 对灯的 `shadow_item_cull_mask` | 哪些遮挡体投影 |

法线与高光贴图：

- 精灵纹理换成 `CanvasTexture`，分别指定 diffuse、normal、specular
- 灯的 `height` 控制法线光照角度

## HDR 2D 与 glow

| 步骤 | 做法 |
|---|---|
| 开 HDR 2D | `rendering/viewport/hdr_2d`，仅 Forward+ 与 Mobile，启动时读取 |
| 运行时切换 | 根 `Viewport.use_hdr_2d` |
| 加 glow | `WorldEnvironment`，`Environment.background_mode` 选 canvas，开 `glow_enabled` |
| 精灵发光 | `modulate` 或 `self_modulate` 的 Intensity 大于 1 |
| UI 不发光 | `background_canvas_max_layer` 限制受影响的 CanvasLayer，UI 放更高层 |

- 没开 HDR 2D 时颜色夹到 1，`modulate` 大于 1 无效
- 不开 HDR 2D 也能 glow：`glow_hdr_threshold` 降到 1 以下，但不能逐物体控制
- 开 HDR 2D 后线性空间渲染，颜色 sampler 要写 `source_color`，否则偏灰
- 命中闪白用 shader uniform 配 Tween，不靠 `modulate` 大于 1
- Compatibility 的 glow 是简化实现，`glow_levels/*` `glow_strength` `glow_blend_mode` 无效
