# GDScript 警告全表

项目设置路径 `debug/gdscript/warnings/<名字>`，值 0 忽略、1 警告、2 错误。`debug/gdscript/warnings/enable` 为 `false` 时全部关闭。默认值取自 4.7 的 `ProjectSettings` 文档。

文件内忽略用 `@warning_ignore("名字")`，名字同下表。

| 名字 | 默认 | 含义 | 常见处理 |
|---|---|---|---|
| `assert_always_false` | 1 | `assert` 条件恒假 | 删或改成 `push_error` |
| `assert_always_true` | 1 | `assert` 条件恒真 | 删 |
| `confusable_capture_reassignment` | 1 | lambda 里重新赋值捕获的局部变量，外层不变 | 改用 Array 或 Dictionary 承载 |
| `confusable_identifier` | 1 | 标识符混用易混淆的字符 | 改名 |
| `confusable_local_declaration` | 1 | 嵌套块里声明的名字与父块后面声明的同名 | 改名 |
| `confusable_local_usage` | 1 | 使用了块内稍后会被遮蔽的标识符 | 改名 |
| `confusable_temporary_modification` | 1 | 对内置属性的 `Packed*Array` 做链式赋值或非 const 方法调用，改的是临时副本 | 取到局部变量，改完写回 |
| `deprecated_keyword` | 1 | 已弃用关键字，目前没有 | 无 |
| `directory_rules` | `{ "res://addons": 0 }` | 按目录排除或包含警告，值 0 排除 1 包含，取最深的匹配目录 | 第三方目录设 0 |
| `empty_file` | 1 | 空文件 | 删文件 |
| `enum_variable_without_default` | 1 | 枚举类型变量无初值且枚举里没有 0 | 写初值 |
| `get_node_default_without_onready` | 2 | 成员默认值里用 `$` 或 `get_node()` 没加 `@onready` | 加 `@onready` |
| `incompatible_ternary` | 1 | 三元表达式两支类型不兼容 | 统一类型 |
| `inference_on_variant` | 2 | `:=` 的右值是 Variant | 写显式类型 |
| `inferred_declaration` | 0 | 用了 `:=` 推断 | 只在要求显式类型的项目里开 |
| `int_as_enum_without_cast` | 1 | 整数当枚举用没有显式转换 | 用枚举成员或 `as` |
| `int_as_enum_without_match` | 1 | 整数当枚举用但没有对应成员 | 修正值 |
| `integer_division` | 1 | 整数除整数丢小数 | `/ 2.0` 或 `float()`，有意整除时 `@warning_ignore("integer_division")` |
| `missing_await` | 0 | 调用协程没写 `await` | 建议开到 2 |
| `missing_tool` | 1 | 基类脚本是 `@tool` 而当前脚本不是 | 加 `@tool` |
| `narrowing_conversion` | 1 | 浮点传给整数参数 | `int()` `roundi()` `floori()` |
| `native_method_override` | 2 | 脚本里的方法覆盖了引擎原生方法 | 改名 |
| `onready_with_export` | 2 | `@onready` 与 `@export` 同用 | 二选一 |
| `redundant_await` | 1 | 对非协程用了 `await` | 去掉 `await` |
| `redundant_static_unload` | 1 | 没有静态变量却写了 `@static_unload` | 去掉 |
| `return_value_discarded` | 0 | 丢弃了函数返回值，`connect()` 也算 | 想严格时开，配合 `@warning_ignore` |
| `shadowed_global_identifier` | 1 | 变量、信号、枚举与内置函数或全局类同名 | 改名 |
| `shadowed_variable` | 1 | 局部变量遮蔽当前类成员 | 改名 |
| `shadowed_variable_base_class` | 1 | 局部变量遮蔽基类成员 | 改名 |
| `standalone_expression` | 1 | 无效果的独立表达式如 `2 + 2` | 删 |
| `standalone_ternary` | 1 | 无效果的独立三元表达式 | 改成 if |
| `static_called_on_instance` | 1 | 用实例调静态方法 | 用类名调 |
| `unassigned_variable` | 1 | 使用未赋值的变量 | 赋初值 |
| `unassigned_variable_op_assign` | 1 | 对未赋值的变量用 `+=` 等 | 赋初值 |
| `unreachable_code` | 1 | 不可达代码 | 删 |
| `unreachable_pattern` | 1 | 不可达的 match 分支 | 删或调序 |
| `unsafe_call_argument` | 0 | 参数类型不保证兼容 | 加 `as` 或显式类型 |
| `unsafe_cast` | 0 | Variant 转成非 Variant | 加类型检查 |
| `unsafe_method_access` | 0 | 调用编译期不保证存在的方法 | 改用具体类型或 `has_method()` |
| `unsafe_property_access` | 0 | 访问编译期不保证存在的属性 | 同上 |
| `unsafe_void_return` | 1 | 在 void 函数里返回不保证是 void 的调用 | 拆成两行 |
| `untyped_declaration` | 0 | 变量、参数、返回值无类型 | 全类型化项目开到 2 |
| `unused_local_constant` | 1 | 局部常量未使用 | 删 |
| `unused_parameter` | 1 | 参数未使用 | 加 `_` 前缀 |
| `unused_private_class_variable` | 1 | 私有成员变量未使用 | 删 |
| `unused_signal` | 1 | 信号声明后类内没有任何使用 | 外部发射的加 `@warning_ignore` |
| `unused_variable` | 1 | 局部变量未使用 | 删 |

## 抓不到的警告

命令行运行默认不打印级别 1 的警告，加 `--debug` 才打印，如 `godot --headless --debug` 加载脚本，但它遇到解析错误崩溃、运行时错误停在 `debug>` 提示符，自动化里把警告设成 2 来抓，做法见 godot-headless-testing。级别 2 的错误任何时候都会打印并让脚本加载失败。
