# 生命周期 owner 与延迟调用

SKILL.md 的陷阱一节指到这里时读，手写 `.tscn` 里的节点引用也在这里。

## 回调选择

| 回调 | 触发 | 用来做 |
|---|---|---|
| `_init` | 对象构造，`@export` 值还没到 | 只初始化纯数据字段 |
| `_enter_tree` | 进树，父先于子 | 向外注册，`@export` 节点引用此时可用 |
| `_ready` | 本节点和所有子节点都进树之后，子先于父，一生一次 | 取子节点、连信号、初始化状态 |
| `_exit_tree` | 出树，子先于父 | 与 `_enter_tree` 成对的反注册 |
| `tree_exited` 信号 | 已经出树 | 出树后才能做的清理 |

- `@onready var` 在 `_ready` 之前赋值，所以 `_ready` 里可以直接用
- `_ready` 只在第一次进树时调用。`remove_child` 后再 `add_child` 不会重来，要重来先调 `request_ready()`
- `reparent(new_parent)` 会出树再进树，`_enter_tree` 和 `_exit_tree` 各走一次，`_ready` 不走
- 需要等子场景就绪时，在父里 `await child.ready`，或者让子在 `_ready` 末尾发信号
- 成对的东西用成对的回调：`_enter_tree` 里 `connect`，`_exit_tree` 里 `disconnect`。`_ready` 里连、节点只进树一次的情况不用断开

## 构造期设值的顺序

```gdscript
extends Node

@export var scene: PackedScene

func spawn(parent: Node, label_text: String) -> void:
	var inst := scene.instantiate()
	inst.set("label_text", label_text)
	parent.add_child(inst)
```

`instantiate()` 后、`add_child` 前设置的值，目标节点的 `_enter_tree` 和 `_ready` 都能读到。`add_child` 之后设，`_ready` 已经跑完。

脚本类型已知时直接转型赋值，比 `set` 好：`var enemy := scene.instantiate() as Enemy`。

## owner

`owner` 影响保存和编辑器显示，运行时只有 `%UniqueName` 查找和 `find_child` 默认的 `owned` 过滤用到它。

- 编辑器里摆好的节点，`owner` 是场景根；子场景实例里的节点，`owner` 是那个实例的根
- 代码 `add_child` 的节点 `owner` 为 `null`，不会被 `PackedScene.pack` 打包，在编辑器里 `@tool` 脚本生成的节点也不会出现在场景面板
- 要打包或在编辑器显示：`child.owner = root`，`root` 是要保存的那个场景根，不是直接父节点
- `%Name` 查找以调用节点所在的 owner 为范围。`owner` 为 `null` 的节点查不到，设了 `owner` 才生效，与 `unique_name_in_owner` 的设置先后无关

```gdscript
extends Node

func build() -> PackedScene:
	var root := Node2D.new()
	var child := Sprite2D.new()
	root.add_child(child)
	child.owner = root
	var packed := PackedScene.new()
	packed.pack(root)
	root.free()
	return packed
```

更深的后代也要逐个设 `owner`，设一个根节点的直接子节点不够。

## 手写 .tscn 的节点引用

脚本里 `@export` 的类型是 `Node` 或其子类时，节点头必须写 `node_paths`，列出这些属性名，属性行写 `NodePath`。漏写时场景加载不报错，属性运行期为 `null`，用到时才报错。

```ini
[node name="Hud" type="Node" parent="." node_paths=PackedStringArray("player", "targets")]
script = ExtResource("1")
player = NodePath("../Player")
targets = [NodePath("../Player"), NodePath("../Enemy")]
```

- 路径相对这个节点自己，不相对场景根
- 实例化的子场景在宿主场景里覆盖节点引用，节点头同样要写：`[node name="Hud" parent="." node_paths=PackedStringArray("player") instance=ExtResource("1")]`
- 漏写 `player`：4.7.2 实测属性为 `null`，访问 `player.name` 报 `Invalid access to property or key 'name' on a base object of type 'Nil'.`
- `Array[Node]` 同理。漏写时数组为空，加载时报 `Unable to convert array index 0 from "NodePath" to "Object".`
- `node_paths` 少列一个，这一个就是 `null`，其余正常
- `@export var p: NodePath` 和 `@export_node_path` 的属性存的就是路径，不进 `node_paths`
- 拿不准格式时，用无头脚本 `pack` 再 `ResourceSaver.save` 存一份，照引擎写出的抄

## 必须 call_deferred 的场合

| 场合 | 症状 | 写法 |
|---|---|---|
| 物理回调里增删碰撞体、改 `disabled` `monitoring` | `Can't change this state while flushing queries` | `shape.set_deferred("disabled", true)` |
| 子节点 `_ready` 里给父节点 `add_child` | `Parent node is busy setting up children` | `get_parent().add_child.call_deferred(node)` |
| `_exit_tree` 或遍历子节点时改子节点列表 | `Parent node is busy removing children` | `remove_child.call_deferred(node)` |
| 工作线程里改场景树 | 崩溃或随机报错 | `call_deferred` 回主线程 |

```gdscript
extends Area2D

@export var drop_scene: PackedScene

func _ready() -> void:
	body_entered.connect(_on_body_entered)

func _on_body_entered(_body: Node2D) -> void:
	set_deferred("monitoring", false)
	var drop := drop_scene.instantiate() as Node2D
	get_parent().add_child.call_deferred(drop)
	drop.set_deferred("global_position", global_position)
```

- 想等本帧树改动全部落定再读结果，用 `await get_tree().process_frame`
- 其他场合不要用 `call_deferred`。它让时序难读，只在上面几种有报错或确有同帧冲突时用
- `Object.set_deferred` 和 `Object.call_deferred` 是 `Object` 上的方法，所有节点都有
- 带参数的写法用 `Callable.call_deferred(args)`，比字符串名字少一次拼写错误

C# 对应：

```csharp
public partial class Pickup : Area2D
{
    [Export] public PackedScene DropScene { get; set; }

    public override void _Ready()
    {
        BodyEntered += OnBodyEntered;
    }

    private void OnBodyEntered(Node2D body)
    {
        SetDeferred(Area2D.PropertyName.Monitoring, false);
        var drop = DropScene.Instantiate<Node2D>();
        GetParent().CallDeferred(Node.MethodName.AddChild, drop);
        drop.SetDeferred(Node2D.PropertyName.GlobalPosition, GlobalPosition);
    }
}
```

## 释放与失效引用

| 做法 | 行为 |
|---|---|
| `queue_free()` | 帧末释放，安全。子树一起释放 |
| `free()` | 立即释放。节点在回调或信号发射中被锁定时报错，别对树内节点用 |
| `remove_child(n)` | 只出树，不释放，`n` 变成孤儿，要自己 `free` 或重新挂回，`owner` 不再是祖先时被清成 `null` |
| `new()` 创建后没 `add_child` | 同样是孤儿，不用就 `free` |

- `is_instance_valid(x)` 判断对象是否已释放。刚 `queue_free` 的节点在帧末之前仍然有效，要排除用 `x.is_queued_for_deletion()`
- 持有其他节点引用的成员变量在对方释放后会变成无效引用，访问时报 `previously freed`。办法：监听对方的 `tree_exiting` 清空，或者每次使用前 `is_instance_valid`
- 遍历子节点逐个释放：`for c in get_children(): c.queue_free()`。`get_children()` 返回副本，边遍历边释放安全
- `await` 期间自己被释放，函数不会恢复；被 `await` 的信号所属对象被释放，信号不会再发，函数一直挂起；自己只是出树时会恢复，恢复后先 `if not is_inside_tree(): return`
- 调试内存泄漏，仅 debug 构建：退出时的 `ObjectDB instances leaked` 警告，用 `Node.print_orphan_nodes()` 或 `--verbose` 找孤儿
