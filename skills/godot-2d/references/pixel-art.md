# 像素风设置

SKILL.md 的像素风一节放不下的细节。先选渲染路线，再配过滤、对齐、导入。

## 两条路线

| 路线 | stretch mode | 画面 | 适合 |
|---|---|---|---|
| 低分辨率整体放大 | `viewport` + scale_mode `integer` | 整个场景先渲到基准分辨率再整数倍放大，精灵不能有亚像素位置和旋转 | 严格像素风，UI 和文字也是像素 |
| 高分辨率渲染加对齐 | `canvas_items` + snap | 按目标分辨率直接渲染，2D 精灵顶点对齐像素，UI 和文字可以是矢量清晰的 | 像素精灵配高清 UI，或 2D 与 3D 混合 |

官方口径：`viewport` 是低分辨率渲染再拉伸，想要精灵亚像素移动或旋转、或需要高分辨率 3D 视口时改用 `canvas_items`。

## 路线一 viewport

```ini
[display]

window/size/viewport_width=640
window/size/viewport_height=360
window/stretch/mode="viewport"
window/stretch/aspect="keep"
window/stretch/scale_mode="integer"

[rendering]

textures/canvas_textures/default_texture_filter=0
```

- 基准 640x360 能整除放大到 1280x720、1920x1080、2560x1440、3840x2160，没有黑边。256x224 到 640x480 是常见基准。
- `display/window/stretch/aspect` 用 `keep` 固定比例带黑边，或 `expand` 支持多种比例，此时 Control 要配锚点。
- `display/window/stretch/scale_mode` 取 `integer` 时窗口小于基准会裁切内容，用 `Window.min_size` 设成基准尺寸。
- `rendering/textures/canvas_textures/default_texture_filter` 值 0 是 Nearest，1 是 Linear，默认 1。项目级默认，单个节点用 `CanvasItem.texture_filter` 覆盖。

## 路线二 canvas_items 加对齐

```ini
[display]

window/stretch/mode="canvas_items"
window/stretch/aspect="expand"

[rendering]

textures/canvas_textures/default_texture_filter=0
2d/snap/snap_2d_transforms_to_pixel=true
```

- `rendering/2d/snap/snap_2d_transforms_to_pixel` 让 CanvasItem 内部取整到整像素，位置仍可带小数但小数不生效。
- `rendering/2d/snap/snap_2d_vertices_to_pixel` 只对最终顶点取整，不改变换。两个设置官方都不建议同开，只开前者。
- 这两个设置只在启动时读取。运行时切换改根 Viewport 的 `Viewport.snap_2d_transforms_to_pixel`。
- 取整的代价是移动不如亚像素平滑，Camera2D 开 `position_smoothing_enabled` 时更明显。
- Control 默认按像素对齐，由 `gui/common/snap_controls_to_pixels` 控制，默认 true。

## 抖动排查

按顺序查：

1. 只有部分物体抖：角色在 `_physics_process` 里动，相机或背景在 idle 帧更新。打开 `physics/common/physics_interpolation`，传送后调 `Node.reset_physics_interpolation`。
2. 相机抖：`Camera2D.process_callback` 默认 `CAMERA2D_PROCESS_IDLE`，跟随物理角色时改 `CAMERA2D_PROCESS_PHYSICS`。
3. 取整与相机平滑同开：官方说明移动会更不平滑，二选一。
4. 显示器刷新率与物理频率不一致：官方 jitter 文档的首要原因，用物理插值处理。

## 导入与过滤

- 导入页 Compress Mode 用 Lossless，2D 默认就是，像素图不要用 VRAM Compressed。
- 2D 里不要给像素图开 mipmap，过滤用 `TEXTURE_FILTER_NEAREST`。
- 同一张图拿去 3D 用时，编辑器会检测到并改成 VRAM Compressed 加 mipmap，像素图会糊。改回 Lossless，细节见 godot-2d-in-3d。

## 精灵与 Control

- `Sprite2D.centered` 默认 true，奇数尺寸贴图的中心落在半像素上会变形。像素风设为 false，或开顶点取整。`AnimatedSprite2D.centered` 同理。
- 位图字体和光栅化动态字体不吃 Camera2D 缩放，zoom 之后会糊。要清晰用 MSDF，或把文字放进不跟随相机的 CanvasLayer。
- 项目默认字体的相关设置在 `gui/theme/default_font_antialiasing`、`gui/theme/default_font_hinting`、`gui/theme/default_font_subpixel_positioning`。像素字体用位图字体，或把 `FontFile.antialiasing` 设为无抗锯齿。

## 光照与阴影分辨率

2D 光照和阴影按 Viewport 像素分辨率计算，不跟贴图像素走，Nearest 过滤改不了它。想要块状光影，在 canvas_item shader 里对 `LIGHT_VERTEX` 和 `SHADOW_VERTEX` 取 `floor()` 对齐网格，见官方 2D lights and shadows 页的 pixel-art 说明。

## HDR 2D

`rendering/viewport/hdr_2d` 为 true 时 2D 用 RGBA16 帧缓冲并在线性空间渲染，可以用 Modulate 的 Intensity 超过 1 驱动 glow，也能减轻渐变色带。canvas_item shader 里作为颜色输入的 sampler 必须带 `source_color` 提示，否则偏灰。只在 Forward+ 与 Mobile 可用，启动时读取，运行时用 `Viewport.use_hdr_2d`。
