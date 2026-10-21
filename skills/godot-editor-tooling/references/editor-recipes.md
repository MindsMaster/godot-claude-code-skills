# 编辑器扩展配方

## 插件骨架

```
addons/
  items/
    plugin.cfg
    plugin.gd
```

```ini
[plugin]

name="Items"
description="物品数据工具"
author="team"
version="1.0"
script="plugin.gd"
```

```gdscript
@tool
extends EditorPlugin

func _enter_tree() -> void:
	pass

func _exit_tree() -> void:
	pass
```

- 在 Project Settings 的 Plugins 页勾选 Enable，写入 `editor_plugins/enabled`
- `_exit_tree` 里撤销 `_enter_tree` 做的每件事：`remove_dock` `remove_inspector_plugin` `remove_import_plugin` `remove_tool_menu_item`，并 `queue_free` 自己建的控件，否则关闭再开启会重复注册
- 改了 `plugin.gd` 后关掉再开启插件，`_enter_tree` 才会重新执行
- 只给本项目用的工具也放 `addons/`，导出预设里排除 `addons/*` 下的编辑器脚本
- 多数场合不需要 `add_custom_type`：脚本加 `class_name` 和 `@icon` 就会出现在创建节点和资源的对话框里

## Dock

4.6+ 用 `EditorDock`，它是实验性类。`add_control_to_dock` 与 `add_control_to_bottom_panel` 已标记弃用，底部面板把 `default_slot` 设为 `DOCK_SLOT_BOTTOM`。

```gdscript
@tool
extends EditorPlugin

var _dock: EditorDock

func _enter_tree() -> void:
	_dock = EditorDock.new()
	_dock.title = "Items"
	_dock.default_slot = EditorDock.DOCK_SLOT_RIGHT_UL
	_dock.add_child(load("res://addons/items/items_panel.tscn").instantiate())
	add_dock(_dock)

func _exit_tree() -> void:
	remove_dock(_dock)
	_dock.queue_free()
	_dock = null
```

- `dock_icon` 或 `icon_name` 设图标，`closable` 允许关闭，`available_layouts` 限定垂直水平浮动布局，默认只允许垂直和浮动，`dock_shortcut` 绑定打开快捷键
- 面板内容做成场景，布局随停靠位置变化时重写 `EditorDock._update_layout`
- 要兼容 4.4 到 4.5，面板控件用 `add_control_to_dock(EditorPlugin.DOCK_SLOT_RIGHT_UL, panel)` 加入，`remove_control_from_docks(panel)` 移除
- 同一份代码跨 4.5 与 4.6 时，用 `ClassDB.class_exists(&"EditorDock")` 分支，`EditorDock` 用 `ClassDB.instantiate` 创建，`add_dock` 用 `call("add_dock", dock)`，否则 4.5 解析报错

## 主题 图标 缩放

```gdscript
@tool
extends VBoxContainer

var _title: Label = Label.new()

func _init() -> void:
	add_child(_title)

func _notification(what: int) -> void:
	if what == NOTIFICATION_THEME_CHANGED:
		_title.add_theme_color_override("font_color", get_theme_color("accent_color", "Editor"))
		var icon := get_theme_icon("Reload", "EditorIcons")
		custom_minimum_size.y = icon.get_height() * 2.0
```

- 控件挂进编辑器后，`get_theme_color(名, "Editor")` 取编辑器主题色，主题切换时 `NOTIFICATION_THEME_CHANGED` 重新取
- 脱离控件树时用 `EditorInterface.get_editor_theme()`，再 `get_color("warning_color", "Editor")`
- 可用颜色名：`base_color` `accent_color` `success_color` `warning_color` `error_color` `font_color` `disabled_font_color` 等，`get_color_list("Editor")` 列全
- 图标取 EditorIcons 类型下的内置名，如 Add Remove Reload Save Warning Error Node Folder Search Edit Play，完整列表见 godot-editor-icons.github.io
- 尺寸乘 `EditorInterface.get_editor_scale()`，高分屏上不糊
- 硬编码 `Color(0.2, 0.2, 0.2)` 在亮色主题下看不见

## 快捷键与菜单

```gdscript
@tool
extends EditorPlugin

var _shortcut: Shortcut

func _enter_tree() -> void:
	_shortcut = Shortcut.new()
	var key := InputEventKey.new()
	key.keycode = KEY_V
	key.command_or_control_autoremap = true
	key.shift_pressed = true
	_shortcut.events = [key]
	EditorInterface.get_editor_settings().add_shortcut("items/validate", _shortcut)
	add_tool_menu_item("Validate Items", _validate)
	EditorInterface.get_command_palette().add_command("Validate Items", "items/validate", _validate)

func _exit_tree() -> void:
	remove_tool_menu_item("Validate Items")
	EditorInterface.get_command_palette().remove_command("items/validate")

func _shortcut_input(event: InputEvent) -> void:
	if not event.is_pressed() or event.is_echo():
		return
	if EditorInterface.get_editor_settings().is_shortcut("items/validate", event):
		_validate()
		get_viewport().set_input_as_handled()

func _validate() -> void:
	print("validate")
```

- 用 `Shortcut` 资源，不要在 `_input` 里手写 `keycode` 判断。`command_or_control_autoremap` 让 macOS 自动换成 Cmd
- `EditorSettings.add_shortcut` 与 `is_shortcut`（4.6+）让快捷键出现在编辑器设置的快捷键页，用户可改键，注册后须在 `_shortcut_input` 里用 `is_shortcut(路径, event)` 匹配才会触发
- 4.5 及以下没有这两个方法，用 `Shortcut.matches_event(event)`，或把 `Shortcut` 赋给按钮的 `shortcut` 属性，4.6+ 的 `EditorDock` 用 `dock_shortcut`
- `add_tool_menu_item` 放进 Project > Tools 菜单，`add_command` 进命令面板（Ctrl+Shift+P）

文件系统和场景树的右键菜单用 `EditorContextMenuPlugin`（4.4+）：

```gdscript
@tool
extends EditorContextMenuPlugin

func _popup_menu(paths: PackedStringArray) -> void:
	if paths.size() == 1 and paths[0].ends_with(".tres"):
		add_context_menu_item("Validate Resource", _validate)

func _validate(files: Array) -> void:
	for path: String in files:
		print("validate ", path)
```

```gdscript
@tool
extends EditorPlugin

var _menu: EditorContextMenuPlugin

func _enter_tree() -> void:
	_menu = load("res://addons/items/file_menu.gd").new()
	add_context_menu_plugin(EditorContextMenuPlugin.CONTEXT_SLOT_FILESYSTEM, _menu)

func _exit_tree() -> void:
	remove_context_menu_plugin(_menu)
	_menu = null
```

## 响应文件变化

```gdscript
@tool
extends EditorPlugin

func _enter_tree() -> void:
	var fs := EditorInterface.get_resource_filesystem()
	fs.resources_reimported.connect(_on_reimported)
	fs.filesystem_changed.connect(_on_filesystem_changed)

func _exit_tree() -> void:
	var fs := EditorInterface.get_resource_filesystem()
	fs.resources_reimported.disconnect(_on_reimported)
	fs.filesystem_changed.disconnect(_on_filesystem_changed)

func _on_reimported(paths: PackedStringArray) -> void:
	for path in paths:
		print("重导 ", path)

func _on_filesystem_changed() -> void:
	print("文件系统有变化")
```

- `resources_reimported(paths)` 重导后触发，`resources_reimporting(paths)` 重导前触发，`filesystem_changed` 文件系统有变化时触发，`sources_changed(exist)` 导入文件的源文件变化时触发
- 别在 `_process` 里每 0.5 秒轮询 mtime 或文件列表
- 代码生成了文件后调用 `EditorInterface.get_resource_filesystem().scan()` 让编辑器看见，`update_file(path)` 只登记文件不导入，要导入用 `reimport_files` 或 `scan`
- 一次连续写很多文件会触发多次信号，在回调里只置脏标志，下一帧统一刷新

## 项目设置

```gdscript
@tool
extends EditorPlugin

const SETTING: String = "items/validation/strict"

func _enter_tree() -> void:
	if not ProjectSettings.has_setting(SETTING):
		ProjectSettings.set_setting(SETTING, true)
	ProjectSettings.set_initial_value(SETTING, true)
	ProjectSettings.add_property_info({
		"name": SETTING,
		"type": TYPE_BOOL,
	})
```

保存项目设置时才写入 `project.godot`，`set_initial_value` 让与默认值相同的设置不写盘。

## 编辑器里造节点

```gdscript
@tool
extends Node2D

@export_tool_button("Add Marker", "Add") var add_action: Callable = add_marker

func add_marker() -> void:
	var marker := Marker2D.new()
	marker.name = "SpawnPoint"
	add_child(marker)
	marker.owner = EditorInterface.get_edited_scene_root()
	EditorInterface.mark_scene_as_unsaved()
```

- 不设 `owner`，节点既不在场景面板显示，也不会存盘
- `owner` 必须是当前编辑场景的根，不是直接父节点
- 脚本同时在游戏里运行时，不能直接写 `EditorInterface`，导出的游戏里没有这个类，脚本会解析失败。把编辑器部分拆成只在编辑器用的脚本，或者通过 `Engine.get_singleton(&"EditorInterface")` 取对象

## EditorScript 批处理

```gdscript
@tool
class_name SnapSelectionToGrid
extends EditorScript

func _run() -> void:
	var ur := EditorInterface.get_editor_undo_redo()
	ur.create_action("Snap to grid")
	for node: Node in EditorInterface.get_selection().get_selected_nodes():
		var node_2d := node as Node2D
		if node_2d == null:
			continue
		ur.add_do_property(node_2d, &"position", node_2d.position.snapped(Vector2(16.0, 16.0)))
		ur.add_undo_property(node_2d, &"position", node_2d.position)
	ur.commit_action()
```

- 脚本编辑器里 `File > Run`（Ctrl+Shift+X）执行，文件系统里右键 Run 也行。有 `class_name` 的也能从命令面板搜类名运行
- C# 的 `EditorScript` 不能从脚本编辑器运行，命令面板里出现须写 `[GlobalClass]` 和 `[Tool]`
- 一次性、不需要界面的批量改动用它，经常用的做成 `@export_tool_button` 或菜单项
- 不走 `EditorUndoRedoManager` 的改动没法撤销，运行前先存盘
- 不要改场景实例的子节点：重载场景时改动会丢，判断 `node == 场景根` 或 `node.owner == 场景根` 再改，场景根取 `EditorInterface.get_edited_scene_root()`

## 撤销重做

```gdscript
@tool
extends Node2D

@export_tool_button("Randomize Color", "ColorRect") var randomize_action: Callable = randomize_color

func randomize_color() -> void:
	var ur := EditorInterface.get_editor_undo_redo()
	ur.create_action("Randomize Color", UndoRedo.MERGE_DISABLE, self)
	ur.add_do_property(self, &"self_modulate", Color(randf(), randf(), randf()))
	ur.add_undo_property(self, &"self_modulate", self_modulate)
	ur.commit_action()
```

- `EditorInterface.get_editor_undo_redo()` 4.4+，插件里的 `get_undo_redo()` 返回同一个对象
- 动作的历史按第一个操作的对象推断：节点记入当前编辑场景，内嵌资源记入所属场景，外部资源和其他对象记入全局历史。推断不对时用第三个参数 `custom_context` 指定
- 需要调函数的动作用 `add_do_method` 和 `add_undo_method`
- 连续拖动同一属性，动作用同一个名字加 `UndoRedo.MERGE_ENDS` 合并成一步

## C# 插件

```csharp
[Tool]
public partial class ItemsPlugin : EditorPlugin
{
    private EditorDock _dock;

    public override void _EnterTree()
    {
        _dock = new EditorDock();
        _dock.Title = "Items";
        _dock.DefaultSlot = EditorDock.DockSlot.RightUl;
        AddDock(_dock);
    }

    public override void _ExitTree()
    {
        RemoveDock(_dock);
        _dock.QueueFree();
        _dock = null;
    }
}
```

- 编辑器单例在 C# 里经 Singleton 属性访问，如 `EditorInterface.Singleton.GetEditorTheme()`，不是静态方法
- `plugin.cfg` 里 `script="ItemsPlugin.cs"`，类名与文件名一致
- 每次改完先点 Build，`[Tool]` 脚本才用上新代码
