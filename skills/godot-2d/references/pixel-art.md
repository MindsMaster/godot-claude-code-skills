# 像素风设置

两条渲染路线的完整设置、抖动排查、导入、精灵与字体、光影分辨率、HDR 2D。

## 两条路线

| 路线 | stretch mode | 画面 | 适合 |
|---|---|---|---|
| 低分辨率整体放大 | `viewport` 加 scale_mode `integer` | 先渲到基准分辨率再整数倍放大，精灵无亚像素位置和旋转 | 严格像素风，UI 和文字也是像素 |
| 高分辨率渲染加对齐 | `canvas_items` 加 snap | 按目标分辨率渲染，精灵顶点对齐像素，UI 文字矢量清晰 | 像素精灵配高清 UI，或 2D 与 3D 混合 |

- 要精灵亚像素移动、旋转，或高分辨率 3D 视口，用 `canvas_items`

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

- 基准 640x360 整除放大到 720p、1080p、1440p、2160p，无黑边
- 常见基准在 256x224 到 640x480 之间
- `display/window/stretch/aspect` 用 `keep` 固定比例带黑边
- 用 `expand` 支持多种比例，此时 Control 要配锚点
- `display/window/stretch/scale_mode` 为 `integer` 时窗口小于基准会裁切
- 用 `Window.min_size` 设成基准尺寸
- `rendering/textures/canvas_textures/default_texture_filter` 0 是 Nearest，默认 1 Linear
- 单个节点用 `CanvasItem.texture_filter` 覆盖

## 路线二 canvas_items 加对齐

```ini
[display]

window/stretch/mode="canvas_items"
window/stretch/aspect="expand"

[rendering]

textures/canvas_textures/default_texture_filter=0
2d/snap/snap_2d_transforms_to_pixel=true
```

| 设置 | 作用 |
|---|---|
| `rendering/2d/snap/snap_2d_transforms_to_pixel` | CanvasItem 内部取整，位置可带小数但不生效 |
| `rendering/2d/snap/snap_2d_vertices_to_pixel` | 只对最终顶点取整，不改变换 |
| `gui/common/snap_controls_to_pixels` | Control 按像素对齐，默认 true |

- 两个 snap 官方不建议同开，只开前者
- 两个 snap 只在启动时读取，运行时改根 `Viewport.snap_2d_transforms_to_pixel`
- 取整后移动不如亚像素平滑，相机开平滑时更明显

## 抖动排查

按顺序查：

| 现象 | 原因与做法 |
|---|---|
| 只有部分物体抖 | 角色在物理帧动，相机或背景在 idle 帧；开 `physics/common/physics_interpolation` |
| 相机抖 | `Camera2D.process_callback` 默认 `CAMERA2D_PROCESS_IDLE`，跟物理角色改 `CAMERA2D_PROCESS_PHYSICS` |
| 取整与相机平滑同开 | 官方说明会更不平滑，二选一 |
| 刷新率与物理频率不一致 | 官方 jitter 文档的首要原因，用物理插值 |

- 开物理插值后传送调 `Node.reset_physics_interpolation`

## 导入与过滤

- 导入页 Compress Mode 用 Lossless，2D 默认就是
- 像素图不用 VRAM Compressed，不开 mipmap
- 过滤用 `TEXTURE_FILTER_NEAREST`
- 同一张图拿去 3D 用时编辑器改成 VRAM Compressed 加 mipmap，会糊
- 改回 Lossless，细节见 godot-2d-in-3d

## 精灵与字体

- `Sprite2D.centered` 默认 true，奇数尺寸贴图中心落在半像素会变形
- 像素风设为 false，或开取整，`AnimatedSprite2D.centered` 同理
- 位图字体和光栅化字体不吃 Camera2D 缩放，zoom 后会糊
- 要清晰用 MSDF，或把文字放进不跟随相机的 CanvasLayer
- 像素字体用位图字体，或 `FontFile.antialiasing` 设为无抗锯齿
- 项目默认字体设置：`gui/theme/default_font_antialiasing`
- 另有 `gui/theme/default_font_hinting`、`gui/theme/default_font_subpixel_positioning`

## 光照与阴影分辨率

- 2D 光照和阴影按 Viewport 像素分辨率计算，不跟贴图像素走
- Nearest 过滤改不了光影分辨率
- 块状光影：canvas_item shader 里对 `LIGHT_VERTEX` 和 `SHADOW_VERTEX` 取 `floor()`
- 见官方 2D lights and shadows 页的 pixel-art 说明

## HDR 2D

- `rendering/viewport/hdr_2d` 为 true 时用 RGBA16 帧缓冲，线性空间渲染
- Modulate 的 Intensity 超过 1 可驱动 glow，也减轻渐变色带
- 颜色输入的 sampler 必须带 `source_color`，否则偏灰
- 只在 Forward+ 与 Mobile 可用，启动时读取
- 运行时用 `Viewport.use_hdr_2d`
