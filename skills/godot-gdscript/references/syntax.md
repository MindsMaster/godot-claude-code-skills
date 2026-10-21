# GDScript 语法速查

match、静态成员、内部类、StringName、setter getter、super 的最短写法与规则。

## match

```gdscript
extends Node

enum State { IDLE, RUN, JUMP }

func describe(state: State, data: Variant) -> String:
	match state:
		State.IDLE, State.RUN:
			return "ground"
		State.JUMP:
			return "air"
	match data:
		[var x, var y]:
			return "pair %s %s" % [x, y]
		{"type": "hit", "damage": var d}:
			return "hit %s" % d
		var n when n is int and n > 10:
			return "big"
		_:
			return "other"
```

- 无贯穿，不写 `break`。3.x 的 `continue` 贯穿行为在 4.0 移除
- 模式有常量、`var x` 绑定、`_` 通配、数组与字典结构、逗号分隔多个、`when` 守卫
- 排在通配之后或被前面完全覆盖的分支触发 `unreachable_pattern`
- `String` 与 `StringName` 比较相等，`match name:` 里 `&"run"` 能匹配 `"run"`

## static 与内部类

```gdscript
extends RefCounted

class Hit:
	var damage: int

	func _init(d: int) -> void:
		damage = d

static var created: int = 0

static func make(d: int) -> Hit:
	created += 1
	return Hit.new(d)
```

- `static var` 4.1+，属于类，所有实例共享，不能 `@export` 或 `@onready`，局部变量不能 `static`
- 子类通过 `B.x` 访问到的是基类同一份静态变量
- `static func` 里不能用实例成员。用实例调静态方法触发 `static_called_on_instance`
- `static func _static_init()` 在类加载后、静态变量初始化完成后自动调用
- 带静态变量的脚本不会被卸载。持有大资源时手动清空，或在文件最顶加 `@static_unload`，当前版本有已知问题，脚本仍不释放
- `@tool` 脚本引用的静态变量所在脚本也必须是 `@tool`
- 内部类不写 `extends` 时是 `RefCounted`。外部用 `Outer.Hit` 引用。Inspector 不认内部类

## StringName 与 NodePath

- `&"idle"` 是 `StringName` 字面量，`^"Path/To"` 是 `NodePath` 字面量
- 动画名、分组名、输入动作名、方法名用 `&""`。引擎 API 参数本来就是 `StringName`，字符串字面量每次调用要转换一次
- `&"x" == "x"` 为真，字典里 `&"a"` 与 `"a"` 作键互通
- `$Path` 是 `get_node(^"Path")` 的简写，路径含空格写 `$"A B"`，唯一名写 `%Name`

## setter getter

```gdscript
extends Node

signal health_changed(value: int)

@export var max_health: int = 100
var health: int = max_health:
	set(value):
		health = clampi(value, 0, max_health)
		health_changed.emit(health)

var ratio: float:
	get:
		return float(health) / max_health
```

- 声明初值不调 setter。类内其他方法里写 `health = 5` 会调 setter，setter 内部写 `health = ...` 直接赋值不递归
- 只写 `get` 是计算属性，不占存储
- 指向已有方法的写法：`var x: int: set = set_x, get = get_x`
- 导出变量的 setter 在场景实例化时先于 `_ready()` 调用，此时 `@onready` 变量是 `null`，setter 里判断 `is_node_ready()`，非 `@tool` 脚本在编辑器里改导出值时 setter 不运行

## super

```gdscript
extends Node

class Enemy extends Node:
	var hp: int = 10

	func _init(start_hp: int = 10) -> void:
		hp = start_hp

	func _ready() -> void:
		print("enemy ready")

class Boss extends Enemy:
	func _init() -> void:
		super(500)

	func _ready() -> void:
		super()
		print("boss ready")
```

- 子类写了 `_init()` 不会自动调用父类 `_init()`，父类 `_init` 有必填参数时子类必须写 `super(args)`
- `_ready()` `_process()` 等虚函数同理，父类里有逻辑要显式 `super()`
- 调用父类的另一个方法写 `super.other(args)`

## 可变参数与抽象类 4.5+

```gdscript
@abstract class Shape:
	@abstract func area() -> float

class Square extends Shape:
	var side: float = 2.0

	func area() -> float:
		return side * side

func total(...values: Array) -> float:
	var sum: float = 0.0
	for v: float in values:
		sum += v
	return sum
```

- `@abstract` 类不能实例化，有抽象方法的类必须也是 `@abstract`，子类要么实现全部抽象方法，要么自己也标 `@abstract`
- 可变参数 `...args`，调用时不支持展开语法，用 `callv()` 传数组
