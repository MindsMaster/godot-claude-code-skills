# GDScript 注解全表

SKILL.md 讲了用法和陷阱，这里按类别列注解。示例是片段，类型写法按 `docs.godotengine.org` 的导出页。

## 导出

| 需求 | 写法 |
|---|---|
| 基本类型 | `@export var speed: float = 200.0`，类型来自标注或默认值 |
| 数值范围 | `@export_range(0, 100, 1)`，附加提示 `"or_less"` `"or_greater"` `"exp"` `"hide_slider"` `"prefer_slider"` `"suffix:m"` `"radians_as_degrees"` `"degrees"` |
| 枚举类型 | `@export var state: State`，存整数 |
| 整数或字符串枚举 | `@export_enum("Idle", "Run") var mode: int`，类型写 `String` 时存字符串；`"Slow:30"` 指定值 |
| 位标志 | `@export_flags("Fire", "Water")`，值依次为 1 2 4，`"Self:4"` 指定值，只允许 2 的幂 |
| 物理渲染层 | `@export_flags_2d_physics`、`_2d_render`、`_2d_navigation`、`_3d_physics`、`_3d_render`、`_3d_navigation`、`@export_flags_avoidance` |
| 文件与目录 | `@export_file("*.tscn")`、`@export_dir`、`@export_file_path` 4.5+；全局路径 `@export_global_file`、`@export_global_dir` 只在 `@tool` 脚本里可用 |
| 多行文本 | `@export_multiline var text: String` |
| 占位文本 | `@export_placeholder("hint") var s: String` |
| 颜色 | `@export var c: Color`，无 alpha 用 `@export_color_no_alpha` |
| 缓动曲线 | `@export_exp_easing var curve: float` |
| 节点引用 | `@export var node: Node`，可写具体类或 `class_name` 类，仅 Node 派生脚本 |
| 节点路径 | `@export_node_path("Button", "Control") var p: NodePath` |
| 资源 | `@export var res: Resource`，写子类缩小下拉列表 |
| 延迟加载的资源 | `@export_file("*.tscn") var level: String`，用时 `load()` |
| 数组 | `@export var items: Array[Item] = []`、`Array[PackedScene]`、`Array[int]` |
| 输入动作名 | `@export_custom(PROPERTY_HINT_INPUT_NAME, "show_builtin") var action: StringName`，4.5+ |
| 联动向量 | `@export_custom(PROPERTY_HINT_LINK, "suffix:px") var size: Vector2` |
| 只存不显示 | `@export_storage var cache: int`，保存进场景，复制时也被复制 |
| 自定义提示 | `@export_custom(hint, hint_string, usage)`，不做校验，原样传给编辑器 |
| Inspector 按钮 | `@export_tool_button("Bake", "Callable") var bake := _bake`，4.4+，需 `@tool` |

分组：

```gdscript
@export_category("Main")
@export_group("Combat", "combat_")
@export var combat_damage := 1
@export_subgroup("Ranged", "combat_ranged_")
@export var combat_ranged_range := 5.0
```

- `@export_group` 之后的导出都属于该组，`@export_group("")` 退出。第二参数是属性名前缀，Inspector 里省略该前缀
- 组不能嵌套，子组用 `@export_subgroup`
- 开关整个组的布尔属性用 `@export_custom(PROPERTY_HINT_GROUP_ENABLE, "")`，4.5+，名字以 `_enabled` 结尾

## 导出的约束

- 导出的变量需要有常量初值或类型标注
- 导出 Resource 时，场景加载就把该资源当依赖一起加载。大关卡场景、可选内容用 `@export_file` 存路径，用时再加载
- 非 `@tool` 脚本在编辑器里不执行，Inspector 修改导出变量时 setter 与 getter 也不运行
- `Array[Array]` 之类嵌套类型可导出，但 Inspector 对元素类型提示有限
- 在 `Resource` 里导出 `Node` 是解析错误

## 其他注解

| 注解 | 作用 |
|---|---|
| `@onready` | 在 `_ready()` 之前赋值。不能用于 `static var`，不能与 `@export` 同用 |
| `@tool` | 脚本在编辑器里运行。被它引用的静态变量所在脚本也要是 `@tool` |
| `@icon("res://x.svg")` | 给 `class_name` 类指定图标 |
| `@static_unload` | 放在文件最顶、`class_name` 之前，允许卸载带静态变量的脚本，当前有已知问题 |
| `@warning_ignore("name")` | 忽略下一条语句的指定警告，名字同项目设置名 |
| `@warning_ignore_start("name")` / `@warning_ignore_restore("name")` | 区域忽略，省略 restore 则到文件末 |
| `@rpc` | 多人网络 RPC 方法标注 |
| `@abstract` | 抽象类或抽象方法，4.5+ |

## 4.5+ 语法

- 可变参数函数 `func sum(...values: Array) -> int:`，4.5+
- `@abstract class Shape:` 与 `@abstract func area() -> float`，4.5+
