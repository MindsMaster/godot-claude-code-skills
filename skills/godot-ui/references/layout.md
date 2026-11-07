# 布局细节

Container 排版限制与多分辨率设置。

## 容器限制

Container 在子节点变化和 `queue_sort()` 时重排。

| 需求 | 做法 |
|---|---|
| 动画子节点 | 动 `scale` `modulate` `rotation`，`position` `size` 会被排序覆盖 |
| 必须动位置 | 动画节点外包一层普通 Control |
| 按中心缩放 | `pivot_offset_ratio = Vector2(0.5, 0.5)` 4.6+ |
| 4.5 及以前按中心缩放 | `resized` 信号里设 `pivot_offset = size / 2.0` |
| autowrap 的 Label 不被压成 1 像素宽 | 宽度来自 `custom_minimum_size.x` 或 `SIZE_EXPAND_FILL` |
| 气泡短句收窄、长句到上限换行 | `custom_maximum_size.x` 4.7+ |
| ScrollContainer 内容随滚动区变宽 | 内容子节点设 `SIZE_EXPAND` |
| 手风琴 | FoldableContainer 4.5+ 配 FoldableGroup |
| 折叠标题栏加按钮 | `add_title_bar_control` |

## 多分辨率

`display/window/stretch/mode`：

| 值 | 效果 | 适用 |
|---|---|---|
| `disabled` | 不缩放，1 单位 1 像素，aspect 无效 | 工具类应用 |
| `canvas_items` | 2D 与 UI 以目标分辨率直接渲染，文字清晰 | 大多数游戏，4.7 起新建项目默认 |
| `viewport` | 先渲染到基准尺寸再整体缩放 | 像素风 |

`display/window/stretch/aspect`：

| 值 | 效果 |
|---|---|
| `keep` | 保持比例，留黑边，UI 不用考虑比例 |
| `keep_width` | 宽固定，更高的屏幕多露出下方，HUD 常用 |
| `keep_height` | 高固定，更宽的屏幕多露出右侧，横版卷轴常用 |
| `expand` | 宽高都可能变大，4.7 起新建项目默认，UI 须用 anchors 贴边 |
| `ignore` | 拉伸变形，一般不用 |

- 基准尺寸：`display/window/size/viewport_width` 与 `display/window/size/viewport_height`
- 未设置时 mode 为 `disabled`，aspect 为 `keep`
- 像素风：`viewport` 配 `keep` 或 `expand`
- 整数缩放：`display/window/stretch/scale_mode` 设 `integer`
- 整数缩放下窗口小于基准尺寸会裁切，设 `Window.min_size`
- `display/window/stretch/scale` 是全局倍率
- 玩家的界面缩放选项：运行时设 `get_window().content_scale_factor`
- 除 `keep` 外，HUD 靠 anchors 和 Container 贴边
- 刘海圆角：`DisplayServer.get_display_safe_area()` 取安全区，设根 MarginContainer 边距
