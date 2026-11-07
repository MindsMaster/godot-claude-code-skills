# SubViewport、文字与 UI

2D 场景贴进 3D、SubViewport 属性、世界内 UI 输入、Label3D、投影到屏幕的 Control、屏幕叠加 HUD。

## 把 2D 场景贴进 3D

用于 2D 骨骼动画、带粒子或着色器的 2D 特效、Spine 等无 3D 节点的 2D 动画库。纯静态图集直接用 `Sprite3D`。

<!-- check: extends Node3D -->
```gdscript
@onready var _viewport: SubViewport = $SubViewport
@onready var _sprite: Sprite3D = $Sprite3D

func _ready() -> void:
	_viewport.size = Vector2i(128, 128)
	_viewport.disable_3d = true
	_viewport.transparent_bg = true
	_viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	_sprite.texture = _viewport.get_texture()
	_sprite.pixel_size = 1.0 / 32.0
	_sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	_sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_OPAQUE_PREPASS
	_sprite.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
```

```csharp
public partial class ViewportSprite : Node3D
{
    private SubViewport _viewport;
    private Sprite3D _sprite;

    public override void _Ready()
    {
        _viewport = GetNode<SubViewport>("SubViewport");
        _sprite = GetNode<Sprite3D>("Sprite3D");
        _viewport.Size = new Vector2I(128, 128);
        _viewport.Disable3D = true;
        _viewport.TransparentBg = true;
        _viewport.CanvasItemDefaultTextureFilter = Viewport.DefaultCanvasItemTextureFilter.Nearest;
        _sprite.Texture = _viewport.GetTexture();
        _sprite.PixelSize = 1.0f / 32.0f;
        _sprite.TextureFilter = BaseMaterial3D.TextureFilterEnum.Nearest;
        _sprite.AlphaCut = SpriteBase3D.AlphaCutMode.OpaquePrepass;
        _sprite.Billboard = BaseMaterial3D.BillboardModeEnum.FixedY;
    }
}
```

- 角色原点对准视口底边中点
- Sprite3D 的 `offset.y` 设为视口高度的一半，原点落在脚底
- 上下方向与 2D 一致，实测没有翻转

## SubViewport 属性

默认值与行为来自 XML 与 4.7.2 实测。

| 属性 | 默认 | 要点 |
|---|---|---|
| `size` | 512x512 | 渲染目标的像素数，Sprite3D 世界尺寸是 `size × pixel_size` |
| `transparent_bg` | false | 不开时背景是默认清屏色，实测灰色 0.3，贴到 3D 里是一块灰底 |
| `disable_3d` | false | 纯 2D 内容开 true，不创建 3D 渲染 |
| `render_target_update_mode` | `UPDATE_WHEN_VISIBLE` | 贴图在某帧被绘制才重渲，其他取值见下表 |
| `render_target_clear_mode` | `CLEAR_MODE_ALWAYS` | 每帧清屏，其他取值见下表 |
| `canvas_item_default_texture_filter` | 线性 | 不继承项目设置，见下 |
| `snap_2d_transforms_to_pixel` | false | 不继承项目设置 |
| `use_hdr_2d` | false | 不继承项目设置 |
| `size_2d_override` | 0 | 非零时 2D 逻辑尺寸与渲染尺寸分离 |
| `size_2d_override_stretch` | false | 为 true 时 2D 内容拉伸填满渲染目标 |

| `render_target_update_mode` | 行为 |
|---|---|
| `UPDATE_ONCE` | 渲一次后停 |
| `UPDATE_ALWAYS` | 每帧渲 |
| `UPDATE_DISABLED` | 不渲 |
| `UPDATE_WHEN_PARENT_VISIBLE` | 看父节点可见性 |

| `render_target_clear_mode` | 行为 |
|---|---|
| `CLEAR_MODE_NEVER` | 保留上一帧，做拖影或累积 |
| `CLEAR_MODE_ONCE` | 下一帧清一次后转 `CLEAR_MODE_NEVER` |

- 项目默认过滤设成 Nearest 后，新建的 SubViewport 仍是线性，实测
- 像素风给每个 SubViewport 手动设 `canvas_item_default_texture_filter`
- `snap_2d_transforms_to_pixel`、`use_hdr_2d` 同样逐个设
- `size_2d_override` 32x32 配 `size` 64x64 与拉伸：布局按 32x32，输出翻倍
- 此时 Sprite3D 的 `pixel_size` 减半才保持世界尺寸
- 开 `use_hdr_2d` 后 `ViewportTexture` 是线性编码，直接显示偏暗
- 需要时用 `Image.linear_to_srgb` 转换
- 同一 SubViewport 摆多个角色，各 Sprite3D 用 `region_rect` 取自己一块
- 每个 SubViewport 都是一次独立渲染

| ViewportTexture 陷阱 | 做法 |
|---|---|
| 场景根未 ready 时取到的数据不对 | 代码里用 `get_texture` 取 |
| 编辑器里指定的 `viewport_path` 找不到 | 路径相对场景根，不相对使用它的节点 |
| 高分辨率的随场景实例化卡顿 | 预先创建 |
| `Decal`、`Light3D`、`PointLight2D` 不能直接用 | `get_image` 建 `ImageTexture`，较慢，不每帧做 |

## 转发输入到世界内 UI

- Control 面板渲染进 SubViewport，贴到四边形上
- 点击时射线求交，换算成视口坐标，`Viewport.push_input` 送进 SubViewport
- 照官方 GUI in 3D 演示项目的射线与坐标换算写

## Label3D

<!-- check: extends Label3D -->
```gdscript
func _ready() -> void:
	text = "Lv 12"
	font_size = 32
	pixel_size = 0.01
	outline_size = 8
	billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	alpha_cut = Label3D.ALPHA_CUT_DISCARD
```

```csharp
public partial class LevelLabel : Label3D
{
    public override void _Ready()
    {
        Text = "Lv 12";
        FontSize = 32;
        PixelSize = 0.01f;
        OutlineSize = 8;
        Billboard = BaseMaterial3D.BillboardModeEnum.FixedY;
        AlphaCut = AlphaCutMode.Discard;
    }
}
```

| 属性 | 默认 |
|---|---|
| `shaded` | false |
| `cast_shadow` | 关 |
| `pixel_size` | 0.005 |
| `font_size` | 32 |
| `outline_size` | 12 |
| `alpha_cut` | `ALPHA_CUT_DISABLED` |

- 多个带描边的 Label3D 重叠会排序错乱
- `ALPHA_CUT_DISCARD` 缓解排序，字边不如平滑
- `ALPHA_CUT_OPAQUE_PREPASS` 保留平滑并可投影，仍有部分排序问题
- 远处变糊：字体开 mipmap，或用 MSDF
- 更清晰：`font_size` 调大，`pixel_size` 调小
- `fixed_size` 为 true 时屏幕大小不随距离变，仍受 fov 或正交 `size` 影响
- `Label3D` 不继承 UI 主题，字体用字体子资源设置

| 需求 | 用 |
|---|---|
| 多数情况 | `Label3D` |
| 自定义 shader、字形有厚度、自带投影 | `TextMesh`，只支持动态字体 |
| 整套 Control 主题、按钮交互 | 投影到屏幕的 Control |

## 投影到屏幕的 Control

血条、名牌用相机把 3D 点投到 2D，放在 `CanvasLayer` 下的 Control 上。

<!-- check: extends Control -->
```gdscript
@export var target: Node3D

func _process(_delta: float) -> void:
	var camera := get_viewport().get_camera_3d()
	if camera == null or target == null:
		return
	var world_pos := target.global_position
	visible = not camera.is_position_behind(world_pos)
	position = camera.unproject_position(world_pos) - size * 0.5
```

```csharp
public partial class NamePlate : Control
{
    [Export] public Node3D Target { get; set; }

    public override void _Process(double delta)
    {
        Camera3D camera = GetViewport().GetCamera3D();
        if (camera == null || Target == null)
        {
            return;
        }
        Vector3 worldPos = Target.GlobalPosition;
        Visible = !camera.IsPositionBehind(worldPos);
        Position = camera.UnprojectPosition(worldPos) - Size * 0.5f;
    }
}
```

- 不会被 3D 几何遮挡，需要时用射线判断
- 分辨率和宽高比变化在脚本里处理，缩放不随距离变
- 要被遮挡、随距离缩放的，用 `Sprite3D` 或 `Label3D`

## 屏幕叠加 HUD

- HUD、暂停菜单放 `CanvasLayer` 下的 Control，不受 3D 相机影响
- `layer` 大的在上
- `display/window/stretch/mode` 取 `canvas_items`：UI 按分辨率缩放，3D 原生分辨率
- 取 `viewport`：3D 也低分辨率，UI 与 3D 一起放大
- 单独降 3D 分辨率用 `Viewport.scaling_3d_scale`，UI 不受影响
