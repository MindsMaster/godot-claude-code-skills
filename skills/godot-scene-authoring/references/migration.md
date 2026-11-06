# 把代码搭的内容迁进场景

按 [audit.md](audit.md) 自查后确认场景只有空壳、内容在运行时按配表或代码建，并且用户同意迁移时读这一篇。

## 先盘点

列出运行时建节点的每一处，每一项归到下面一类：

| 现在 | 迁成 |
|---|---|
| 固定位置的背景层、灯、道具、门 | 场景里的节点，配表删字段 |
| 固定站位的 NPC，配表写贴图或动画 ID | 标记点下挂显示节点，配表只留对话 条件 商店 |
| 代码里 `new ColorRect` 拼出来的机关 | 预制 `.tscn`，代码 `instantiate()` 后取子节点改状态 |
| 敌人 投射物 掉落 | 预制 `.tscn`，生成逻辑不变 |
| HUD 菜单在代码里设 `position` `size` | 场景里用 Container 摆，代码只填数据和连信号 |
| 数量和位置由种子决定的生成内容 | 不迁，`@tool` 里调同一段生成代码给编辑器看 |

一个房间里有一半内容按条件出现时，全部摆进场景，代码按条件设 `visible`，别把有条件的那部分留在代码里建。

## 顺序

每步单独提交，每步跑完回归：

1. 显示节点：加 `@tool`，配表里的外观字段变成导出属性，setter 里重画。运行时代码这时还照旧按配表建，只是改成给属性赋值
2. 派生属性：`_ready` 里按视口、按深度算出来的属性加 `_validate_property` 去掉存盘位，生成的辅助节点改成 internal
3. 写场景：按配表一项一项建节点，坐标按运行时的公式换算一次，见下一节
4. 换运行时：实例化场景，从里面按名字或标记取节点，删掉建节点的代码
5. 删数据：配表和加载器删掉外观字段，加载器对剩下的字段严格校验
6. 验证：见最后一节

第 1 步和第 4 步之间，游戏画面应该完全不变。截一张迁移前的图对比。

## 坐标换算

配表里的坐标往往不是场景坐标：图上的像素、按米算的位置、相对地面线的偏移。换算一次写进场景，之后只在场景里改：

- 运行时公式原样抄成一段一次性的换算脚本，跑完删掉，别留进仓库
- 节点的原点放在美术好理解的位置：图层的原点放在地面线中点，道具放在底边中点，灯放在发光点
- 灯这类挂在图上的东西做成图层的子节点，跟着图层滚动，拖图层时灯一起走
- 镜头每帧改写的属性，比如视差层的 `position`，别让美术拖。文档里写明拖哪一层

## 运行时从场景取节点

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

- 取节点按场景里的名字或标记的种类，不按子节点下标。美术会调整顺序
- 预制场景要统一换材质时，代码只设根的 `material`，子节点在场景里勾 `use_parent_material`
- 实例化后再改的东西：运行时状态，比如门开关、楼层数字。存盘的是初始样子

## 验证

- 导出给模拟的数据和迁移前逐字节一致
- 冒烟测试过，迁移前后截图一致
- 无头编辑器打开每个改过的场景再存盘，`git diff` 里只有 `uid` 和 `unique_id` 这类补全，没有多出的节点和 `material`
- 场景面板里每个节点都能点中，拖动后存盘再进游戏位置跟着变

无头编辑器验证用一个临时插件，打开场景、打印树、存盘、退出：

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

- 插件放进 `addons/<名字>/`，写进 `project.godot` 的 `editor_plugins/enabled`，跑完把 `project.godot` 还原、插件目录删掉
- 结果写文件，Windows 下无头编辑器的标准输出容易丢
- 第一次跑会导入全部资源，耗时长，`--quit-after` 给够
- 无头编辑器生成缩略图时报 `Parameter "t" is null` 之类的错，是假渲染器，不影响结果
- 打开场景本身就可能让编辑器改写别的资源文件，跑完 `git status` 看一遍，和本次无关的还原

输出里要看：每个内容节点的 owner 是场景根，生成的辅助节点 owner 是 `-` 并且只出现在 `get_children(true)` 里。

## 常见问题

| 现象 | 原因 |
|---|---|
| 编辑器里节点空白，运行时正常 | 脚本没加 `@tool`；C# 加了 `[Tool]` 没 Build；材质按游戏视口写死，编辑器视口用不了 |
| 存盘后 tscn 里多了 `material` `z_index` | `_ready` 里赋的派生属性，加 `_validate_property` |
| 存盘后多出一串子节点 | 生成节点设了 owner，或挂在实例化子场景下被那个子场景的根认领 |
| Ctrl+D 复制后子节点翻倍 | 生成节点没用 internal |
| 改完脚本节点变空 | C# 重载丢了非 Variant 状态，`ISerializationListener` 里重建 |
| 切换场景标签页回来节点变空 | `_exit_tree` 里释放、`_enter_tree` 里没补 |
| 打开场景后编辑器 CPU 一直高 | `@tool` 节点在 `_process` 里每帧 `queue_redraw()` |
| 存盘时报 `add_child` 被阻止 | `NOTIFICATION_EDITOR_PRE_SAVE` 里加删了节点，改成只写文件或改属性 |
