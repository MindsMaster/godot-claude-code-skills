---
name: godot-editor-tooling
description: Godot 4 编辑器扩展与工具脚本，用于项目内数据编辑、Inspector 定制、编辑器插件、导入插件。Use when writing @tool scripts, Engine.is_editor_hint(), @export_tool_button, EditorPlugin / plugin.cfg, EditorInspectorPlugin / EditorProperty, EditorImportPlugin, EditorScenePostImport, EditorScript batch scripts, EditorUndoRedoManager, EditorDock / add_control_to_dock, EditorFileSystem signals, add_autoload_singleton / _enable_plugin, main screen plugin (_has_main_screen), editor theme colors (get_editor_theme), Shortcut, _get_property_list / _validate_property dynamic properties, _get_configuration_warnings, @export_group annotations, C# [Tool] hot reload pitfalls. 编辑器插件 工具脚本 数据编辑器 Inspector 导入器 撤销重做 停靠面板 主屏幕 插件 Autoload 热重载。
---

# Godot 编辑器工具

解决在编辑器里做东西：@tool 脚本、数据编辑、Inspector 定制、插件、导入。不管数据怎么存怎么加载（见 godot-resources-data），不管游戏内的 UI（见 godot-ui）。

核心做法：项目内的数据编辑器做成 Inspector 能编辑的 `Resource`，不做独立工具窗口，不把 JSON 伪装进 Inspector。`Resource` 自带属性编辑、撤销重做、拖拽引用、复制粘贴、版本控制 diff，这些独立窗口都要自己写。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 编辑一张数据表 | 自定义 `Resource` + `@export` | 独立编辑窗口，JSON 加手写表单 |
| Inspector 里放按钮 | `@export_tool_button`（4.4+） | 为放一个按钮写 `EditorInspectorPlugin` |
| 按条件隐藏 禁用属性 | `_validate_property` | 重写 `_get_property_list` 整体伪造 |
| 属性联动刷新 | setter 里 `notify_property_list_changed()` | 定时器刷新 Inspector |
| 节点配置检查 | `_get_configuration_warnings` | 打印日志代替警告三角 |
| 属性分组 范围 下拉 文件选择 | `@export_*` 注解，见 [references/export-annotations.md](references/export-annotations.md) | 自定义属性控件 |
| 外部文件变成资源 | `EditorImportPlugin` | 运行时解析，或手动转换后忘了重转 |
| 3D 场景导入后统一处理 | `EditorScenePostImport` | 手动改每个场景 |
| 一次性批处理 | `EditorScript`，或 tool 按钮 | 临时场景加 `_ready` 里跑完再删 |
| 撤销重做 | `EditorUndoRedoManager` | 直接改属性，用户 Ctrl+Z 无效 |
| 文件变化通知 | `EditorFileSystem` 信号 | `_process` 里轮询 mtime |
| 编辑器颜色 图标 缩放 | 控件的 `get_theme_color(名, "Editor")`，脱离控件用 `EditorInterface.get_editor_theme()` | 硬编码 `Color` 和像素 |
| 快捷键 | `Shortcut` 资源 | `_input` 里手写 `keycode` 判断 |
| 停靠面板 | `EditorDock`（4.6+），4.5 及以下 `add_control_to_dock`，4.6+ 已弃用 | 独立 `Window` |
| 右键菜单 命令面板 | `EditorContextMenuPlugin`（4.4+），`EditorCommandPalette.add_command` | 监听鼠标自己弹菜单 |
| 项目里自定义设置 | `ProjectSettings.add_property_info` | 另存一份配置文件 |
| 插件自带 Autoload，顶部主屏幕标签页 | `_enable_plugin` 里 `add_autoload_singleton`，`_has_main_screen` | 让用户手动去项目设置里加 Autoload，用独立窗口代替主屏幕 |

## 数据编辑器做成 Resource

```gdscript
@tool
class_name SpawnRule
extends Resource

enum Kind { ONCE, TIMED }

@export var kind: Kind = Kind.ONCE:
	set(value):
		kind = value
		notify_property_list_changed()
		emit_changed()
@export var interval: float = 1.0:
	set(value):
		interval = value
		emit_changed()
@export var scene: PackedScene

func _validate_property(property: Dictionary) -> void:
	if property.name == "interval" and kind != Kind.TIMED:
		property.usage = PROPERTY_USAGE_NO_EDITOR
```

- 资源加 `@tool`，`_validate_property` 才在编辑器里运行
- `PROPERTY_USAGE_NO_EDITOR` 只隐藏，值照常存盘，数值上等于 `PROPERTY_USAGE_STORAGE`。只读用 `property.usage |= PROPERTY_USAGE_READ_ONLY`
- 整张表用一个数据库资源持有 `Array[SpawnRule]`，Inspector 里直接增删排序，不用写列表控件
- 需要字段重置箭头时重写 `_property_can_revert` 与 `_property_get_revert`
- 想要自己的编辑界面，先问数据是不是图形（对话树 技能树）或空间（地图 关卡）。是才考虑主屏幕插件或 `GraphEdit`，数据仍然存成 `Resource`，界面是另一个编辑入口

## @tool 脚本

```gdscript
@tool
extends Node2D

@export var rule: SpawnRule:
	set(value):
		if rule != null and rule.changed.is_connected(queue_redraw):
			rule.changed.disconnect(queue_redraw)
		rule = value
		if rule != null:
			rule.changed.connect(queue_redraw)
		queue_redraw()

func _draw() -> void:
	if rule != null and Engine.is_editor_hint():
		draw_circle(Vector2.ZERO, 16.0, Color.RED)

func _process(delta: float) -> void:
	if Engine.is_editor_hint():
		return
	position.x += 10.0 * delta
```

- 编辑器里 `@tool` 脚本的 `_process` `_physics_process` `_input` 都会跑。游戏逻辑一律用 `Engine.is_editor_hint()` 挡住
- `@export` 的 setter 在场景加载时、节点进树之前就会调用，里面用子节点要先判断 `is_node_ready()` 或 `is_inside_tree()`
- 改了资源内部属性不会触发持有者的 setter。资源要是 `@tool`，setter 里 `emit_changed()`，持有者连 `changed` 信号，换资源时断开旧的
- `@tool` 脚本用到的其他脚本也要加 `@tool`，否则编辑器里 `load` 到的资源和 `set_script` 挂上的是占位实例，方法不可用，`.new()` 造的实例不受影响。静态方法 常量 枚举不受限，静态变量的初值不执行，带类型的读出类型默认值，无类型的读出 `null`
- 子类脚本不继承父类的 `@tool`，要再写一遍
- 在 `_init` 里读 `@export` 值拿到的是默认值，Inspector 里设的值在 `_init` 之后才赋入
- 脚本代码在编辑器里造成的改动（改节点属性 增删节点）没有撤销，也不会自动把场景标为未保存。批量改动走 `EditorUndoRedoManager`，否则调 `EditorInterface.mark_scene_as_unsaved()`

## 动态属性

按其他数据决定有哪些属性时才重写 `_get_property_list`，配合 `_get` 和 `_set`：

```gdscript
@tool
class_name WaveTable
extends Resource

@export var wave_count: int = 3:
	set(value):
		wave_count = clampi(value, 1, 20)
		counts.resize(wave_count)
		notify_property_list_changed()

var counts: PackedInt32Array = PackedInt32Array([5, 8, 12])

func _get_property_list() -> Array[Dictionary]:
	var props: Array[Dictionary] = []
	for i in wave_count:
		props.append({
			"name": "wave_%d_count" % i,
			"type": TYPE_INT,
			"usage": PROPERTY_USAGE_DEFAULT,
		})
	return props

func _get(property: StringName) -> Variant:
	if property.begins_with("wave_") and property.ends_with("_count"):
		return counts[property.get_slice("_", 1).to_int()]
	return null

func _set(property: StringName, value: Variant) -> bool:
	if property.begins_with("wave_") and property.ends_with("_count"):
		counts[property.get_slice("_", 1).to_int()] = value
		return true
	return false
```

- 这是动态结构的最后手段。每波人数这种可变长度数据，`@export var counts: Array[int]` 更简单，Inspector 原生支持增删
- 把 JSON 的键值用 `_get_property_list` 伪装成属性，又得自己做撤销和存盘。数据本来就该是 `Resource`
- `_get_property_list` 返回的属性要带 `PROPERTY_USAGE_STORAGE` 才会存盘，`PROPERTY_USAGE_DEFAULT` 已包含
- 结构变了必须调 `notify_property_list_changed()`，Inspector 才会重建
- `_validate_property` 不处理 `_get_property_list` 加的属性，这类属性的 `usage` 在返回字典里直接写
- `_get_property_list` 须线程安全，保存资源时可能在别的线程被调用，里面不碰场景树

## Inspector 按钮与校验

```gdscript
@tool
extends Node2D

@export var target: Node2D:
	set(value):
		target = value
		update_configuration_warnings()
@export_tool_button("Snap To Target", "Reload") var snap_action: Callable = snap_to_target

func _get_configuration_warnings() -> PackedStringArray:
	var warnings := PackedStringArray()
	if target == null:
		warnings.append("target 未设置")
	return warnings

func snap_to_target() -> void:
	var ur := EditorInterface.get_editor_undo_redo()
	ur.create_action("Snap To Target", UndoRedo.MERGE_DISABLE, self)
	ur.add_do_property(self, &"global_position", target.global_position)
	ur.add_undo_property(self, &"global_position", global_position)
	ur.commit_action()
```

- `@export_tool_button` 的第二个参数是编辑器内置图标名，不能用工程里的图标
- 按钮回调里的改动走 `EditorUndoRedoManager`，`EditorInterface.get_editor_undo_redo()` 是 4.4+，插件里 `get_undo_redo()` 返回同一个对象
- `_get_configuration_warnings` 是节点的校验入口，脚本须 `@tool`，场景面板显示黄色三角。条件变了调 `update_configuration_warnings()`
- `Resource` 没有警告三角，校验用 tool 按钮加 `push_warning`，或做成导入期检查
- 引用了 `EditorInterface` 的脚本如果也在游戏里运行，导出后解析失败，因为导出模板里没有编辑器类。把编辑器部分拆到只在编辑器加载的脚本里

## 插件

目录 `addons/<名>/plugin.cfg` 加 `plugin.gd`，在 Project Settings 的 Plugins 页启用。骨架 Dock Autoload 主屏幕 主题 快捷键 菜单 文件变化信号 项目设置 EditorScript 撤销的完整写法见 [references/editor-recipes.md](references/editor-recipes.md)。

`EditorPlugin` 的基本约束：

- `_enter_tree` 里注册，`_exit_tree` 里反注册并 `queue_free` 自己建的控件
- 不要在 `_process` 里轮询。用 `EditorInterface.get_resource_filesystem()` 的 `filesystem_changed` 和 `resources_reimported` 信号
- 颜色优先用控件的 `get_theme_color(名, "Editor")`，脱离控件树时用 `EditorInterface.get_editor_theme()`，尺寸乘 `EditorInterface.get_editor_scale()`
- 快捷键用 `Shortcut` 资源
- 多数场合不需要 `add_custom_type`，脚本写 `class_name` 加 `@icon`
- 图标和面板场景用 `res://addons/<名>/...` 完整路径

自定义属性控件和 `EditorInspectorPlugin`：[references/inspector-plugin.md](references/inspector-plugin.md)。

## 导入外部数据

JSON 表格导出文件放进工程自动变成 `Resource`：`EditorImportPlugin`。自定义后缀，`_import` 里解析并 `ResourceSaver.save`，游戏里 `load` 源文件路径直接得到资源。完整可运行的导入器、选项、平台变体、`EditorScenePostImport` 见 [references/import-plugin.md](references/import-plugin.md)。

数据很少改时不必写导入器，一个 `EditorScript` 一次转换，见 godot-resources-data 的 `references/baking-data.md`。

## C# 的 [Tool] 与热重载

- 改了 C# 代码要点 Build，`[Tool]` 脚本才用上新代码；新增的导出成员和信号也要先 Build 才出现
- 热重载时只有 `[Export]` 变量的值被保留，其他状态不保证
- 存着 `Callable` 的字段或带后备字段的属性可能挡住程序集卸载。`[ExportToolButton]` 必须是表达式体属性，否则报 GD0111
- 官方文档没有说明静态字段在重载后的行为，`[Tool]` 类里少放静态缓存
- 订阅了信号或事件的 `[Tool]` 类，在 `_ExitTree` 里取消订阅
- 编辑器单例在 C# 里经 Singleton 属性访问，如 `EditorInterface.Singleton.GetEditedSceneRoot()`
- C# 的 `EditorScript` 要出现在命令面板须同时写 `[GlobalClass]` 和 `[Tool]`
- C# 的 `EditorScript` 不能从脚本编辑器运行，用文件系统右键 Run 或命令面板

## 陷阱

- `@tool` 脚本里写了会改节点的游戏逻辑，打开场景就修改并存盘。先 `Engine.is_editor_hint()` 挡住
- 编辑器里 `add_child` 的节点不设 `owner` 既不显示也不存盘。`owner` 设成当前编辑场景根，用 `EditorInterface.get_edited_scene_root()`
- 不要改场景实例的子节点。重载场景时改动丢失，判断 `node == EditorInterface.get_edited_scene_root()` 或 `node.owner == EditorInterface.get_edited_scene_root()` 再改
- 导入器和 Inspector 插件用到的 `class_name` 脚本漏了 `@tool`
- 导入器用 `json` `txt` 这类常见后缀，和内置导入器抢文件。自定义后缀
- 插件 `_exit_tree` 没有反注册，关闭再启用后出现重复的面板和菜单
- 颜色写死，换亮色主题后看不见
- 用 `_process` 轮询文件变化，空耗 CPU 且有延迟
- 用 JSON 加 `_get_property_list` 伪装 Inspector，撤销和存盘全要自己做。数据改成 `Resource`
- `EditorInterface` 引用泄漏进游戏脚本，导出后解析失败
- 在 `_init` 里读 `@export` 值得到默认值，改到 `_ready` 或 setter 里

## 参考

- [references/export-annotations.md](references/export-annotations.md)：`@export_*` 注解一览，C# 特性对照
- [references/inspector-plugin.md](references/inspector-plugin.md)：`EditorInspectorPlugin` 与 `EditorProperty`
- [references/import-plugin.md](references/import-plugin.md)：`EditorImportPlugin` 与 `EditorScenePostImport`
- [references/editor-recipes.md](references/editor-recipes.md)：插件骨架 Dock Autoload 主屏幕 主题 快捷键 菜单 文件变化 项目设置 EditorScript 撤销 C# 插件
- 官方文档：https://docs.godotengine.org/en/stable/tutorials/plugins/running_code_in_the_editor.html
- 官方文档：https://docs.godotengine.org/en/stable/tutorials/plugins/editor/index.html
