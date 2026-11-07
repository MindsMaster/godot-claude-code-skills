# 生命周期 owner 与延迟调用

回调顺序、构造期设值、`owner`、手写 `.tscn` 的节点引用、`call_deferred`、释放与失效引用。

## 回调

| 回调 | 触发 | 用来做 |
|---|---|---|
| `_init` | 对象构造，`@export` 值未到 | 初始化纯数据字段 |
| `_enter_tree` | 进树，父先于子 | 向外注册，`@export` 节点引用已可用 |
| `_ready` | 自己和所有子节点进树后，子先于父，一生一次 | 取子节点、连信号、初始化状态 |
| `_exit_tree` | 出树，子先于父 | 与 `_enter_tree` 成对的反注册 |
| `tree_exited` 信号 | 已出树 | 出树后才能做的清理 |

| 操作 | `_enter_tree` `_exit_tree` | `_ready` |
|---|---|---|
| 首次 `add_child` | 走 | 走 |
| `remove_child` 后再 `add_child` | 走 | 不走，先调 `request_ready()` 才走 |
| `reparent(new_parent)` | 各走一次 | 不走 |

- `@onready` 变量在 `_ready` 之前赋值
- 等子场景就绪：父里 `await child.ready`，或子在 `_ready` 末尾发信号
- `_enter_tree` 里 `connect` 的，在 `_exit_tree` 里 `disconnect`
- `_ready` 里连接、节点只进树一次的，不用断开

## 构造期设值

`instantiate()` 后、`add_child` 前设的值，`_enter_tree` 和 `_ready` 都能读到。`add_child` 后再设，`_ready` 已跑完。

```gdscript
extends Node

@export var scene: PackedScene

func spawn(parent: Node, label_text: String) -> void:
	var inst := scene.instantiate()
	inst.set("label_text", label_text)
	parent.add_child(inst)
```

```csharp
public partial class Card : Node
{
    public string LabelText { get; set; } = "";
}

public partial class CardSpawner : Node
{
    [Export] public PackedScene Scene { get; set; }

    public void Spawn(Node parent, string labelText)
    {
        var inst = Scene.Instantiate<Card>();
        inst.LabelText = labelText;
        parent.AddChild(inst);
    }
}
```

- 脚本类型已知时转型后直接赋值，如 `scene.instantiate() as Enemy`，比 `set` 少拼写错误

## owner

`owner` 决定节点是否随场景存盘、是否出现在编辑器场景面板。运行时只有 `%UniqueName` 和 `find_child` 的 `owned` 过滤用到它。

| 节点来源 | `owner` |
|---|---|
| 编辑器里摆的节点 | 场景根 |
| 子场景实例内部的节点 | 该实例的根 |
| 代码 `add_child` 的节点 | `null` |

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

```csharp
public partial class SceneBuilder : Node
{
    public PackedScene Build()
    {
        var root = new Node2D();
        var child = new Sprite2D();
        root.AddChild(child);
        child.Owner = root;
        var packed = new PackedScene();
        packed.Pack(root);
        root.Free();
        return packed;
    }
}
```

- `owner` 为 `null` 的节点不进 `PackedScene.pack`，不出现在场景面板
- `owner` 设为要保存的场景根，不是直接父节点
- 每个后代都要设，只设直接子节点不够
- `%Name` 以调用节点的 owner 为范围，`owner` 为 `null` 时查不到
- `%Name` 查找与 `unique_name_in_owner` 和 `owner` 的设置先后无关

## 手写 .tscn 的节点引用

`@export` 类型是 `Node` 或其子类时，节点头必须写 `node_paths` 列出属性名，属性行写 `NodePath`：

```ini
[node name="Hud" type="Node" parent="." node_paths=PackedStringArray("player", "targets")]
script = ExtResource("1")
player = NodePath("../Player")
targets = [NodePath("../Player"), NodePath("../Enemy")]
```

| 漏写 | 4.7.2 结果 |
|---|---|
| 单个节点属性不在 `node_paths` | 加载不报错，属性为 `null`，访问时报 `Invalid access to property or key 'name' on a base object of type 'Nil'.` |
| `Array[Node]` 不在 `node_paths` | 数组为空，加载时报 `Unable to convert array index 0 from "NodePath" to "Object".` |
| `node_paths` 少列一个 | 只有这一个为 `null` |

- 路径相对这个节点自己，不相对场景根
- 宿主场景覆盖子场景实例的节点引用，节点头同样要写 `node_paths`
- 实例节点头写法：`[node name="Hud" parent="." node_paths=PackedStringArray("player") instance=ExtResource("1")]`
- `@export var p: NodePath` 和 `@export_node_path` 存的是路径，不进 `node_paths`
- C# 的 `[Export]` 节点属性同样要写 `node_paths`，属性名用 C# 原名
- 拿不准格式时用无头脚本 `pack` 后 `ResourceSaver.save` 存一份照抄

## call_deferred

只在下表场合用，其他场合会让时序难读。

| 场合 | 报错 | 写法 |
|---|---|---|
| 物理回调里增删碰撞体、改 `disabled` | `Can't change this state while flushing queries` | `shape.set_deferred("disabled", true)` |
| 物理回调里改 `monitoring` `monitorable` | `Function blocked during in/out signal` | `set_deferred("monitoring", false)` |
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

- 等本帧树改动全部落定再读结果：`await get_tree().process_frame`
- 带参数延迟调用用 `Callable.call_deferred(args)`，不用字符串方法名
- C# 用 `PropertyName` `MethodName` 常量，不写字符串

## 释放与失效引用

| 做法 | 行为 |
|---|---|
| `queue_free()` | 帧末释放，子树一起释放 |
| `free()` | 立即释放，节点在回调或信号发射中被锁时报错，不对树内节点用 |
| `remove_child(n)` | 只出树不释放，`n` 成孤儿，要自己 `free` 或挂回 |
| `new()` 后没 `add_child` | 孤儿，不用就 `free` |

- `remove_child` 时父在树内且 `owner` 不再是祖先，`owner` 清为 `null`
- `remove_child` 时父在树外，`owner` 保持原值
- 刚 `queue_free` 的节点帧末前 `is_instance_valid` 仍为 `true`，用 `is_queued_for_deletion()` 排除
- 引用的节点释放后访问报 `previously freed`。监听对方 `tree_exiting` 清空，或用前 `is_instance_valid`
- 遍历 `get_children()` 逐个 `queue_free` 安全，`get_children()` 返回副本

| `await` 期间 | 结果 |
|---|---|
| 自己被释放 | 函数不恢复 |
| 被等信号的对象被释放 | 信号不再发，函数一直挂起 |
| 自己只是出树 | 函数恢复，先判断 `is_inside_tree()` 再继续 |

- 查泄漏，仅 debug 构建：退出时看 `ObjectDB instances leaked`，用 `Node.print_orphan_nodes()` 或 `--verbose` 找孤儿

## 禁用时的信号

`PROCESS_MODE_DISABLED` 只停回调和输入，已连接的信号照常调用。

| 写法 | 禁用期间 | 改法 |
|---|---|---|
| `node_added` 里入队，`_process` 里清空 | 队列只增不减 | 在 `node_removed` 里同步出队 |
