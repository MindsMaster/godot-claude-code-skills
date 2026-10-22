# godot-editor-tooling

## SKILL.md `class_name SpawnRule`

```gdscript
var changed_count: Array[int] = [0]
var list_changed: Array[int] = [0]
node.changed.connect(func() -> void: changed_count[0] += 1)
node.property_list_changed.connect(func() -> void: list_changed[0] += 1)
var interval_usage := func() -> int:
	for info: Dictionary in node.get_property_list():
		if info["name"] == "interval":
			return info["usage"]
	return -1
expect(interval_usage.call() == PROPERTY_USAGE_NO_EDITOR, "ONCE 时 interval 只隐藏")
expect(PROPERTY_USAGE_NO_EDITOR == PROPERTY_USAGE_STORAGE, "NO_EDITOR 数值上等于 STORAGE")
node.interval = 2.5
expect(changed_count[0] == 1, "interval setter 发 changed")
ResourceSaver.save(node, "user://rule.tres")
expect(FileAccess.get_file_as_string("user://rule.tres").contains("interval = 2.5"), "隐藏的属性照常存盘")
DirAccess.remove_absolute("user://rule.tres")
node.kind = SpawnRule.Kind.TIMED
expect(list_changed[0] == 1, "kind setter 通知属性列表变化")
expect(changed_count[0] == 2, "kind setter 发 changed")
expect(int(interval_usage.call()) & PROPERTY_USAGE_EDITOR != 0, "TIMED 时 interval 显示")
node.kind = SpawnRule.Kind.ONCE
expect(interval_usage.call() == PROPERTY_USAGE_NO_EDITOR, "切回 ONCE 又隐藏")
```

## SKILL.md `position.x += 10.0 * delta`

<!-- run: mode editor -->

<!-- check: prepare -->
```gdscript
var file := FileAccess.open("res://plain.gd", FileAccess.WRITE)
file.store_string("class_name Plain\nextends Resource\n\nconst LIMIT: int = 5\nenum Kind { A, B }\nstatic var cache: int = 9\nstatic var loose: Variant = 9\nvar hp: int = 1\n\nfunc heal() -> int:\n\treturn 7\n\nstatic func twice(x: int) -> int:\n\treturn x * 2\n")
file.close()
var tres := FileAccess.open("res://thing.tres", FileAccess.WRITE)
tres.store_string("[gd_resource type=\"Resource\" load_steps=2 format=3]\n\n[ext_resource type=\"Script\" path=\"res://plain.gd\" id=\"1\"]\n\n[resource]\nscript = ExtResource(\"1\")\nhp = 3\n")
tres.close()
```

```gdscript
expect(Engine.is_editor_hint(), "编辑器里 is_editor_hint 为 true")
var rule := SpawnRule.new()
var other := SpawnRule.new()
node.rule = rule
expect(rule.changed.is_connected(node.queue_redraw), "换入资源时连 changed")
node.rule = other
expect(not rule.changed.is_connected(node.queue_redraw), "换资源时断开旧的")
expect(other.changed.is_connected(node.queue_redraw), "新资源连上")
node.rule = null
expect(not other.changed.is_connected(node.queue_redraw), "置空时断开")
await frames(10)
expect(is_zero_approx(node.position.x), "is_editor_hint 挡住游戏逻辑")

var thing: Resource = load("res://thing.tres")
expect(not thing.get_script().can_instantiate(), "加载出来的非 tool 脚本资源是占位实例")
expect(thing.get("hp") == null, "占位实例读不到成员变量")
var made := Plain.new()
expect(made.heal() == 7 and made.hp == 1, "new 造的实例方法和成员可用")
var attached := Resource.new()
attached.set_script(load("res://plain.gd"))
expect(attached.get("hp") == null, "set_script 挂上的也是占位实例")
expect(Plain.twice(4) == 8, "静态方法可调")
expect(Plain.LIMIT == 5 and Plain.Kind.B == 1, "常量和枚举可读")
expect(Plain.cache == 0 and Plain.loose == null, "静态变量不执行初始化")
```

## SKILL.md `class_name WaveTable`

```gdscript
var names := func() -> PackedStringArray:
	var found := PackedStringArray()
	for info: Dictionary in node.get_property_list():
		if str(info["name"]).begins_with("wave_") and str(info["name"]).ends_with("_count") and info["name"] != "wave_count":
			expect(int(info["usage"]) & PROPERTY_USAGE_STORAGE != 0 and info["type"] == TYPE_INT, "动态属性带存盘标志")
			found.append(info["name"])
	return found
expect(names.call() == PackedStringArray(["wave_0_count", "wave_1_count", "wave_2_count"]), "三波三个属性")
expect(node.get("wave_2_count") == 12 and node.get("wave_1_count") == 8, "_get 读 counts")
expect(node.get("missing") == null, "_get 对其他属性返回 null")
node.set("wave_1_count", 20)
expect(node.counts[1] == 20, "_set 写 counts")
var changed: Array[int] = [0]
node.property_list_changed.connect(func() -> void: changed[0] += 1)
node.wave_count = 5
expect(changed[0] == 1, "wave_count 改变通知属性列表")
expect(node.counts.size() == 5 and names.call().size() == 5, "wave_count 重建属性")
node.wave_count = 99
expect(node.wave_count == 20 and node.counts.size() == 20, "wave_count 夹在 20")
node.wave_count = 0
expect(node.wave_count == 1 and node.counts.size() == 1, "wave_count 至少 1")
node.wave_count = 3
node.set("wave_0_count", 7)
node.set("wave_1_count", 9)
node.set("wave_2_count", 11)
ResourceSaver.save(node, "user://waves.tres")
var text := FileAccess.get_file_as_string("user://waves.tres")
expect(text.contains("wave_1_count = 9"), "动态属性存盘")
var loaded: Resource = ResourceLoader.load("user://waves.tres", "", ResourceLoader.CACHE_MODE_IGNORE)
expect(loaded.wave_count == 3 and loaded.counts == PackedInt32Array([7, 9, 11]), "读回动态属性")
DirAccess.remove_absolute("user://waves.tres")
```

## SKILL.md `func snap_to_target`

```gdscript
expect(node._get_configuration_warnings() == PackedStringArray(["target 未设置"]), "target 为空时有警告")
var target := Node2D.new()
EditorInterface.get_base_control().add_child(target)
target.position = Vector2(30.0, 40.0)
node.target = target
expect(node._get_configuration_warnings().is_empty(), "设置 target 后警告消失")
var button: Dictionary = {}
for info: Dictionary in node.get_property_list():
	if info["name"] == "snap_action":
		button = info
expect(button["hint"] == PROPERTY_HINT_TOOL_BUTTON and button["hint_string"] == "Snap To Target,Reload", "tool 按钮的提示")
expect(get_undo_redo() == EditorInterface.get_editor_undo_redo(), "插件的 get_undo_redo 是同一个对象")
node.position = Vector2(-5.0, 5.0)
var before := node.global_position
node.snap_action.call()
expect(node.global_position.is_equal_approx(target.global_position), "按钮把节点移到 target")
var history := EditorInterface.get_editor_undo_redo().get_history_undo_redo(EditorInterface.get_editor_undo_redo().get_object_history_id(node))
expect(history.has_undo() and history.get_current_action_name() == "Snap To Target", "动作已提交")
history.undo()
expect(node.global_position.is_equal_approx(before), "撤销回到原位")
history.redo()
expect(node.global_position.is_equal_approx(target.global_position), "重做再次移动")
target.free()
```

## references/editor-recipes.md `pass`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://addons/items")
var cfg := FileAccess.open("res://addons/items/plugin.cfg", FileAccess.WRITE)
cfg.store_string("[plugin]\n\nname=\"Items\"\ndescription=\"物品数据工具\"\nauthor=\"team\"\nversion=\"1.0\"\nscript=\"plugin.gd\"\n")
cfg.close()
DirAccess.copy_absolute("res://s0.gd", "res://addons/items/plugin.gd")
```

```gdscript
expect(node.is_inside_tree(), "插件节点进树")
expect(not EditorInterface.is_plugin_enabled("items"), "启用前未启用")
EditorInterface.set_plugin_enabled("items", true)
expect(EditorInterface.is_plugin_enabled("items"), "按骨架启用成功")
expect(ProjectSettings.get_setting("editor_plugins/enabled", PackedStringArray()).has("res://addons/items/plugin.cfg"), "启用写入 editor_plugins/enabled")
EditorInterface.set_plugin_enabled("items", false)
expect(not EditorInterface.is_plugin_enabled("items"), "可以停用")
```

## references/editor-recipes.md `add_dock(_dock)`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://addons/items")
var panel := VBoxContainer.new()
panel.name = "ItemsPanel"
var title := Label.new()
title.name = "Title"
panel.add_child(title)
title.owner = panel
var packed := PackedScene.new()
packed.pack(panel)
ResourceSaver.save(packed, "res://addons/items/items_panel.tscn")
panel.free()
```

```gdscript
var dock: EditorDock = node._dock
await frames(2)
expect(dock.is_inside_tree(), "dock 已加入编辑器")
expect(dock.title == "Items" and dock.default_slot == EditorDock.DOCK_SLOT_RIGHT_UL, "标题和默认位置")
expect(dock.get_child(0).name == "ItemsPanel", "面板场景挂进 dock")
expect(dock.available_layouts == (EditorDock.DOCK_LAYOUT_VERTICAL | EditorDock.DOCK_LAYOUT_FLOATING), "默认只允许垂直和浮动")
node.free()
await frames(2)
expect(not is_instance_valid(dock), "退出时 dock 被释放")
```

## references/editor-recipes.md `func _enable_plugin`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://addons/items")
var file := FileAccess.open("res://addons/items/items_service.gd", FileAccess.WRITE)
file.store_string("extends Node\n")
file.close()
```

```gdscript
var key := "autoload/" + node.AUTOLOAD_NAME
expect(not ProjectSettings.has_setting(key), "启用前没有 autoload")
node._enable_plugin()
var value: String = ProjectSettings.get_setting(key, "")
expect(value.begins_with("*") and ResourceUID.uid_to_path(value.trim_prefix("*")) == "res://addons/items/items_service.gd", "启用时登记带星号的 autoload " + value)
node._disable_plugin()
expect(not ProjectSettings.has_setting(key), "停用时移除 autoload")
```

## references/editor-recipes.md `func _has_main_screen`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://addons/items")
var panel := VBoxContainer.new()
panel.name = "MainScreen"
var packed := PackedScene.new()
packed.pack(panel)
ResourceSaver.save(packed, "res://addons/items/main_screen.tscn")
panel.free()
```

```gdscript
var screen: Control = node._screen
expect(screen.get_parent() == EditorInterface.get_editor_main_screen(), "面板挂在主屏幕容器下")
expect(not screen.visible, "进树后先隐藏")
expect(screen.size_flags_vertical == Control.SIZE_EXPAND_FILL, "纵向 EXPAND_FILL")
expect(node._has_main_screen() and node._get_plugin_name() == "Items", "主屏幕标签页名")
expect(node._get_plugin_icon() != null, "取得编辑器内置图标")
node._make_visible(true)
expect(screen.visible, "_make_visible(true) 显示")
node.free()
await frames(2)
expect(not is_instance_valid(screen), "退出时面板被释放")
```

## references/editor-recipes.md `NOTIFICATION_THEME_CHANGED`

```gdscript
var theme := EditorInterface.get_editor_theme()
var accent := theme.get_color("accent_color", "Editor")
expect(node._title.has_theme_color_override("font_color"), "进树后按编辑器主题着色")
expect(node._title.get_theme_color("font_color") == accent and node.get_theme_color("accent_color", "Editor") == accent, "控件取到的主题色等于编辑器主题色")
for color_name in ["base_color", "accent_color", "success_color", "warning_color", "error_color", "font_color", "disabled_font_color"]:
	expect(theme.has_color(color_name, "Editor"), "Editor 主题有颜色 " + color_name)
	expect(theme.get_color_list("Editor").has(color_name), "get_color_list 列出 " + color_name)
for icon_name in ["Add", "Remove", "Reload", "Save", "Warning", "Error", "Node", "Folder", "Search", "Edit", "Play"]:
	expect(theme.has_icon(icon_name, "EditorIcons"), "EditorIcons 有图标 " + icon_name)
var icon := node.get_theme_icon("Reload", "EditorIcons")
expect(node.custom_minimum_size.y == icon.get_height() * 2.0 and icon.get_height() > 0, "最小高度是图标高度的 2 倍")
expect(EditorInterface.get_editor_scale() > 0.0, "编辑器缩放可读")
```

## references/editor-recipes.md `add_tool_menu_item("Validate Items"`

```gdscript
var settings := EditorInterface.get_editor_settings()
expect(settings.has_shortcut("items/validate"), "快捷键已注册")
var found: Array[Callable] = []
for popup: Node in EditorInterface.get_base_control().find_children("*", "PopupMenu", true, false):
	var menu := popup as PopupMenu
	for i in menu.item_count:
		if menu.get_item_text(i) == "Validate Items":
			found.append(menu.get_item_metadata(i))
expect(found.size() == 1, "工具菜单里有一个 Validate Items")
expect(found[0].get_object() == node and found[0].get_method() == &"_validate", "菜单项绑定 _validate")
var wrong := InputEventKey.new()
wrong.keycode = KEY_B
wrong.ctrl_pressed = true
wrong.shift_pressed = true
wrong.pressed = true
var right := InputEventKey.new()
right.keycode = KEY_V
right.ctrl_pressed = true
right.shift_pressed = true
right.pressed = true
expect(not settings.is_shortcut("items/validate", wrong), "别的键不匹配")
expect(settings.is_shortcut("items/validate", right), "Ctrl+Shift+V 匹配")
get_viewport().push_input(wrong)
expect(not get_viewport().is_input_handled(), "不匹配的键不处理")
get_viewport().push_input(right)
expect(get_viewport().is_input_handled(), "匹配的键被标记为已处理")
node.free()
found.clear()
for popup: Node in EditorInterface.get_base_control().find_children("*", "PopupMenu", true, false):
	var menu := popup as PopupMenu
	for i in menu.item_count:
		if menu.get_item_text(i) == "Validate Items":
			found.append(menu.get_item_metadata(i))
expect(found.is_empty(), "退出时移除菜单项")
var palette := EditorInterface.get_command_palette()
palette.add_command("Validate Items", "items/validate", Callable())
palette.remove_command("items/validate")
```

## references/editor-recipes.md `func _popup_menu(paths: PackedStringArray)`

<!-- check: prepare -->
```gdscript
ResourceSaver.save(Resource.new(), "res://a.tres")
ResourceSaver.save(Resource.new(), "res://b.tres")
var text := FileAccess.open("res://c.txt", FileAccess.WRITE)
text.store_string("c")
text.close()
var capture := FileAccess.open("res://capture.gd", FileAccess.WRITE)
capture.store_string("extends Logger\n\nvar lines: Array[String] = []\n\nfunc _log_message(message: String, _error: bool) -> void:\n\tlines.append(message)\n")
capture.close()
```

```gdscript
var capture: Logger = load("res://capture.gd").new()
OS.add_logger(capture)
add_context_menu_plugin(EditorContextMenuPlugin.CONTEXT_SLOT_FILESYSTEM, node)
var dock := EditorInterface.get_file_system_dock()
dock.navigate_to_path("res://a.tres")
await frames(5)
var tree: Tree
for candidate: Node in dock.find_children("*", "Tree", true, false):
	var root := (candidate as Tree).get_root()
	if root != null and (candidate as Tree).get_selected() != null and (candidate as Tree).get_selected().get_text(0) == "a.tres":
		tree = candidate as Tree
expect(tree != null, "文件系统树里选中了 a.tres")
tree.item_mouse_selected.emit(Vector2.ZERO, MOUSE_BUTTON_RIGHT)
await frames(2)
var menu: PopupMenu
var menu_id := -1
for candidate: Node in dock.find_children("*", "PopupMenu", true, false):
	var popup := candidate as PopupMenu
	for i in popup.item_count:
		if popup.get_item_text(i) == "Validate Resource":
			menu = popup
			menu_id = popup.get_item_id(i)
expect(menu != null, "右键 .tres 文件出现 Validate Resource")
menu.id_pressed.emit(menu_id)
menu.hide()
await frames(3)
expect(capture.lines.has("validate res://a.tres\n"), "回调收到选中的路径")
remove_context_menu_plugin(node)
```

## references/editor-recipes.md `add_context_menu_plugin(`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://addons/items")
DirAccess.copy_absolute("res://s4.gd", "res://addons/items/file_menu.gd")
```

```gdscript
var menu: EditorContextMenuPlugin = node._menu
expect(menu != null and menu.get_script().resource_path == "res://addons/items/file_menu.gd", "加载了文件菜单脚本")
node.free()
add_context_menu_plugin(EditorContextMenuPlugin.CONTEXT_SLOT_FILESYSTEM, menu)
remove_context_menu_plugin(menu)
```

## references/editor-recipes.md `resources_reimported.connect`

<!-- check: prepare -->
```gdscript
var capture := FileAccess.open("res://capture.gd", FileAccess.WRITE)
capture.store_string("extends Logger\n\nvar lines: Array[String] = []\n\nfunc _log_message(message: String, _error: bool) -> void:\n\tlines.append(message)\n")
capture.close()
```

```gdscript
var capture: Logger = load("res://capture.gd").new()
OS.add_logger(capture)
var fs := EditorInterface.get_resource_filesystem()
expect(fs.resources_reimported.is_connected(node._on_reimported), "连了 resources_reimported")
expect(fs.filesystem_changed.is_connected(node._on_filesystem_changed), "连了 filesystem_changed")
var events: Array[String] = []
fs.resources_reimporting.connect(func(paths: PackedStringArray) -> void: events.append("reimporting " + ",".join(paths)))
fs.resources_reimported.connect(func(paths: PackedStringArray) -> void: events.append("reimported " + ",".join(paths)))
make_texture().get_image().save_png("res://one.png")
fs.update_file("res://one.png")
await frames(10)
expect(not FileAccess.file_exists("res://one.png.import"), "update_file 只登记不导入")
fs.reimport_files(PackedStringArray(["res://one.png"]))
expect(FileAccess.file_exists("res://one.png.import"), "reimport_files 生成 .import")
expect(events == ["reimporting res://one.png", "reimported res://one.png"], "重导前后各触发一次 " + str(events))
expect(capture.lines.has("重导 res://one.png\n"), "回调收到重导路径")
make_texture().get_image().save_png("res://two.png")
fs.scan()
for i in 600:
	if FileAccess.file_exists("res://two.png.import") and not fs.is_scanning():
		break
	await get_tree().process_frame
expect(FileAccess.file_exists("res://two.png.import"), "scan 让编辑器看见并导入新文件")
expect(capture.lines.has("文件系统有变化\n"), "filesystem_changed 回调触发")
var on_reimported: Callable = node._on_reimported
node.free()
expect(not fs.resources_reimported.is_connected(on_reimported), "退出时断开")
```

## references/editor-recipes.md `ProjectSettings.add_property_info`

```gdscript
var setting := "items/validation/strict"
expect(ProjectSettings.has_setting(setting) and ProjectSettings.get_setting(setting) == true, "进树后设置存在且为 true")
var info: Dictionary = {}
for entry: Dictionary in ProjectSettings.get_property_list():
	if entry["name"] == setting:
		info = entry
expect(not info.is_empty() and info["type"] == TYPE_BOOL, "属性信息登记为 bool")
ProjectSettings.save()
expect(not FileAccess.get_file_as_string("res://project.godot").contains("items/validation"), "与默认值相同不写盘")
ProjectSettings.set_setting(setting, false)
ProjectSettings.save()
expect(FileAccess.get_file_as_string("res://project.godot").contains("strict=false"), "改动后写盘")
ProjectSettings.set_setting(setting, true)
```

## references/editor-recipes.md `Add Marker`

<!-- check: prepare -->
```gdscript
var level := Node2D.new()
level.name = "Level"
var packed := PackedScene.new()
packed.pack(level)
ResourceSaver.save(packed, "res://level.tscn")
level.free()
```

```gdscript
EditorInterface.open_scene_from_path("res://level.tscn")
await frames(5)
var root := EditorInterface.get_edited_scene_root()
expect(root != null and root.name == "Level", "打开了 level.tscn")
node.get_parent().remove_child(node)
root.add_child(node)
node.owner = root
expect(not EditorInterface.get_unsaved_scenes().has("res://level.tscn"), "刚打开的场景未改动")
node.position = Vector2(5.0, 5.0)
expect(not EditorInterface.get_unsaved_scenes().has("res://level.tscn"), "脚本改属性不会自动标记未保存")
expect(Engine.get_singleton(&"EditorInterface") == EditorInterface, "Engine.get_singleton 取得 EditorInterface")
node.add_action.call()
var marker := node.get_node("SpawnPoint") as Marker2D
expect(marker != null and marker.owner == root, "marker 的 owner 是场景根")
expect(EditorInterface.get_unsaved_scenes().has("res://level.tscn"), "场景被标记为未保存")
var loose := Marker2D.new()
loose.name = "Loose"
node.add_child(loose)
var wrong := Marker2D.new()
wrong.name = "Wrong"
node.add_child(wrong)
wrong.owner = node
var packed := PackedScene.new()
packed.pack(root)
var copy := packed.instantiate()
expect(copy.find_child("SpawnPoint", true, true) != null, "owner 是场景根的节点会存盘")
expect(copy.find_child("Loose", true, false) == null, "没有 owner 的节点不存盘")
expect(copy.find_child("Wrong", true, false) == null, "owner 是直接父节点的节点不存盘")
copy.free()
```

## references/editor-recipes.md `class_name SnapSelectionToGrid`

<!-- check: prepare -->
```gdscript
var level := Node2D.new()
level.name = "Level"
var packed := PackedScene.new()
packed.pack(level)
ResourceSaver.save(packed, "res://level.tscn")
level.free()
```

```gdscript
EditorInterface.open_scene_from_path("res://level.tscn")
await frames(5)
var root := EditorInterface.get_edited_scene_root()
var first := Node2D.new()
first.name = "First"
first.position = Vector2(21.0, 37.0)
var second := Node2D.new()
second.name = "Second"
second.position = Vector2(-5.0, 9.0)
var plain := Node.new()
plain.name = "Plain"
for child: Node in [first, second, plain]:
	root.add_child(child)
	child.owner = root
	EditorInterface.get_selection().add_node(child)
node._run()
expect(first.position == Vector2(16.0, 32.0) and second.position == Vector2(0.0, 16.0), "位置吸附到 16 的网格 " + str(first.position) + str(second.position))
var manager := EditorInterface.get_editor_undo_redo()
var history := manager.get_history_undo_redo(manager.get_object_history_id(first))
expect(history.get_current_action_name() == "Snap to grid", "动作名")
expect(manager.get_object_history_id(first) != EditorUndoRedoManager.GLOBAL_HISTORY, "节点记入编辑场景的历史")
history.undo()
expect(first.position == Vector2(21.0, 37.0) and second.position == Vector2(-5.0, 9.0), "一次撤销还原所有节点")
EditorInterface.get_selection().clear()
```

## references/editor-recipes.md `Randomize Color`

<!-- check: prepare -->
```gdscript
var level := Node2D.new()
level.name = "Level"
var packed := PackedScene.new()
packed.pack(level)
ResourceSaver.save(packed, "res://level.tscn")
level.free()
ResourceSaver.save(Resource.new(), "res://external.tres")
```

```gdscript
EditorInterface.open_scene_from_path("res://level.tscn")
await frames(5)
var root := EditorInterface.get_edited_scene_root()
node.get_parent().remove_child(node)
root.add_child(node)
node.owner = root
var manager := EditorInterface.get_editor_undo_redo()
expect(get_undo_redo() == manager, "插件的 get_undo_redo 是同一个对象")
node.randomize_action.call()
var scene_history := manager.get_object_history_id(node)
expect(scene_history != EditorUndoRedoManager.GLOBAL_HISTORY, "节点记入当前编辑场景的历史")
var history := manager.get_history_undo_redo(scene_history)
expect(node.self_modulate != Color.WHITE and history.get_current_action_name() == "Randomize Color", "动作已提交并改了颜色")
history.undo()
expect(node.self_modulate == Color.WHITE, "撤销恢复颜色")
history.redo()
expect(node.self_modulate != Color.WHITE, "重做再次改色")
var external: Resource = load("res://external.tres")
expect(manager.get_object_history_id(external) == EditorUndoRedoManager.GLOBAL_HISTORY, "外部资源记入全局历史")
manager.create_action("Drag", UndoRedo.MERGE_ENDS, node)
manager.add_do_property(node, &"position", Vector2(10.0, 0.0))
manager.add_undo_property(node, &"position", Vector2.ZERO)
manager.commit_action()
manager.create_action("Drag", UndoRedo.MERGE_ENDS, node)
manager.add_do_property(node, &"position", Vector2(20.0, 0.0))
manager.add_undo_property(node, &"position", Vector2(10.0, 0.0))
manager.commit_action()
expect(node.position == Vector2(20.0, 0.0), "拖动两次")
history.undo()
expect(node.position == Vector2.ZERO, "同名 MERGE_ENDS 合并成一步")
manager.create_action("Call", UndoRedo.MERGE_DISABLE, node)
manager.add_do_method(node, &"set_rotation", 1.0)
manager.add_undo_method(node, &"set_rotation", 0.0)
manager.commit_action()
expect(is_equal_approx(node.rotation, 1.0), "add_do_method 提交时执行")
history.undo()
expect(is_zero_approx(node.rotation), "add_undo_method 撤销时执行")
```

## references/export-annotations.md `class_name SkillDef`

```gdscript
var props: Dictionary = {}
var order: Array[String] = []
for info: Dictionary in node.get_property_list():
	props[info["name"]] = info
	order.append(info["name"])
expect(props["基础"]["usage"] == PROPERTY_USAGE_CATEGORY, "export_category 是分类")
expect(props["数值"]["usage"] == PROPERTY_USAGE_GROUP and props["引用"]["usage"] == PROPERTY_USAGE_GROUP, "export_group 是分组")
expect(props["高级"]["usage"] == PROPERTY_USAGE_GROUP and props["高级"]["hint_string"] == "adv_", "带前缀的分组")
expect(props[""]["usage"] == PROPERTY_USAGE_GROUP, "export_group 空串结束分组")
expect(props["description"]["hint"] == PROPERTY_HINT_MULTILINE_TEXT, "export_multiline")
expect(props["id"]["hint"] == PROPERTY_HINT_PLACEHOLDER_TEXT and props["id"]["hint_string"] == "skill_id", "export_placeholder")
expect(props["element"]["hint"] == PROPERTY_HINT_ENUM and props["element"]["hint_string"] == "Fire,Water,Earth", "export_enum")
expect(props["chance"]["hint"] == PROPERTY_HINT_RANGE and props["chance"]["hint_string"] == "0.0,100.0,0.5,suffix:%", "export_range 带后缀")
expect(props["angle"]["hint"] == PROPERTY_HINT_RANGE and props["angle"]["hint_string"] == "0.0,360.0,1.0,degrees", "export_range 度数")
expect(props["targets"]["hint"] == PROPERTY_HINT_FLAGS and props["targets"]["hint_string"] == "Self:1,Allies:2,Foes:4", "export_flags")
expect(props["hit_mask"]["hint"] == PROPERTY_HINT_LAYERS_2D_PHYSICS, "export_flags_2d_physics")
expect(props["falloff"]["hint"] == PROPERTY_HINT_EXP_EASING and props["falloff"]["hint_string"] == "attenuation", "export_exp_easing")
expect(props["source"]["hint"] == PROPERTY_HINT_FILE and props["source"]["hint_string"] == "*.json", "export_file")
expect(props["folder"]["hint"] == PROPERTY_HINT_DIR, "export_dir")
expect(props["anchor"]["hint"] == PROPERTY_HINT_NODE_PATH_VALID_TYPES and props["anchor"]["hint_string"] == "Marker2D", "export_node_path")
expect(props["tint"]["hint"] == PROPERTY_HINT_COLOR_NO_ALPHA, "export_color_no_alpha")
expect(int(props["format_version"]["usage"]) & PROPERTY_USAGE_EDITOR == 0 and int(props["format_version"]["usage"]) & PROPERTY_USAGE_STORAGE != 0, "export_storage 存盘不显示")
expect(props["level"]["hint"] == PROPERTY_HINT_RANGE and props["level"]["hint_string"] == "0,10,1,or_greater", "export_custom")
expect(props["validate_action"]["hint"] == PROPERTY_HINT_TOOL_BUTTON and props["validate_action"]["hint_string"] == "Validate,Reload", "export_tool_button")
expect(order.find("adv_cooldown") > order.find("高级") and order.find("adv_cost") < order.find(""), "高级组包含 adv_ 属性")

node.format_version = 5
node.level = 12
var copy: Resource = node.duplicate()
expect(copy.format_version == 5 and copy.level == 12, "duplicate 复制 export_storage 的值")
node.title = "火球"
node.id = "fireball"
node.validate()
node.id = ""
Engine.print_error_messages = false
node.validate()
Engine.print_error_messages = true
```

## references/import-plugin.md `class_name ItemData`

```gdscript
node.id = &"sword"
node.price = 10
ResourceSaver.save(node, "user://item.tres")
var loaded: ItemData = ResourceLoader.load("user://item.tres", "", ResourceLoader.CACHE_MODE_IGNORE)
expect(loaded.id == &"sword" and loaded.price == 10, "id 和 price 存盘后读回")
DirAccess.remove_absolute("user://item.tres")
```

## references/import-plugin.md `class_name ItemDb`

```gdscript
var sword := ItemData.new()
sword.id = &"sword"
sword.price = 10
node.items.append(sword)
expect(node.items.is_typed() and node.items.get_typed_script() == ItemData.new().get_script(), "items 是 Array[ItemData]")
ResourceSaver.save(node, "user://db.res")
var loaded: ItemDb = ResourceLoader.load("user://db.res", "", ResourceLoader.CACHE_MODE_IGNORE)
expect(loaded.items.size() == 1 and loaded.items[0].id == &"sword" and loaded.items[0].price == 10, "条目存盘后读回")
DirAccess.remove_absolute("user://db.res")
```

## references/import-plugin.md `extends EditorImportPlugin`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://data")
```

```gdscript
add_import_plugin(node)
var fs := EditorInterface.get_resource_filesystem()
var good := FileAccess.open("res://data/items.itemtable", FileAccess.WRITE)
good.store_string("[{\"id\":\"sword\",\"price\":10},{\"id\":\"shield\",\"price\":25},{\"id\":\"bare\"}]")
good.close()
var bad := FileAccess.open("user://bad.itemtable", FileAccess.WRITE)
bad.store_string("{\"id\":\"sword\"}")
bad.close()
fs.scan()
for i in 600:
	if FileAccess.file_exists("res://data/items.itemtable.import") and not fs.is_scanning():
		break
	await get_tree().process_frame
expect(FileAccess.file_exists("res://data/items.itemtable.import"), "扫描后生成 .import 文件")
var config := ConfigFile.new()
config.load("res://data/items.itemtable.import")
expect(config.get_value("remap", "importer") == "game.item_table", "importer 名字")
var saved: String = config.get_value("remap", "path")
expect(saved.begins_with("res://.godot/imported/") and saved.ends_with(".res") and FileAccess.file_exists(saved), "导入结果在 .godot/imported 下的 .res")
var db := load("res://data/items.itemtable") as ItemDb
expect(db != null and db.items.size() == 3, "load 源文件路径得到 ItemDb")
expect(db.items[0].id == &"sword" and db.items[0].price == 10 and db.items[1].price == 25, "字段解析")
expect(db.items[2].id == &"bare" and db.items[2].price == 0, "缺字段用默认值")
var variants: Array[String] = []
var generated: Array[String] = []
expect(node._import("user://bad.itemtable", "user://bad", {}, variants, generated) == ERR_PARSE_ERROR, "不是数组返回 ERR_PARSE_ERROR")
expect(node._import("res://data/items.itemtable", "user://direct", {}, variants, generated) == OK, "直接调用 _import")
var direct := ResourceLoader.load("user://direct.res", "", ResourceLoader.CACHE_MODE_IGNORE) as ItemDb
expect(direct != null and direct.items.size() == 3, "直接导入的结果")
DirAccess.remove_absolute("user://direct.res")
DirAccess.remove_absolute("user://bad.itemtable")
expect(node._get_recognized_extensions() == PackedStringArray(["itemtable"]), "只认自己的后缀")
expect(node._get_import_options("", 0).is_empty() and node._get_preset_name(0) == "Default", "选项和预设")
remove_import_plugin(node)
```

## references/import-plugin.md `add_import_plugin(_importer)`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://addons/items")
DirAccess.make_dir_recursive_absolute("res://data")
DirAccess.copy_absolute("res://s2.gd", "res://addons/items/item_table_importer.gd")
```

```gdscript
var fs := EditorInterface.get_resource_filesystem()
var source := FileAccess.open("res://data/items.itemtable", FileAccess.WRITE)
source.store_string("[{\"id\":\"sword\",\"price\":10}]")
source.close()
fs.scan()
for i in 600:
	if FileAccess.file_exists("res://data/items.itemtable.import") and not fs.is_scanning():
		break
	await get_tree().process_frame
var db := load("res://data/items.itemtable") as ItemDb
expect(db != null and db.items.size() == 1 and db.items[0].id == &"sword" and db.items[0].price == 10, "插件注册后 load 源文件得到 ItemDb")
node.free()
var later := FileAccess.open("res://data/later.itemtable", FileAccess.WRITE)
later.store_string("[]")
later.close()
fs.scan()
await frames(60)
expect(not FileAccess.file_exists("res://data/later.itemtable.import"), "退出后导入器已移除")
```

## references/import-plugin.md `extends EditorScenePostImport`

<!-- check: prepare -->
```gdscript
DirAccess.copy_absolute("res://s4.gd", "res://post.gd")
var positions := PackedByteArray()
positions.resize(36)
var values := PackedFloat32Array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
for i in values.size():
	positions.encode_float(i * 4, values[i])
var model := {
	"asset": {"version": "2.0"},
	"scene": 0,
	"scenes": [{"nodes": [0]}],
	"nodes": [{"mesh": 0, "name": "Tri"}],
	"meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
	"accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "max": [1, 1, 0], "min": [0, 0, 0]}],
	"bufferViews": [{"buffer": 0, "byteLength": 36, "target": 34962}],
	"buffers": [{"byteLength": 36, "uri": "data:application/octet-stream;base64," + Marshalls.raw_to_base64(positions)}],
}
var file := FileAccess.open("res://tri.gltf", FileAccess.WRITE)
file.store_string(JSON.stringify(model))
file.close()
```

```gdscript
var root := Node3D.new()
for mesh_name in ["A", "B"]:
	var mesh := MeshInstance3D.new()
	mesh.name = mesh_name
	root.add_child(mesh)
	mesh.owner = root
expect(node._post_import(root) == root, "返回场景根")
for child in root.get_children():
	expect((child as MeshInstance3D).cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, "关闭阴影 " + child.name)
root.free()

var fs := EditorInterface.get_resource_filesystem()
expect(FileAccess.file_exists("res://tri.gltf.import"), "glTF 已按默认设置导入")
var plain := (load("res://tri.gltf") as PackedScene).instantiate()
var plain_mesh := plain.find_children("*", "MeshInstance3D", true, false)
expect(plain_mesh.size() == 1 and (plain_mesh[0] as MeshInstance3D).cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_ON, "默认导入的网格有阴影")
plain.free()
var config := ConfigFile.new()
config.load("res://tri.gltf.import")
config.set_value("params", "import_script/path", "res://post.gd")
config.save("res://tri.gltf.import")
fs.reimport_files(PackedStringArray(["res://tri.gltf"]))
var processed := (ResourceLoader.load("res://tri.gltf", "", ResourceLoader.CACHE_MODE_REPLACE) as PackedScene).instantiate()
var processed_mesh := processed.find_children("*", "MeshInstance3D", true, false)
expect(processed_mesh.size() == 1 and (processed_mesh[0] as MeshInstance3D).cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, "Import Script 的 Path 设成脚本后重导关闭了阴影")
processed.free()
```

## references/inspector-plugin.md `class_name ItemData`

```gdscript
node.id = &"sword"
node.price = 10
ResourceSaver.save(node, "user://item.tres")
var loaded: ItemData = ResourceLoader.load("user://item.tres", "", ResourceLoader.CACHE_MODE_IGNORE)
expect(loaded.id == &"sword" and loaded.price == 10, "id 和 price 存盘后读回")
DirAccess.remove_absolute("user://item.tres")
```

## references/inspector-plugin.md `extends EditorProperty`

```gdscript
var item := ItemData.new()
item.price = 25
node.set_object_and_property(item, &"price")
node.update_property()
expect(node._spin.value == 25.0 and node._spin.max_value == 9999.0 and node._spin.step == 1.0, "控件显示当前值")
var emitted: Array[Array] = []
node.property_changed.connect(func(property: StringName, value: Variant, _field: StringName, _changing: bool) -> void: emitted.append([property, value]))
item.price = 60
node.update_property()
expect(node._spin.value == 60.0 and emitted.is_empty(), "别处改值时更新控件不回写")
node._spin.value = 40.0
expect(emitted == [[&"price", 40]], "用户改值只发 emit_changed " + str(emitted))
expect(typeof(emitted[0][1]) == TYPE_INT, "提交的是 int")
```

## references/inspector-plugin.md `extends EditorInspectorPlugin`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://addons/items")
DirAccess.copy_absolute("res://s1.gd", "res://addons/items/price_editor.gd")
```

```gdscript
var item := ItemData.new()
item.id = &"sword"
item.price = 25
var other := Resource.new()
expect(node._can_handle(item) and not node._can_handle(other), "只处理 ItemData")
expect(not node._parse_property(item, TYPE_STRING_NAME, "id", PROPERTY_HINT_NONE, "", PROPERTY_USAGE_DEFAULT, false), "其他属性返回 false")
add_inspector_plugin(node)
EditorInterface.inspect_object(item)
await frames(5)
var price_editors: Array[EditorProperty] = []
var id_editors: Array[EditorProperty] = []
for candidate: Node in EditorInterface.get_inspector().find_children("*", "EditorProperty", true, false):
	var editor := candidate as EditorProperty
	if editor.get_edited_property() == &"price":
		price_editors.append(editor)
	if editor.get_edited_property() == &"id":
		id_editors.append(editor)
expect(price_editors.size() == 1 and price_editors[0].get_script() != null and price_editors[0].get_script().resource_path == "res://addons/items/price_editor.gd", "price 换成了自定义控件")
expect(id_editors.size() == 1 and id_editors[0].get_script() == null, "id 保留内置编辑器")
price_editors[0]._spin.value = 40.0
await frames(2)
expect(item.price == 40, "emit_changed 写回属性")
var manager := EditorInterface.get_editor_undo_redo()
var history := manager.get_history_undo_redo(manager.get_object_history_id(item))
expect(history.has_undo(), "编辑器登记了撤销")
history.undo()
expect(item.price == 25, "撤销恢复 price")
remove_inspector_plugin(node)
EditorInterface.inspect_object(null)
```

## references/inspector-plugin.md `add_inspector_plugin(_inspector)`

<!-- check: prepare -->
```gdscript
DirAccess.make_dir_recursive_absolute("res://addons/items")
DirAccess.copy_absolute("res://s1.gd", "res://addons/items/price_editor.gd")
DirAccess.copy_absolute("res://s2.gd", "res://addons/items/item_inspector.gd")
```

```gdscript
var item := ItemData.new()
item.price = 25
EditorInterface.inspect_object(item)
await frames(5)
var count := func() -> int:
	var found := 0
	for candidate: Node in EditorInterface.get_inspector().find_children("*", "EditorProperty", true, false):
		var editor := candidate as EditorProperty
		if editor.get_edited_property() == &"price" and editor.get_script() != null:
			found += 1
	return found
expect(count.call() == 1, "插件启用后 price 用自定义控件")
node.free()
EditorInterface.inspect_object(null)
await frames(2)
EditorInterface.inspect_object(item)
await frames(5)
expect(count.call() == 0, "插件退出后 price 回到内置控件")
EditorInterface.inspect_object(null)
```
