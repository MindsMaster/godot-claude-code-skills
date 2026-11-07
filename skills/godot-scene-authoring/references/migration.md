# 迁移

把运行时按代码或配表建的内容迁进场景：盘点、顺序、坐标换算、运行时取节点、验证、常见问题。前提是按 [audit.md](audit.md) 自查过且用户同意。

## 盘点

列出运行时建节点的每一处，逐项归类：

| 现在 | 迁成 |
|---|---|
| 固定位置的背景层、灯、道具、门 | 场景里的节点，配表删字段 |
| 固定站位的 NPC，配表写贴图或动画 ID | 标记点下挂显示节点，配表只留对话 条件 商店 |
| 代码 `new ColorRect` 拼出的机关 | 预制 `.tscn`，代码 `instantiate()` 后取子节点改状态 |
| 敌人 投射物 掉落 | 预制 `.tscn`，生成逻辑不变 |
| HUD 菜单在代码里设 `position` `size` | 场景里用 Container 摆，代码只填数据和连信号 |
| 数量和位置由种子决定的生成内容 | 不迁，`@tool` 里调同一段生成代码 |

- 按条件出现的内容也摆进场景，代码按条件设 `visible`

## 顺序

每步单独提交，每步跑回归：

1. 显示节点：加 `@tool`，配表外观字段变成导出属性，setter 里重画。运行时代码改成给属性赋值
2. 派生属性：加 `_validate_property` 去掉存盘位，生成的辅助节点改成 internal
3. 写场景：按配表逐项建节点，坐标按运行时公式换算一次
4. 换运行时：实例化场景，按名字或标记取节点，删掉建节点的代码
5. 删数据：配表和加载器删外观字段，剩下的字段严格校验
6. 验证：见下文

- 第 1 步到第 4 步之间游戏画面不变，迁移前截图对比

## 坐标换算

配表坐标常是图上像素、按米的位置、相对地面线的偏移。换算一次写进场景，之后只在场景里改。

- 运行时公式抄成一次性换算脚本，跑完删掉
- 图层原点放在地面线中点，道具放在底边中点，灯放在发光点
- 挂在图上的灯做成图层的子节点，跟着图层滚动
- 镜头每帧改写的属性，如视差层的 `position`，写明不让美术拖

## 运行时取节点

```gdscript
extends Node2D

@export var room_scene: PackedScene

func enter_room() -> void:
	var room := room_scene.instantiate() as Node2D
	add_child(room)
	for marker: Node in room.get_children():
		if marker is Marker2D and marker.has_node("Npc"):
			var npc := marker.get_node("Npc") as CanvasItem
			npc.visible = marker.name != "Locked"
```

```csharp
public partial class RoomLoader : Node2D
{
    [Export] public PackedScene RoomScene { get; set; }

    public void EnterRoom()
    {
        var room = RoomScene.Instantiate<Node2D>();
        AddChild(room);
        foreach (Node marker in room.GetChildren())
        {
            if (marker is Marker2D && marker.HasNode("Npc"))
            {
                var npc = marker.GetNode<CanvasItem>("Npc");
                npc.Visible = marker.Name != "Locked";
            }
        }
    }
}
```

- 按名字或标记种类取节点，不按子节点下标
- 统一换材质时代码只设根的 `material`，子节点勾 `use_parent_material`
- 实例化后只改运行时状态，如门开关，存盘的是初始样子

## 验证

- 导出给模拟的数据和迁移前逐字节一致
- 冒烟测试通过，迁移前后截图一致
- 无头编辑器打开并存盘每个改过的场景，`git diff` 只有 `uid` `unique_id` 补全
- 场景面板里每个节点都能点中，拖动存盘后游戏里位置跟着变

无头编辑器验证用临时插件：打开场景、打印树、存盘、退出。C# 项目同样用这个 GDScript 插件：

<!-- check: gdonly -->
```gdscript
@tool
extends EditorPlugin

const SCENES: PackedStringArray = ["res://rooms/room_a.tscn"]
const OUT: String = "res://probe_out.txt"

func _enter_tree() -> void:
	probe.call_deferred()

func probe() -> void:
	var lines := PackedStringArray()
	for path: String in SCENES:
		EditorInterface.open_scene_from_path(path)
		var root := EditorInterface.get_edited_scene_root()
		dump(root, 0, lines)
		EditorInterface.save_scene()
	var file := FileAccess.open(OUT, FileAccess.WRITE)
	file.store_string("\n".join(lines))
	file.close()
	get_tree().quit()

func dump(node: Node, depth: int, lines: PackedStringArray) -> void:
	var owner_name := "-" if node.owner == null else String(node.owner.name)
	lines.append("%s%s %s owner=%s" % ["  ".repeat(depth), node.name, node.get_class(), owner_name])
	for child: Node in node.get_children(true):
		dump(child, depth + 1, lines)
```

```
godot --headless --editor --path . --quit-after 600
```

- 插件放进 `addons/<名字>/`，写进 `project.godot` 的 `editor_plugins/enabled`
- 跑完还原 `project.godot`，删插件目录
- 结果写文件，Windows 下无头编辑器的标准输出容易丢
- 首次运行导入全部资源，`--quit-after` 给够
- 缩略图报 `Parameter "t" is null` 之类是假渲染器所致，不影响结果
- 打开场景可能改写别的资源文件，跑完 `git status` 还原无关改动

| 输出里看 | 期望 |
|---|---|
| 内容节点的 owner | 场景根 |
| 生成的辅助节点 | owner 为 `-`，只出现在 `get_children(true)` 里 |

## 常见问题

| 现象 | 原因 |
|---|---|
| 编辑器里节点空白，运行时正常 | 没加 `@tool`；C# 加了 `[Tool]` 没 Build；材质按游戏视口写死 |
| 存盘后 tscn 多了 `material` `z_index` | `_ready` 里赋的派生属性，加 `_validate_property` |
| 存盘后多出一串子节点 | 生成节点设了 owner，或被实例化子场景的根认领 |
| Ctrl+D 复制后子节点翻倍 | 生成节点没用 internal |
| 改完脚本节点变空 | C# 重载丢了非 Variant 状态，`ISerializationListener` 里重建 |
| 切换场景标签页回来节点变空 | `_exit_tree` 里释放、`_enter_tree` 里没补 |
| 打开场景后编辑器 CPU 一直高 | `@tool` 节点 `_process` 里每帧 `queue_redraw()` |
| 存盘时报 `add_child` 被阻止 | `NOTIFICATION_EDITOR_PRE_SAVE` 里增删节点，改成只写文件或改属性 |
