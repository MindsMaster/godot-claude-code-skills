# 场景切换

切换 API 的选择与行为、自建切换器、叠加打开。

## 选择

| 需求 | 用这个 |
|---|---|
| 整屏换关卡，旧场景全部丢弃 | `SceneTree.change_scene_to_file(path)` |
| 已有预加载的 `PackedScene` | `SceneTree.change_scene_to_packed(scene)` |
| 切换前建好场景、传参数 | `SceneTree.change_scene_to_node(node)` 4.6+ |
| 重开当前关 | `SceneTree.reload_current_scene()` |
| 菜单、对话框、小游戏叠在当前场景上 | `instantiate()` 后 `add_child`，不切换 |
| 保留旧场景状态再回来 | 旧场景 `remove_child` 不释放，或叠加 |
| 转场动画、加载进度 | 自建切换器 |

- `change_scene_to_file` 同步 `load`，大场景卡一帧以上

## 行为

| 时刻 | 状态 |
|---|---|
| 调用后 | 旧场景出树，`current_scene` 为 `null` |
| 调用后的同一帧 | 拿不到新场景 |
| 帧末 | 旧场景释放，新场景进树 |
| `scene_changed` 发出 4.5+ | 新场景可用 |

- 等 `scene_changed` 要在 autoload 里，旧场景的函数随节点释放不恢复
- 旧场景脚本里调用之后的代码照常运行，但 `get_tree()` 为 `null`
- 切换调用放在函数最后，或先存 `var tree := get_tree()`
- autoload 不受影响，留在 `/root` 下
- `change_scene_to_node` 的 `node` 不能已在树里
- `change_scene_to_node` 后 `SceneTree` 接管该节点，下次切换释放它，不保留引用

## 传参数

4.6+ 用 `change_scene_to_node`，切换前设好：

```gdscript
extends Node

@export var next_scene: PackedScene

func go(level_index: int) -> void:
	var level := next_scene.instantiate()
	level.set("index", level_index)
	get_tree().change_scene_to_node(level)
```

```csharp
public partial class Level : Node
{
    public int Index { get; set; }
}

public partial class LevelGate : Node
{
    [Export] public PackedScene NextScene { get; set; }

    public void Go(int levelIndex)
    {
        var level = NextScene.Instantiate<Level>();
        level.Index = levelIndex;
        GetTree().ChangeSceneToNode(level);
    }
}
```

- 4.5 及以下参数放 autoload 字段，新场景 `_ready` 里读

## 自建切换器

放在 autoload 里，自带一个 `CanvasLayer` 和遮罩。4.4 没有 `scene_changed`，改成等 `process_frame`：

```gdscript
extends CanvasLayer

signal finished

@onready var fade: ColorRect = $Fade

func change_to(path: String) -> void:
	var tween := create_tween()
	tween.tween_property(fade, "modulate:a", 1.0, 0.3)
	await tween.finished
	ResourceLoader.load_threaded_request(path)
	var status := ResourceLoader.load_threaded_get_status(path)
	while status == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
		await get_tree().process_frame
		status = ResourceLoader.load_threaded_get_status(path)
	if status == ResourceLoader.THREAD_LOAD_LOADED:
		get_tree().change_scene_to_packed(ResourceLoader.load_threaded_get(path) as PackedScene)
		await get_tree().scene_changed
	else:
		push_error("场景加载失败 %s" % path)
	tween = create_tween()
	tween.tween_property(fade, "modulate:a", 0.0, 0.3)
	await tween.finished
	finished.emit()
```

```csharp
public partial class SceneSwitcher : CanvasLayer
{
    [Signal] public delegate void FinishedEventHandler();

    private ColorRect _fade;

    public override void _Ready()
    {
        _fade = GetNode<ColorRect>("Fade");
    }

    public async Task ChangeTo(string path)
    {
        var tween = CreateTween();
        tween.TweenProperty(_fade, "modulate:a", 1.0, 0.3);
        await ToSignal(tween, Tween.SignalName.Finished);
        ResourceLoader.LoadThreadedRequest(path);
        var status = ResourceLoader.LoadThreadedGetStatus(path);
        while (status == ResourceLoader.ThreadLoadStatus.InProgress)
        {
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            status = ResourceLoader.LoadThreadedGetStatus(path);
        }
        if (status == ResourceLoader.ThreadLoadStatus.Loaded)
        {
            GetTree().ChangeSceneToPacked((PackedScene)ResourceLoader.LoadThreadedGet(path));
            await ToSignal(GetTree(), SceneTree.SignalName.SceneChanged);
        }
        else
        {
            GD.PushError($"场景加载失败 {path}");
        }
        tween = CreateTween();
        tween.TweenProperty(_fade, "modulate:a", 0.0, 0.3);
        await ToSignal(tween, Tween.SignalName.Finished);
        EmitSignal(SignalName.Finished);
    }
}
```

- 遮罩的 `layer` 大于 HUD
- 切换器设 `PROCESS_MODE_ALWAYS`，暂停时也能转场
- 切换前恢复 `get_tree().paused`，暂停状态会带到新场景
- 不手动 `free` 旧场景再赋 `current_scene`，`change_scene_to_*` 已处理
- 加载进度条见 godot-resources-data 的带进度的异步加载
- C# 的 `await ToSignal` 对应 GDScript 的 `await 信号`

## 叠加打开

能回到原界面的商店、设置页、小游戏，叠加不切换：

```gdscript
extends Node

@export var shop_scene: PackedScene

func open_shop() -> void:
	var shop := shop_scene.instantiate()
	add_child(shop)
	get_tree().paused = true
	shop.tree_exited.connect(_on_shop_closed)

func _on_shop_closed() -> void:
	get_tree().paused = false
```

```csharp
public partial class ShopOpener : Node
{
    [Export] public PackedScene ShopScene { get; set; }

    public void OpenShop()
    {
        var shop = ShopScene.Instantiate();
        AddChild(shop);
        GetTree().Paused = true;
        shop.TreeExited += OnShopClosed;
    }

    private void OnShopClosed()
    {
        GetTree().Paused = false;
    }
}
```

- 商店根节点设 `PROCESS_MODE_WHEN_PAUSED` 或 `PROCESS_MODE_ALWAYS`
- 关闭时商店自己 `queue_free`
