# godot-ui

## SKILL.md `set_anchors_and_offsets_preset`

<!-- check: prepare -->
```gdscript
var f := FileAccess.open("res://hud.tscn", FileAccess.WRITE)
f.store_string("""[gd_scene format=3]

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
""")
f.close()
```

```gdscript
await frames(2)
expect(node.anchor_left == 0.5 and node.anchor_right == 0.5, "CENTER_BOTTOM 水平锚点居中")
expect(node.anchor_top == 1.0 and node.anchor_bottom == 1.0, "CENTER_BOTTOM 垂直锚点贴底")
expect(is_equal_approx(node.offset_bottom, -32.0), "底边留 32 边距")

expect(Control.SIZE_EXPAND_FILL == 3 and Control.MOUSE_FILTER_IGNORE == 2 and Control.PRESET_FULL_RECT == 15, "场景片段里的数值对应枚举")
var hud := (load("res://hud.tscn") as PackedScene).instantiate() as Control
root.add_child(hud)
await frames(2)
var bar := hud.get_node("Margin/Row/HealthBar") as ProgressBar
expect(hud.mouse_filter == Control.MOUSE_FILTER_IGNORE, "HUD 根节点 IGNORE")
expect(not bar.show_percentage, "血条关掉百分比")
expect(bar.get_combined_minimum_size().x >= 240.0, "custom_minimum_size 是下限")
expect(hud.get_node("Margin").theme_type_variation == &"HudMargin", "variation 名写进了节点")
hud.free()

var defaults := {
	"Control": Control.MOUSE_FILTER_STOP, "Panel": Control.MOUSE_FILTER_STOP, "PanelContainer": Control.MOUSE_FILTER_STOP,
	"ColorRect": Control.MOUSE_FILTER_STOP, "Button": Control.MOUSE_FILTER_STOP, "ProgressBar": Control.MOUSE_FILTER_STOP,
	"RichTextLabel": Control.MOUSE_FILTER_STOP,
	"Container": Control.MOUSE_FILTER_PASS, "HBoxContainer": Control.MOUSE_FILTER_PASS, "VBoxContainer": Control.MOUSE_FILTER_PASS,
	"GridContainer": Control.MOUSE_FILTER_PASS, "MarginContainer": Control.MOUSE_FILTER_PASS, "CenterContainer": Control.MOUSE_FILTER_PASS,
	"ScrollContainer": Control.MOUSE_FILTER_PASS, "TextureRect": Control.MOUSE_FILTER_PASS, "TextureProgressBar": Control.MOUSE_FILTER_PASS,
	"Label": Control.MOUSE_FILTER_IGNORE, "NinePatchRect": Control.MOUSE_FILTER_IGNORE,
}
for type_name: String in defaults:
	var c := ClassDB.instantiate(type_name) as Control
	expect(c.mouse_filter == defaults[type_name], "%s 的 mouse_filter 默认值" % type_name)
	c.free()

var label := Label.new()
var button := Button.new()
expect(label.focus_mode == Control.FOCUS_NONE and button.focus_mode == Control.FOCUS_ALL, "Label NONE Button ALL")
expect(node.pivot_offset == Vector2.ZERO, "pivot_offset 默认左上角")
node.position = Vector2.ZERO
node.size = Vector2(100, 40)
node.scale = Vector2(2, 2)
expect(node.get_transform().origin == Vector2.ZERO, "默认绕左上角缩放，原点不动")
node.pivot_offset_ratio = Vector2(0.5, 0.5)
expect(node.get_transform().origin == Vector2(-50, -20), "pivot_offset_ratio 0.5 绕中心缩放")
node.scale = Vector2.ONE
root.add_child(label)
label.text = "a fairly long line of text"
label.custom_minimum_size = Vector2(1, 0)
await frames(2)
expect(label.get_combined_minimum_size().x > 1.0, "文字内容撑大最小尺寸")
label.custom_minimum_size = Vector2(900, 0)
await frames(2)
expect(label.get_combined_minimum_size().x == 900.0, "custom_minimum_size 比内容大时生效")
label.free()
button.free()

var wide := ProgressBar.new()
var tex_bar := TextureProgressBar.new()
expect(wide.show_percentage and is_equal_approx(wide.step, 0.01), "ProgressBar 默认显示百分比 step 0.01")
expect(is_equal_approx(tex_bar.step, 1.0), "TextureProgressBar step 默认 1.0")
tex_bar.value = 0.4
expect(tex_bar.value == 0.0, "step 1.0 时小数被吞掉")
tex_bar.step = 0.01
tex_bar.value = 0.4
expect(is_equal_approx(tex_bar.value, 0.4), "step 0.01 后保留小数")
wide.free()
tex_bar.free()
expect(ProjectSettings.get_setting("display/window/stretch/mode") == "disabled", "stretch mode 未设置时 disabled")
expect(ProjectSettings.get_setting("display/window/stretch/aspect") == "keep", "stretch aspect 未设置时 keep")
root.content_scale_factor = 1.5
expect(is_equal_approx(root.content_scale_factor, 1.5), "运行时设界面缩放")
root.content_scale_factor = 1.0
expect(DisplayServer.get_display_safe_area() is Rect2i, "安全区是 Rect2i")

var box := HBoxContainer.new()
var child := Button.new()
box.add_child(child)
root.add_child(box)
await frames(2)
var sorted_position := child.position
child.position = Vector2(300, 300)
child.size = Vector2(999, 999)
box.queue_sort()
await frames(2)
expect(child.position == sorted_position and child.size.x < 999.0, "Container 重排会重置子节点的 position 和 size")
box.free()

var local_theme := Theme.new()
local_theme.set_color(&"font_color", &"Label", Color.RED)
var themed := Control.new()
themed.theme = local_theme
var direct := Label.new()
var plain := Node.new()
var behind := Label.new()
themed.add_child(direct)
themed.add_child(plain)
plain.add_child(behind)
root.add_child(themed)
await frames(2)
expect(direct.get_theme_color(&"font_color") == Color.RED, "局部 Theme 传给 Control 后代")
expect(behind.get_theme_color(&"font_color") != Color.RED, "遇到其他类型节点就断开")
expect(direct.get_theme_color(&"font_color", &"Label") == Color.RED, "按类型名取主题颜色")
themed.free()
```

## SKILL.md `func set_team_color`

```gdscript
await frames(2)
var shared := node.get_theme_stylebox(&"fill") as StyleBoxFlat
var other := ProgressBar.new()
root.add_child(other)
var default_fill := other.get_theme_stylebox(&"fill") as StyleBoxFlat
var before := default_fill.bg_color
expect(default_fill == shared, "同类控件共享 Theme 里同一份 StyleBox")
node.set_team_color(Color.RED)
expect((node.get_theme_stylebox(&"fill") as StyleBoxFlat).bg_color == Color.RED, "本节点填充变红")
expect(other.get_theme_stylebox(&"fill") == default_fill and default_fill.bg_color == before, "共享样式没被改")
expect(node.get_theme_stylebox(&"fill") != default_fill, "本节点持有独立副本")
default_fill.bg_color = Color.GREEN
var third := ProgressBar.new()
expect((third.get_theme_stylebox(&"fill") as StyleBoxFlat).bg_color == Color.GREEN, "不 duplicate 直接改会改到共享样式")
third.free()
default_fill.bg_color = before
other.queue_free()
```

## SKILL.md `StyleBoxFlat.new()`

```gdscript
await frames(2)
var box := node.get_theme_stylebox(&"panel") as StyleBoxFlat
expect(box != null, "panel 样式被覆盖成 StyleBoxFlat")
expect(box.bg_color == Color(0.1, 0.1, 0.12, 0.9), "背景色")
expect(box.corner_radius_top_left == 8 and box.corner_radius_bottom_right == 8, "set_corner_radius_all")
expect(box.border_width_left == 2 and box.border_width_bottom == 2, "set_border_width_all")
expect(box.content_margin_left == 12.0 and box.content_margin_top == 12.0, "set_content_margin_all")
expect(node.get_combined_minimum_size().x >= 24.0, "内容边距计入最小尺寸")
```

## SKILL.md `func set_health`

```gdscript
await frames(2)
(node.get_node("Front") as ProgressBar).value = 100.0
(node.get_node("Chip") as ProgressBar).value = 100.0
node.set_health(30.0)
expect((node.get_node("Front") as ProgressBar).value == 30.0, "前景条立刻到位")
expect((node.get_node("Chip") as ProgressBar).value == 100.0, "残影条先不动")
await frames(12)
expect((node.get_node("Chip") as ProgressBar).value == 100.0, "0.4 秒内残影条仍停着")
await frames(60)
expect(is_equal_approx((node.get_node("Chip") as ProgressBar).value, 30.0), "残影条追上前景条")
node.set_health(80.0)
node.set_health(50.0)
await frames(60)
expect(is_equal_approx((node.get_node("Chip") as ProgressBar).value, 50.0), "连续受伤只留最后一个 Tween")
```

## SKILL.md `NOTIFICATION_TRANSLATION_CHANGED`

<!-- check: prepare -->
```gdscript
var f := FileAccess.open("res://items.csv", FileAccess.WRITE)
f.store_string("en,?plural,fr,ru\n?pluralrule,,nplurals=2; plural=(n >= 2);,\n%d item,%d items,%d objet,%d предмет\n,,%d objets,%d предмета\n,,,%d предметов\n")
f.close()
```

<!-- check: setup -->
```gdscript
TranslationServer.set_locale("en")
TranslationServer.add_translation(load("res://items.fr.translation"))
TranslationServer.add_translation(load("res://items.ru.translation"))
```

```gdscript
await frames(2)
expect(node.text == "0 items", "没有对应语言的翻译时回退到原文")
node._count = 1
TranslationServer.set_locale("fr")
await frames(2)
expect(node.text == "1 objet", "法语 1 个")
node._count = 5
TranslationServer.set_locale("ru")
await frames(2)
expect(node.text == "5 предметов", "俄语 5 个")
node._count = 2
TranslationServer.set_locale("ru")
node.notification(Node.NOTIFICATION_TRANSLATION_CHANGED)
expect(node.text == "2 предмета", "俄语 2 个")
node._count = 5
TranslationServer.set_locale("fr")
await frames(2)
expect(node.text == "5 objets", "法语复数")
expect(node.tr_n("ITEM_COUNT_ONE", "ITEM_COUNT_MANY", 3) == "ITEM_COUNT_MANY", "用键名当单复数文本时缺翻译返回键名")
expect(node.tr_n("ITEM_COUNT_ONE", "ITEM_COUNT_MANY", 1) == "ITEM_COUNT_ONE", "n 为 1 时返回单数键名")
```

## SKILL.md `func _key_text`

<!-- check: setup -->
```gdscript
InputMap.add_action(&"interact")
var key := InputEventKey.new()
key.physical_keycode = KEY_E
InputMap.action_add_event(&"interact", key)
var zh := Translation.new()
zh.locale = "en"
zh.add_message("PROMPT_INTERACT", "Press {key} to interact")
TranslationServer.set_locale("en")
TranslationServer.add_translation(zh)
```

```gdscript
await frames(2)
expect(node.text == "Press E to interact", "命名占位符替换成键名")
expect(node._key_text(&"interact") == "E", "物理键取 as_text_physical_keycode")
var ev := InputMap.action_get_events(&"interact")[0] as InputEventKey
expect(ev.as_text() == "E - Physical", "as_text 对物理键带后缀")
expect(ev.as_text_keycode().is_empty() or ev.as_text_keycode() == "(unset)", "物理键绑定时 as_text_keycode 没有键名")
var pad := InputEventJoypadButton.new()
pad.button_index = JOY_BUTTON_A
expect(pad.as_text().length() > 20, "手柄 as_text 是长描述")
InputMap.add_action(&"jump")
expect(node._key_text(&"jump") == "", "没绑键盘事件时返回空串")

var probe_script := GDScript.new()
probe_script.source_code = """
extends Control
var events: Array[String] = []
var accept: bool = false

func _input(_e: InputEvent) -> void:
	events.append("input")

func _gui_input(_e: InputEvent) -> void:
	events.append("gui")
	if accept:
		accept_event()

func _shortcut_input(_e: InputEvent) -> void:
	events.append("shortcut")

func _unhandled_key_input(_e: InputEvent) -> void:
	events.append("unhandled_key")

func _unhandled_input(_e: InputEvent) -> void:
	events.append("unhandled")
""".dedent()
probe_script.reload()
var probe := Control.new()
probe.set_script(probe_script)
probe.size = Vector2(200, 200)
probe.focus_mode = Control.FOCUS_ALL
root.add_child(probe)
probe.grab_focus()
await frames(2)
var press := InputEventKey.new()
press.pressed = true
press.keycode = KEY_A
press.physical_keycode = KEY_A
root.push_input(press)
expect(probe.events == ["input", "gui", "shortcut", "unhandled_key", "unhandled"], "键盘事件顺序 %s" % [probe.events])
probe.events.clear()
probe.accept = true
root.push_input(press)
expect(probe.events == ["input", "gui"], "_gui_input 里 accept_event 后到不了 unhandled %s" % [probe.events])
probe.events.clear()
probe.accept = false
var click := InputEventMouseButton.new()
click.button_index = MOUSE_BUTTON_LEFT
click.pressed = true
click.position = Vector2(10, 10)
click.global_position = click.position
root.push_input(click)
expect(probe.events == ["input", "gui"], "STOP 吃掉点击 %s" % [probe.events])
probe.events.clear()
var wheel := InputEventMouseButton.new()
wheel.button_index = MOUSE_BUTTON_WHEEL_UP
wheel.pressed = true
wheel.position = Vector2(10, 10)
wheel.global_position = wheel.position
expect(probe.mouse_force_pass_scroll_events, "mouse_force_pass_scroll_events 默认 true")
root.push_input(wheel)
expect(probe.events == ["input", "gui", "unhandled"], "STOP 放行滚轮 %s" % [probe.events])
probe.events.clear()
probe.mouse_filter = Control.MOUSE_FILTER_PASS
root.push_input(click)
expect(probe.events == ["input", "gui", "unhandled"], "PASS 没人处理时继续往后走 %s" % [probe.events])
probe.events.clear()
probe.mouse_filter = Control.MOUSE_FILTER_IGNORE
root.push_input(click)
expect(probe.events == ["input", "unhandled"], "IGNORE 不收事件也不挡 %s" % [probe.events])
probe.free()

var start := Button.new()
var other := Button.new()
root.add_child(start)
root.add_child(other)
start.grab_focus.call_deferred()
await frames(2)
expect(start.has_focus(), "call_deferred 抓焦点")
other.mouse_entered.connect(other.grab_focus)
other.mouse_entered.emit()
expect(other.has_focus() and not start.has_focus(), "mouse_entered 连 grab_focus")
start.hide()
other.hide()
expect(not other.has_focus(), "控件隐藏会丢焦点")
other.show()
expect(not other.has_focus(), "再显示不会自动拿回焦点")
other.grab_focus()
expect(root.gui_get_focus_owner() == other, "gui_get_focus_owner 取当前焦点")
start.free()
other.free()
```

## references/localization.md `print(atr`

<!-- check: prepare -->
```gdscript
var f := FileAccess.open("res://apples.csv", FileAccess.WRITE)
f.store_string("en,?plural,fr,ru\n?pluralrule,,nplurals=2; plural=(n >= 2);,\nThere is %d apple,There are %d apples,Il y a %d pomme,Есть %d яблоко\n,,Il y a %d pommes,Есть %d яблока\n,,,Есть %d яблок\n")
f.close()
f = FileAccess.open("res://letters.csv", FileAccess.WRITE)
f.store_string("en,?context,fr\nLetter,Alphabet,Lettre\nLetter,Message,Courrier\n")
f.close()
```

<!-- check: setup -->
```gdscript
var en := Translation.new()
en.locale = "en"
en.add_message("MENU_START", "Start")
en.add_message("MENU_QUIT", "Quit")
en.add_message("PICKED_UP", "Picked up {item}")
en.add_message("ITEM_SWORD", "Sword")
en.add_message("Close", "Near", "Distance")
TranslationServer.add_translation(en)
for path: String in ["apples.fr", "apples.ru", "letters.fr"]:
	TranslationServer.add_translation(load("res://%s.translation" % path))
TranslationServer.set_locale("en")
```

```gdscript
await frames(2)
expect(node.tr("MENU_START") == "Start", "tr 取键对应的译文")
expect(node.tr("PICKED_UP").format({item = node.tr("ITEM_SWORD")}) == "Picked up Sword", "命名占位符替换")
expect(node.tr("Close", "Distance") == "Near", "context 区分同形词")
expect(node.tr("Close") == "Close", "不带 context 查不到")
expect(node.tr("NOT_IN_TABLE") == "NOT_IN_TABLE", "找不到翻译返回原键")
expect(TranslationServer.translate("MENU_START") == "Start", "静态上下文用 TranslationServer.translate")
expect(node.tr_n("There is %d apple", "There are %d apples", 3) % 3 == "There are 3 apples", "英文回退原文")
expect(TranslationServer.translate_plural("There is %d apple", "There are %d apples", 1) % 1 == "There is 1 apple", "translate_plural 单数")
expect(node.atr("MENU_QUIT") == "Quit", "atr 翻译")
node.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
expect(node.atr("MENU_QUIT") == "MENU_QUIT", "auto_translate_mode 关掉后 atr 不翻译")
expect(node.tr("MENU_QUIT") == "Quit", "tr 不受 auto_translate_mode 影响")
node.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_INHERIT

TranslationServer.set_locale("fr")
expect(node.tr_n("There is %d apple", "There are %d apples", 1) % 1 == "Il y a 1 pomme", "法语 1")
expect(node.tr_n("There is %d apple", "There are %d apples", 0) % 0 == "Il y a 0 pomme", "pluralrule n>=2 时 0 是单数")
expect(node.tr_n("There is %d apple", "There are %d apples", 2) % 2 == "Il y a 2 pommes", "法语 2")
expect(node.tr("Letter", "Message") == "Courrier", "CSV ?context 列")
expect(node.tr("Letter", "Alphabet") == "Lettre", "CSV ?context 列另一行")
expect(node.tr("Letter") == "Letter", "带 context 的行不带 context 查不到")
TranslationServer.set_locale("ru")
expect(node.tr_n("There is %d apple", "There are %d apples", 1) % 1 == "Есть 1 яблоко", "俄语 1")
expect(node.tr_n("There is %d apple", "There are %d apples", 3) % 3 == "Есть 3 яблока", "俄语 3")
expect(node.tr_n("There is %d apple", "There are %d apples", 11) % 11 == "Есть 11 яблок", "俄语 11")
expect(TranslationServer.get_plural_rules("ru").contains("nplurals=3"), "俄语内置三种复数形式")
TranslationServer.set_locale("en")

var keyed := Label.new()
keyed.text = "MENU_START"
var literal := Label.new()
literal.text = "Start"
var raw_key := Label.new()
raw_key.text = "MENU_START"
raw_key.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
root.add_child(keyed)
root.add_child(literal)
root.add_child(raw_key)
await frames(2)
expect(is_equal_approx(keyed.get_minimum_size().x, literal.get_minimum_size().x), "Label 的 text 填键名会自动翻译")
expect(raw_key.get_minimum_size().x > literal.get_minimum_size().x, "auto_translate_mode 关掉后显示键名")
keyed.free()
literal.free()
raw_key.free()

TranslationServer.pseudolocalization_enabled = true
expect(node.tr("MENU_START") != "Start", "伪本地化改写译文")
expect(node.tr_n("There is %d apple", "There are %d apples", 3).contains("%d"), "百分号占位符保留")
expect(not node.tr("PICKED_UP").format({item = "Sword"}).contains("Sword"), "花括号占位符被改写 format 替换不到")
TranslationServer.pseudolocalization_enabled = false
expect(node.tr("MENU_START") == "Start", "关掉后恢复")
expect(ProjectSettings.get_setting("internationalization/pseudolocalization/expansion_ratio") == 0.0, "默认不拉长")
expect(ProjectSettings.get_setting("internationalization/pseudolocalization/double_vowels") == false, "默认不重复元音")
for setting: String in ["use_pseudolocalization", "fake_bidi", "skip_placeholders"]:
	expect(ProjectSettings.has_setting("internationalization/pseudolocalization/" + setting), "项目设置 " + setting)
for setting: String in ["locale/test", "locale/fallback", "locale/translations", "locale/translation_remaps", "locale/translations_pot_files", "locale/include_text_server_data", "rendering/root_node_layout_direction"]:
	expect(ProjectSettings.has_setting("internationalization/" + setting), "项目设置 " + setting)
expect(ProjectSettings.get_setting("internationalization/locale/fallback") == "en", "fallback 默认 en")
expect(TranslationServer.format_number("123", "ar") != "123", "format_number 转阿拉伯数字")

var ctrl := Control.new()
expect(ctrl.localize_numeral_system, "localize_numeral_system 默认 true")
expect(ctrl.layout_direction == Control.LAYOUT_DIRECTION_INHERITED, "layout_direction 默认继承")
ctrl.free()
```

## references/localization.md `tr("MENU_TITLE")`

<!-- check: setup -->
```gdscript
var en := Translation.new()
en.locale = "en"
en.add_message("MENU_TITLE", "Title")
var fr := Translation.new()
fr.locale = "fr"
fr.add_message("MENU_TITLE", "Titre")
TranslationServer.add_translation(en)
TranslationServer.add_translation(fr)
TranslationServer.set_locale("en")
```

```gdscript
expect(node.text == "Title", "进树时通知也到一次")
TranslationServer.set_locale("fr")
await frames(2)
expect(node.text == "Titre", "切语言后重设")
TranslationServer.set_locale("en")
await frames(2)
expect(node.text == "Title", "切回来")
```

## references/localization.md `func apply_language`

<!-- check: setup -->
```gdscript
var zh := Translation.new()
zh.locale = "zh_CN"
zh.add_message("HELLO", "你好")
TranslationServer.add_translation(zh)
```

```gdscript
node.apply_language("zh_CN")
expect(TranslationServer.get_locale() == "zh_CN", "存档里的语言直接生效")
expect(node.tr("HELLO") == "你好", "翻译跟着切")
node.apply_language("")
var system := OS.get_locale_language()
expect(system.length() == 2 or system.length() == 3, "系统语言是 2 或 3 位代码")
expect(TranslationServer.get_locale().begins_with(system), "空串跟随系统")
node.apply_language("automatic")
expect(TranslationServer.get_locale().begins_with(system), "automatic 跟随系统")
node.apply_language("en-US")
expect(TranslationServer.get_locale() == "en_US", "set_locale 规整 en-US")
node.apply_language("zh")
expect(node.tr("HELLO") == "你好", "只有 zh 的系统语言会匹配 zh_CN")
node.apply_language("zh_TW")
expect(node.tr("HELLO") == "你好", "zh_TW 没有自己的翻译时落到 zh_CN")
expect(TranslationServer.compare_locales("zh", "zh_CN") == 10, "compare_locales 范围 0 到 10")
expect(TranslationServer.compare_locales("en", "fr") == 0, "无关语言得 0")
expect(TranslationServer.get_loaded_locales() == PackedStringArray(["zh_CN"]), "已加载的语言")
expect(TranslationServer.get_locale_name("zh_CN") == "Chinese, China", "get_locale_name 是英文名")

var rtl := HBoxContainer.new()
var first := Button.new()
var second := Button.new()
rtl.add_child(first)
rtl.add_child(second)
root.add_child(rtl)
await frames(2)
expect(first.position.x < second.position.x, "英文下按钮从左到右")
TranslationServer.set_locale("ar")
await frames(2)
expect(rtl.is_layout_rtl(), "阿拉伯语 RTL")
expect(first.position.x > second.position.x, "容器自动镜像")
rtl.layout_direction = Control.LAYOUT_DIRECTION_LTR
await frames(2)
expect(not rtl.is_layout_rtl() and first.position.x < second.position.x, "layout_direction 覆盖镜像")
rtl.free()
TranslationServer.set_locale("en")
```

## references/richtext.md `_on_meta_clicked`

```gdscript
await frames(2)
expect(node.bbcode_enabled, "脚本里开了 BBCode")
expect(node.get_parsed_text() == "接受任务", "url 标签不显示在文本里")
expect(not node.context_menu_enabled and not node.selection_enabled, "context_menu_enabled 与 selection_enabled 默认 false")
expect(not node.threaded, "threaded 默认 false")
var got: Array = []
node.meta_clicked.connect(func(meta: Variant) -> void: got.append(meta))
node.size = Vector2(300, 60)
await frames(2)
var motion := InputEventMouseMotion.new()
motion.position = Vector2(4, 4)
motion.global_position = motion.position
root.push_input(motion)
var press := InputEventMouseButton.new()
press.button_index = MOUSE_BUTTON_LEFT
press.pressed = true
press.position = Vector2(4, 4)
press.global_position = press.position
root.push_input(press)
var release := press.duplicate() as InputEventMouseButton
release.pressed = false
root.push_input(release)
expect(got == ["quest:12"], "点击 url 发出 String 参数 %s" % [got])
node.meta_clicked.disconnect(node._on_meta_clicked)
got.clear()
node.clear()
node.push_meta(42)
node.add_text("item")
node.pop()
await frames(2)
root.push_input(motion)
root.push_input(press)
root.push_input(release)
expect(got == [42], "push_meta 可以传非 String %s" % [got])

node.text = "[lb]url]"
expect(node.get_parsed_text() == "[url]", "[lb] 转义左括号")
node.text = "[b]a[/b]"
node.append_text("[i]b[/i]")
expect(node.get_parsed_text() == "ab", "append_text 解析 BBCode")
node.clear()
expect(node.get_parsed_text() == "", "clear 清空")
```

## references/richtext.md `func say`

```gdscript
await frames(2)
node.bbcode_enabled = true
node.say("[b]hello[/b] world", 20.0)
expect(node.get_total_character_count() == 11, "总字数不计标签")
expect(node.visible_ratio == 0.0, "开头全隐藏")
await frames(20)
expect(node.visible_ratio > 0.0 and node.visible_ratio < 1.0, "打字机进行中")
node.say("[b]hello[/b] world", 20.0)
await frames(90)
expect(node.visible_ratio == 1.0, "11 个字 20 字每秒 0.55 秒内打完")
```

## references/richtext.md `RichTextGhost`

```gdscript
var label := RichTextLabel.new()
label.bbcode_enabled = true
label.size = Vector2(300, 100)
label.text = "[ghost freq=5 span=10]text[/ghost]"
root.add_child(label)
await frames(2)
expect(label.get_parsed_text() == "[ghost freq=5 span=10]text[/ghost]", "没注册的标签原样显示")
label.install_effect(RichTextGhost.new())
await frames(2)
expect(label.get_parsed_text() == "text", "install_effect 之后标签生效")

var counted := GDScript.new()
counted.source_code = """
@tool
extends RichTextGhost
var calls: int = 0

func _process_custom_fx(char_fx: CharFXTransform) -> bool:
	calls += 1
	return super(char_fx)
""".dedent()
counted.reload()
var effect := counted.new() as RichTextEffect
expect(effect.bbcode == "ghost", "bbcode 成员决定标签名")
var second := RichTextLabel.new()
second.bbcode_enabled = true
second.size = Vector2(300, 100)
second.custom_effects = [effect]
second.text = "[ghost]text[/ghost]"
root.add_child(second)
await frames(10)
expect(effect.get("calls") > 0, "每个字形都调用 _process_custom_fx")
expect(second.get_parsed_text() == "text", "custom_effects 数组注册")
second.free()
label.free()
```
