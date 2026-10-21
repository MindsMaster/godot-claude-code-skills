# EditorInspectorPlugin

注解和 `_validate_property` 解决不了的显示需求才写它：某个属性要换成自定义控件，或者在某类对象的 Inspector 顶部放一块自定义界面。

## 结构

- `EditorInspectorPlugin`：判断处理哪类对象，在属性列表里插入控件
- `EditorProperty`：单个属性的编辑控件，负责显示当前值，值变了发 `emit_changed`
- 插件的 `_enter_tree` 里 `add_inspector_plugin`，`_exit_tree` 里 `remove_inspector_plugin`

## 自定义属性控件

```gdscript
@tool
class_name ItemData
extends Resource

@export var id: StringName
@export var price: int
```

```gdscript
@tool
extends EditorProperty

var _spin: EditorSpinSlider = EditorSpinSlider.new()
var _updating: bool = false

func _init() -> void:
	_spin.step = 1.0
	_spin.max_value = 9999.0
	add_child(_spin)
	add_focusable(_spin)
	_spin.value_changed.connect(_on_value_changed)

func _update_property() -> void:
	var value: int = get_edited_object()[get_edited_property()]
	_updating = true
	_spin.value = value
	_updating = false

func _on_value_changed(value: float) -> void:
	if _updating:
		return
	emit_changed(get_edited_property(), int(value))
```

```gdscript
@tool
extends EditorInspectorPlugin

func _can_handle(object: Object) -> bool:
	return object is ItemData

func _parse_property(_object: Object, _type: Variant.Type, name: String, _hint_type: PropertyHint, _hint_string: String, _usage_flags: int, _wide: bool) -> bool:
	if name == "price":
		add_property_editor(name, load("res://addons/items/price_editor.gd").new())
		return true
	return false
```

```gdscript
@tool
extends EditorPlugin

var _inspector: EditorInspectorPlugin

func _enter_tree() -> void:
	_inspector = load("res://addons/items/item_inspector.gd").new()
	add_inspector_plugin(_inspector)

func _exit_tree() -> void:
	remove_inspector_plugin(_inspector)
	_inspector = null
```

- `_parse_property` 返回 `true` 表示替换内置编辑器，返回 `false` 表示在内置编辑器之前插入自定义控件，两者都保留
- 值变化只通过 `emit_changed(property, value)` 提交，编辑器据此写属性并登记撤销，不要自己 `object.set`
- `_update_property` 在值被别处改动时调用，更新控件时加一个标志位，避免回写触发 `emit_changed`
- 处理对象的类判断用 `object is ItemData`，被判断的脚本要加 `@tool`
- `_parse_begin(object)` 在属性列表最前面、`_parse_end(object)` 在最后，用 `add_custom_control` 放按钮或预览
- `_parse_category` 和 `_parse_group` 在遇到分类和分组标题时调用，用来跳过或替换整组
- `add_property_editor_for_multiple_properties` 让一个控件同时编辑几个相关属性，如 min 和 max

## 路径要点

- 引用同插件目录的脚本时写完整 `res://addons/<名>/...`
