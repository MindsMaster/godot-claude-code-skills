---
name: godot-ui
description: Godot 4 UI 与 HUD 做法，Control 布局 Container anchors size_flags，项目级 Theme 与 theme type variation，StyleBox，血条 ProgressBar TextureProgressBar，RichTextLabel BBCode，多分辨率 stretch mode aspect，本地化 tr() CSV PO TranslationServer，按键提示 InputMap，手柄焦点导航 focus_neighbor grab_focus，mouse_filter 吃点击，_gui_input。在写菜单 HUD 对话框 血条 设置界面 本地化 分辨率适配 UI 导航时用。UI layout theme localization health bar focus navigation.
---

# Godot UI

在场景里用 Container 和 anchors 搭 Control 界面，用项目级 Theme 统一外观，用引擎自带的 ProgressBar、RichTextLabel、翻译系统和焦点导航。不管 2D 游戏世界里的节点摆放（见 `godot-2d`），不管输入动作本身的定义（见 `godot-input`），不管动画选型（见 `godot-animation`）。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 界面摆放 | 场景里的 Container 加 anchors preset | 代码里按 1920x1080 写死 `position` 和 `size` |
| 边距 | MarginContainer | 手算偏移 |
| 竖排横排 | VBoxContainer HBoxContainer | 逐个设 `position.y` |
| 网格 | GridContainer 的 `columns` | 双重循环算坐标 |
| 自动换行排列 | HFlowContainer VFlowContainer | 手写换行逻辑 |
| 保持宽高比 | AspectRatioContainer | `_process` 里改 `size` |
| 滚动列表 | ScrollContainer | 手写裁剪与拖动 |
| 折叠面板 | FoldableContainer 4.5+ | Button 加手动 `visible` |
| 面板背景 | PanelContainer 或 Panel 加 StyleBoxFlat | ColorRect 叠 ColorRect |
| 血条 经验条 | ProgressBar 或 TextureProgressBar | 改 ColorRect 的 `size.x` |
| 全局字体颜色按钮样式 | 项目级 Theme | 到处 `add_theme_*_override` |
| 同类控件多种样式 | theme type variation | 每个节点单独覆盖 |
| 富文本 打字机效果 | RichTextLabel 的 BBCode 与 `visible_ratio` | 多个 Label 拼接 |
| 玩家可见文本 | `tr()` 加翻译表 | 字符串硬编码 |
| 按键提示 | `InputMap.action_get_events` | 写死 "E" |
| 手柄菜单导航 | focus_neighbor 与 `grab_focus()` | 自己监听方向键切换高亮 |
| 分辨率适配 | `display/window/stretch/mode` | 运行时按窗口大小手动缩放根节点 |

## 布局

HUD 与菜单在场景编辑器里搭。根节点是铺满屏幕的 Control，用 `Full Rect` preset，其下用 Container 嵌套。

```ini
[node name="Hud" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
mouse_filter = 2

[node name="Margin" type="MarginContainer" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
theme_type_variation = &"HudMargin"

[node name="Row" type="HBoxContainer" parent="Margin"]
layout_mode = 2

[node name="HealthBar" type="ProgressBar" parent="Margin/Row"]
custom_minimum_size = Vector2(240, 24)
layout_mode = 2
show_percentage = false
```

要点：

- 根 Control 的 `mouse_filter = 2` 即 `MOUSE_FILTER_IGNORE`，否则整屏 HUD 吃掉所有点击，见陷阱
- Container 的子节点由 Container 决定位置，子节点只表达需求：`custom_minimum_size` 是下限，`size_flags_*` 是分配方式
- `size_flags_horizontal = 3` 即 `Control.SIZE_EXPAND_FILL`，占满剩余空间。空 Control 加 EXPAND_FILL 当弹簧，把左右两组控件推开
- `size_flags_stretch_ratio` 在多个 EXPAND 子节点间分配比例
- 脚本里要摆浮动控件（跟随角色的血条，弹出提示）才用代码，仍然用 preset 而不是裸坐标：

```gdscript
extends Control

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM, Control.PRESET_MODE_MINSIZE, 32)
```

`set_anchors_preset` 只改锚点不改偏移，通常用 `set_anchors_and_offsets_preset`。`PRESET_FULL_RECT` 铺满，`PRESET_TOP_WIDE` 贴顶拉宽。

### 容器的限制

- Container 在子节点变化与 `queue_sort()` 时重排。直接 Tween 子节点的 `position` 或 `size` 会被下一次排序覆盖。要动画就 Tween `scale` `modulate` `rotation`，或把动画节点包一层普通 Control
- `scale` 的中心是 `pivot_offset`，默认左上角。缩放按钮设 `pivot_offset_ratio = Vector2(0.5, 0.5)` 4.6+，4.5 及以前在 `resized` 信号里设 `pivot_offset = size / 2.0`
- Label 开 `autowrap_mode` 后宽度要来自 `custom_minimum_size.x` 或 `SIZE_EXPAND_FILL`
- ScrollContainer 的内容子节点设 `SIZE_EXPAND` 才会随滚动区变宽
- FoldableContainer 4.5+ 配 FoldableGroup 做手风琴，标题栏按钮用 `add_title_bar_control`

## Theme

外观统一放一个 Theme 资源，在项目设置里挂成全局默认：

```ini
[gui]

theme/custom="res://ui/theme/main.tres"
theme/custom_font="res://ui/fonts/main.ttf"
```

- 对应 `gui/theme/custom` 和 `gui/theme/custom_font`。场景里任何 Control 无需设 `theme` 就继承它
- 局部换主题：给某个 Control 设 `theme`，它的 Control 和 Window 后代都继承，遇到其他类型的节点就断开
- 同一类控件的多种样式用 theme type variation：在 Theme 里新建类型如 `DangerButton`，Base Type 选 `Button`，节点上设 `theme_type_variation`。项目级 Theme 里的变体才会出现在 Inspector 下拉里
- 颜色字号间距都在 Theme 编辑器里改，脚本只读：`get_theme_color(&"font_color", &"Label")`
- 代码生成的 UI 同样继承 Theme，不用逐个 `add_theme_*_override`

只有单个节点的一次性差异才用 override，如血条的填充颜色随阵营变：

```gdscript
extends ProgressBar

func set_team_color(color: Color) -> void:
	var fill := get_theme_stylebox(&"fill").duplicate() as StyleBoxFlat
	fill.bg_color = color
	add_theme_stylebox_override(&"fill", fill)
```

`duplicate()` 必须有，否则改的是 Theme 里共享的那份 StyleBox，所有同类控件一起变色。

### StyleBox

StyleBoxFlat 做纯色圆角描边阴影，StyleBoxTexture 做九宫格贴图，StyleBoxEmpty 去掉默认样式如按钮焦点框，StyleBoxLine 做分隔线。

```gdscript
extends PanelContainer

func _ready() -> void:
	var box := StyleBoxFlat.new()
	box.bg_color = Color(0.1, 0.1, 0.12, 0.9)
	box.set_corner_radius_all(8)
	box.set_border_width_all(2)
	box.set_content_margin_all(12.0)
	add_theme_stylebox_override(&"panel", box)
```

复用的样式放进 Theme 资源，代码构造只用于运行时才知道参数的样式。

## 血条

ProgressBar 做纯色条，TextureProgressBar 做贴图条或环形条。样式在 Theme 里改 `fill` 和 `background`。

- ProgressBar 默认 `show_percentage = true`，血条要关掉
- TextureProgressBar 的 `step` 默认 1.0，ProgressBar 的 `step` 是 0.01。用 Tween 做平滑，`step` 太大会出现阶梯，设成 0.01 或更小
- TextureProgressBar 的 `fill_mode` 有径向，做冷却环和圆形血球不用 shader
- 贴图要拉伸用 `nine_patch_stretch` 加 `stretch_margin_*`

缓动与受伤残影：

```gdscript
extends Control

@onready var _front: ProgressBar = %Front
@onready var _chip: ProgressBar = %Chip

var _tween: Tween

func set_health(value: float) -> void:
	_front.value = value
	if _tween:
		_tween.kill()
	_tween = create_tween()
	_tween.tween_interval(0.4)
	_tween.tween_property(_chip, "value", value, 0.3).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
```

前景条与残影条是同位置叠放的两个 ProgressBar，残影条在下，填充色用浅色，前景条的 `background` 设 StyleBoxEmpty 否则盖住残影条。数字跳动用 `tween_method`，见 `godot-animation`。

## RichTextLabel

- `bbcode_enabled = true` 后写 `[b]` `[color=red]` `[url]` `[img]` 等标签。常用标签清单在 `references/richtext.md`
- `visible_ratio` 或 `visible_characters` 做打字机效果，用 Tween 驱动 `visible_ratio` 从 0 到 1
- `fit_content = true` 让高度随内容变，放在 VBox 里时常用
- `[url]` 默认点击无反应，连 `meta_clicked` 信号做词条链接与提示
- 自定义效果继承 RichTextEffect，`bbcode` 成员定义标签名，`_process_custom_fx` 改 `CharFXTransform`，示例见 `references/richtext.md`
- 带自定义效果的 RichTextLabel 持续每帧处理，不用时隐藏

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
| `keep` | 保持比例，两侧或上下黑边。UI 不用考虑比例，代价是黑边 |
| `keep_width` | 宽固定，更高的屏幕多露出下方内容。HUD 常用 |
| `keep_height` | 高固定，更宽的屏幕多露出右侧内容。横版卷轴常用 |
| `expand` | 宽高都可能变大，4.7 起新建项目默认。UI 必须用 anchors 贴边 |
| `ignore` | 拉伸变形，一般不用 |

- 基准尺寸设在 `display/window/size/viewport_width` 与 `display/window/size/viewport_height`。未设置时 mode 是 `disabled`，aspect 是 `keep`
- 像素风用 `viewport` 配 `keep` 或 `expand`，再加 `display/window/stretch/scale_mode = "integer"`，窗口小于基准尺寸会裁切，配合 `Window.min_size`
- `display/window/stretch/scale` 是全局倍率。给玩家的界面缩放选项在运行时设 `get_window().content_scale_factor`
- 除 `keep` 外 HUD 的位置要靠 anchors 和 Container 跟随屏幕边缘，写死坐标必然错位
- 手机刘海与圆角用 `DisplayServer.get_display_safe_area()` 取安全区，再设根 MarginContainer 的边距

## 本地化

玩家可见文本一律进翻译表，包括按钮文字、提示、地点名。表格式与导入见 `references/localization.md`。

- Label Button 等控件的 `text` 填翻译键，如 `MENU_START`，运行时自动翻译，不用写 `tr()`
- 脚本里拼接的文本用 `tr("KEY")`。带变量用命名占位符 `tr("PICKED_UP").format({item = name})`，占位符位置由译者调整
- 复数用 `tr_n("APPLE", "APPLES", count)`，不要自己写 `if count == 1`。语言的复数形式不止两种
- 同一英文词不同含义用第二个参数 context：`tr("Close", "Distance")`
- 不该翻译的文本，如玩家名，把节点的 `auto_translate_mode` 设成 `Node.AUTO_TRANSLATE_MODE_DISABLED`
- 切换语言：`TranslationServer.set_locale("zh_CN")`，选择存进设置文件，启动时读出来再调
- `tr()` 返回的文本在语言切换后不会自动更新，要在 `_notification` 里响应 `NOTIFICATION_TRANSLATION_CHANGED` 重设
- 开发期开 `internationalization/pseudolocalization/use_pseudolocalization` 检查漏翻与文本溢出，运行时用 `TranslationServer.pseudolocalization_enabled` 切换

```gdscript
extends Label

var _count: int = 0

func _notification(what: int) -> void:
	if what == NOTIFICATION_TRANSLATION_CHANGED:
		text = tr_n("ITEM_COUNT_ONE", "ITEM_COUNT_MANY", _count) % _count
```

## 按键提示

提示文本从 InputMap 取，玩家改键后自动跟随：

```gdscript
extends Label

@export var action: StringName = &"interact"

func _ready() -> void:
	text = tr("PROMPT_INTERACT").format({key = _key_text(action)})

func _key_text(action_name: StringName) -> String:
	for event: InputEvent in InputMap.action_get_events(action_name):
		if event is InputEventKey:
			return (event as InputEventKey).as_text_physical_keycode()
	return ""
```

- 绑定的是 `physical_keycode` 时用 `as_text_physical_keycode()`，绑定 `keycode` 时用 `as_text_keycode()`。`InputEvent.as_text()` 对物理键会返回 "E - Physical" 这类带后缀的文本
- 手柄事件的 `as_text()` 是长描述，不适合直接显示，按 `InputEventJoypadButton.button_index` 映射到自己的图标
- 键盘与手柄提示的切换：在 `_input` 里看最近一个事件是 `InputEventJoypadButton` 还是 `InputEventKey`，记成当前设备类型，据此选图标集

## 焦点导航与手柄

- 场景启动后必须有一个控件拿焦点，否则方向键和手柄无反应：`$StartButton.grab_focus.call_deferred()`
- 菜单面板显示时对第一个按钮 `grab_focus()`。控件被隐藏会丢焦点，面板重新显示要再抓一次
- 内置动作 `ui_up` `ui_down` `ui_left` `ui_right` `ui_accept` `ui_cancel` `ui_focus_next` 驱动焦点移动，不要在游戏逻辑里复用这些动作
- 默认的邻居是引擎猜的，复杂界面在 Inspector 的 Focus 分类里显式设 `focus_neighbor_left` `focus_neighbor_right` `focus_neighbor_top` `focus_neighbor_bottom` `focus_next` `focus_previous`
- `focus_mode`：`FOCUS_ALL` 可点击也可导航，`FOCUS_CLICK` 只能点击，`FOCUS_NONE` 不可聚焦。Label 默认 NONE，Button 默认 ALL
- 整棵子树禁止聚焦：`focus_behavior_recursive = Control.FOCUS_BEHAVIOR_DISABLED` 4.5+
- 鼠标悬停高亮也要聚焦时：`mouse_entered.connect(grab_focus)`
- 弹窗关闭后焦点还给触发它的按钮，打开前存 `get_viewport().gui_get_focus_owner()`
- ScrollContainer 的 `follow_focus = true` 让聚焦项自动滚入视野

## 输入与点击

UI 的事件顺序：`_input` 然后 GUI（`_gui_input`）然后 `_shortcut_input` 然后 `_unhandled_key_input` 然后 `_unhandled_input`。

- Control 内部交互（拖动，点击自绘区域）用 `_gui_input`，处理完调 `accept_event()`
- 游戏世界的点击与按键放 `_unhandled_input`。UI 已处理的事件到不了这里，不用再手写 "鼠标是否在 UI 上" 判断
- 全屏键位（暂停，截图）放 `_unhandled_input` 或 `_shortcut_input`，不要放 `_process` 轮询
- 按钮上的快捷键用 `BaseButton.shortcut`，不用另写 `_input`

### mouse_filter

默认值：Control Panel PanelContainer ColorRect Button ProgressBar RichTextLabel 是 `MOUSE_FILTER_STOP`，各种 Container TextureRect TextureProgressBar 是 `MOUSE_FILTER_PASS`，Label NinePatchRect 是 `MOUSE_FILTER_IGNORE`。

- STOP 吃掉事件，下面的节点和 `_unhandled_input` 都收不到。滚轮事件例外，`mouse_force_pass_scroll_events` 默认 true 会放行
- PASS 收到后没调 `accept_event()` 就冒泡给父 Control，冒到 STOP 为止，没人处理才继续往后走
- IGNORE 完全透明，不收事件也不挡下层
- 铺满屏幕的 HUD 根节点，装饰用的 ColorRect TextureRect Panel，叠在按钮上的图标，一律改成 IGNORE
- 整棵子树关掉鼠标输入：`mouse_behavior_recursive = Control.MOUSE_BEHAVIOR_DISABLED` 4.5+

## 无障碍

4.7+ 的 AccessibilityServer 为每个节点自动生成无障碍元素，不用手动调 `create_element`。`accessibility/general/accessibility_support` 默认 0，检测到读屏软件才处理更新。只有图标的按钮和自绘控件设 `accessibility_name` 与 `accessibility_description` 4.5+。

## 陷阱

- 代码里 `new Label()` 加 `new ColorRect()` 按像素写死位置，`expand` 与不同比例屏幕下错位。改成场景加 Container
- 在 Container 的子节点上设 `size` 或 `position` 无效，下次排序就被重置，改 `custom_minimum_size` 与 `size_flags`
- `custom_minimum_size` 只能放大最小尺寸，文字内容也会撑大它
- 手写 `.tscn` 实例化 HUD 并给 `@export var player: Player` 赋 `NodePath`，节点头漏写 `node_paths=PackedStringArray("player")` 则运行期为 `null`，信号连不上。写法见 godot-scene-architecture 的 references/lifecycle.md
- 血条用 ColorRect 改 `size.x`：没有背景，没有圆角，改 Theme 又得改代码。用 ProgressBar
- 每关 `new Theme()` 或到处 `add_theme_*_override`：改一个字号要翻遍代码。用项目级 Theme 与 type variation
- 改 `get_theme_stylebox()` 的返回值前不 `duplicate()`，会改到共享样式
- 把按键名写死在文本里，改键后提示就错了
- 只在 `_ready` 里 `tr()` 一次，切换语言后文本不更新
- 显示玩家名的 Label 没关 `auto_translate_mode`，名字与翻译键同名时会被替换
- 手柄菜单不给初始焦点，或隐藏再显示后不重新 `grab_focus()`
- 用 `ui_accept` 之类内置动作做玩法，菜单打开时会重复触发

## 参考

- `references/localization.md`：CSV 与 PO 导入，注册翻译，复数与上下文，TranslationServer，伪本地化，字体回退
- `references/richtext.md`：BBCode 标签速查，自定义 RichTextEffect，打字机
- [GUI 文档](https://docs.godotengine.org/en/stable/tutorials/ui/index.html)
- [本地化](https://docs.godotengine.org/en/stable/tutorials/i18n/index.html)
- [键盘与手柄导航](https://docs.godotengine.org/en/stable/tutorials/ui/gui_navigation.html)
