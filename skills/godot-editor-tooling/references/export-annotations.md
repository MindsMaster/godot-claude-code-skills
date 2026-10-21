# 导出注解一览

`@export` 系列决定 Inspector 里怎么显示一个属性。能用注解解决的显示需求，不要写 `EditorInspectorPlugin`。

## 对照

| 注解 | 类型 | 效果 |
|---|---|---|
| `@export` | 任意可导出类型 | 默认编辑器，`Resource` `Node` `enum` `Array[T]` 自动识别 |
| `@export_range(min, max, step, hints)` | `int` `float` 及数组 | 滑块。`"or_greater"` `"or_less"` 不封顶，`"exp"` 指数，`"degrees"` `"radians_as_degrees"` 角度，`"suffix:px"` 单位，`"prefer_slider"` 整数用滑块，`"hide_control"` 隐藏数值控件 |
| `@export_enum("A", "B:5")` | `int` `String` | 下拉。`int` 存下标或冒号后的值，具名 `enum` 直接用 `@export` |
| `@export_flags("A", "B:4")` | `int` | 位标志复选。冒号值不继承前一项 |
| `@export_flags_2d_physics` 等 | `int` | 图层选择器，另有 `_2d_render` `_2d_navigation` `_3d_physics` `_3d_render` `_3d_navigation` `_avoidance` |
| `@export_file("*.json")` | `String` | 工程内文件选择，有 uid 时存 uid，文件移动后仍有效 |
| `@export_file_path` | `String` | 同上但存裸路径（4.5+） |
| `@export_dir` | `String` | 工程内目录选择 |
| `@export_global_file` `@export_global_dir` | `String` | 整个文件系统的绝对路径 |
| `@export_multiline` | `String` | 多行文本框 |
| `@export_placeholder("hint")` | `String` | 空值时的灰色提示 |
| `@export_color_no_alpha` | `Color` | 隐藏 alpha |
| `@export_exp_easing("attenuation")` | `float` | 缓动曲线控件 |
| `@export_node_path("Marker2D")` | `NodePath` | 限定类型的节点路径选择 |
| `@export_group("名", "前缀")` | 标记 | 之后的属性归入折叠组。给前缀时只收带该前缀的属性，并在显示时去掉前缀 |
| `@export_subgroup` | 标记 | 组内的子组，必须先有 `@export_group` |
| `@export_category("名")` | 标记 | 顶层分类标题，官方建议优先用组和子组 |
| `@export_storage` | 任意 | 保存进文件但不显示，`duplicate()` 时会被复制 |
| `@export_custom(hint, hint_string, usage)` | 任意 | 直接传 `PropertyHint`，GDScript 不校验 |
| `@export_tool_button("名", "图标")` | `Callable` | Inspector 按钮（4.4+），图标是编辑器内置图标名，如 `Reload` |
| `@icon("res://x.svg")` | 类 | 给 `class_name` 类指定节点或资源图标，参数只能是字符串字面量，写在 `class_name` 和 `extends` 之前 |
| `@abstract` | 类 方法 | 抽象类，不能直接实例化（4.5+） |

## 完整示例

```gdscript
@tool
class_name SkillDef
extends Resource

@export_category("基础")
@export var title: String = ""
@export_multiline var description: String = ""
@export_placeholder("skill_id") var id: String = ""
@export_enum("Fire", "Water", "Earth") var element: String = "Fire"

@export_group("数值")
@export_range(0.0, 100.0, 0.5, "suffix:%") var chance: float = 10.0
@export_range(0, 360, 1, "degrees") var angle: float = 0.0
@export_flags("Self:1", "Allies:2", "Foes:4") var targets: int = 0
@export_flags_2d_physics var hit_mask: int = 0
@export_exp_easing("attenuation") var falloff: float = 1.0

@export_group("引用")
@export_file("*.json") var source: String = ""
@export_dir var folder: String = ""
@export_node_path("Marker2D") var anchor: NodePath
@export_color_no_alpha var tint: Color = Color.WHITE

@export_group("高级", "adv_")
@export var adv_cooldown: float = 1.0
@export var adv_cost: int = 1

@export_group("")
@export_storage var format_version: int = 1
@export_custom(PROPERTY_HINT_RANGE, "0,10,1,or_greater") var level: int = 1
@export_tool_button("Validate", "Reload") var validate_action: Callable = validate

func validate() -> void:
	if id.is_empty():
		push_warning("%s 缺少 id" % title)
```

- 同一个脚本里 `@export_group` 一直生效到下一个组或分类，或 `@export_group("")`
- 带前缀的组只吃连续的、带前缀的属性，遇到第一个不带前缀的属性就结束
- 导出的 `Array[T]` 里 `T` 是 `Resource` 子类时，Inspector 提供新建、拖入、内嵌三种方式
- `@export var x = 1` 由初值推断类型，既无类型又无初值的 `@export var x` 报解析错误

## C# 对应

| GDScript | C# |
|---|---|
| `@export` | `[Export]` |
| `@export_range(0, 100, 1)` | `[Export(PropertyHint.Range, "0,100,1")]` |
| `@export_enum("A", "B")` | `[Export(PropertyHint.Enum, "A,B")]` |
| `@export_file("*.json")` | `[Export(PropertyHint.File, "*.json")]` |
| `@export_group("名", "前缀")` | `[ExportGroup("名", "前缀")]` |
| `@export_subgroup` | `[ExportSubgroup("名")]` |
| `@export_category` | `[ExportCategory("名")]` |
| `@export_tool_button("名", "图标")` | `[ExportToolButton("名", Icon = "图标")]`，类上要 `[Tool]` |

```csharp
[Tool]
[GlobalClass]
public partial class SkillDef : Resource
{
    [ExportCategory("基础")]
    [Export] public string Title { get; set; } = "";

    [ExportGroup("数值")]
    [Export(PropertyHint.Range, "0,100,0.5,suffix:%")]
    public float Chance { get; set; } = 10f;

    [ExportToolButton("Validate")]
    public Callable ValidateAction => Callable.From(Validate);

    public void Validate()
    {
        GD.Print("validate");
    }
}
```

`[ExportToolButton]` 必须写成表达式体属性，不能有存 `Callable` 的后备字段，否则报 GD0111，原因是 `Callable` 可能挡住程序集卸载。不能与 `[Export]` 同用，类上没有 `[Tool]` 也报错。
