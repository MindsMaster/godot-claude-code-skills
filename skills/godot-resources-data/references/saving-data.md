# 存档与用户数据

## 位置

`user://` 是游戏唯一可写、导出后仍存在的位置。默认路径带项目名，项目改名后旧存档就找不到了。发布前固定它：

```ini
[application]

config/use_custom_user_dir=true
config/custom_user_dir_name="MyGame"
```

- 默认位置：Windows `%APPDATA%\Godot\app_userdata\<项目名>`，macOS `~/Library/Application Support/Godot/app_userdata/<项目名>`，Linux `~/.local/share/godot/app_userdata/<项目名>`
- 勾选 `application/config/use_custom_user_dir` 后用 `application/config/custom_user_dir_name` 的名字，不再带 `Godot/app_userdata`
- Web 导出的 `user://` 是浏览器里的虚拟文件系统，清浏览器数据会丢
- 向玩家显示路径用 `OS.get_user_data_dir()`，代码里一律写 `user://`

## 格式选择

| 格式 | 读写 | 适合 | 不适合 |
|---|---|---|---|
| JSON | `JSON.stringify` `JSON.parse_string` | 存档 跨版本迁移 排错时可读 | 大二进制 |
| `ConfigFile` | `set_value` `get_value` `save` `load` | 设置 键盘映射 | 嵌套数据 不可信来源 |
| `FileAccess.store_var` | `store_var` `get_var` | 紧凑二进制 内部缓存 | 需要人读 需要跨版本迁移 |
| `ResourceSaver` | `save` `load` | 编辑器烘焙 开发期数据 | 玩家存档 |

安全相关的三条，实测过：

- `.tres` 里可以内嵌 `GDScript` 子资源，`load` 它就会执行 `_init`。玩家能写的位置不要 `load` 资源文件
- `ConfigFile.parse` 和 `str_to_var` 会按文本创建 `Object(...)`。不可信文本用 JSON
- `FileAccess.get_var(true)` 会解码对象并可能执行脚本，`allow_objects` 保持默认 `false`，`store_var` 的 `full_objects` 同理

## JSON 存档

```gdscript
class_name SaveStore
extends RefCounted

const VERSION: int = 2
const PATH: String = "user://save.json"

static func write(state: Dictionary) -> Error:
	var payload := {"version": VERSION, "state": state}
	var tmp := PATH + ".tmp"
	var file := FileAccess.open(tmp, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(JSON.stringify(JSON.from_native(payload), "\t"))
	file.close()
	return DirAccess.rename_absolute(tmp, PATH)

static func read() -> Dictionary:
	if not FileAccess.file_exists(PATH):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if not parsed is Dictionary:
		return {}
	var payload: Dictionary = JSON.to_native(parsed)
	return _migrate(payload)

static func _migrate(payload: Dictionary) -> Dictionary:
	var version: int = payload.get("version", 1)
	var state: Dictionary = payload.get("state", {})
	if version < 2:
		state["gold"] = state.get("coins", 0)
		state.erase("coins")
	return state
```

- 先写 `.tmp` 再改名，写到一半断电或崩溃不会毁掉旧存档
- `JSON.parse_string` 读回的数字都是 `float`，`3` 变成 `3.0`。用 `JSON.from_native` 写、`JSON.to_native` 读（4.4+）可以保留 `int`、`Vector2`、`Color` 等类型，代价是 `Dictionary` 变成 `{"type":"Dictionary","args":[...]}`，键和 `int` 带 `s:` `i:` 前缀，手改不方便
- 存档带 `version`，读到旧版本在 `_migrate` 里逐级升。不要靠字段是否存在猜版本
- 读取是系统边界：解析失败、字段缺失、类型不对都要处理，回到默认值或提示玩家，不要让游戏崩
- 运行时对象不直接序列化。给对象写 `to_dict()` 和 `from_dict()`，存档只含标识（物品 id、关卡名），读回来再去数据表查 `Resource`

对象存取的最短形态：

```gdscript
class_name PlayerState
extends RefCounted

var gold: int = 0
var item_ids: Array[StringName] = []

func to_dict() -> Dictionary:
	return {"gold": gold, "items": item_ids}

static func from_dict(data: Dictionary) -> PlayerState:
	var state := PlayerState.new()
	state.gold = int(data.get("gold", 0))
	for id: String in data.get("items", []):
		state.item_ids.append(StringName(id))
	return state
```

## ConfigFile 设置

```gdscript
extends Node

const PATH: String = "user://settings.cfg"

func save_volume(value: float) -> void:
	var cfg := ConfigFile.new()
	cfg.load(PATH)
	cfg.set_value("audio", "master", value)
	cfg.save(PATH)

func load_volume() -> float:
	var cfg := ConfigFile.new()
	if cfg.load(PATH) != OK:
		return 1.0
	return cfg.get_value("audio", "master", 1.0)
```

保存前先 `load`，保留其他段落里别的代码写的键。

## 加密

`FileAccess.open_encrypted_with_pass(path, FileAccess.WRITE, password)` 和 `ConfigFile.save_encrypted_pass` 可以防玩家随手改存档。密码在游戏二进制里，防不住有意破解，也不能当安全措施。联网校验另做。

## C#

C# 的存档数据用普通类加 `System.Text.Json`，比 `Variant` 字典好维护：

```csharp
using System.Text.Json;

public sealed class SaveData
{
    public int Version { get; set; } = 2;

    public int Gold { get; set; }

    public List<string> ItemIds { get; set; } = new();
}

public static class SaveStore
{
    private const string SavePath = "user://save.json";

    public static void Write(SaveData data)
    {
        using var file = FileAccess.Open(SavePath, FileAccess.ModeFlags.Write);
        file.StoreString(JsonSerializer.Serialize(data));
    }

    public static SaveData Read()
    {
        if (!FileAccess.FileExists(SavePath))
        {
            return new SaveData();
        }

        string text = FileAccess.GetFileAsString(SavePath);
        try
        {
            return JsonSerializer.Deserialize<SaveData>(text) ?? new SaveData();
        }
        catch (JsonException)
        {
            return new SaveData();
        }
    }
}
```

`FileAccess.Open` 失败返回 `null`，生产代码里先判断 `null` 再写入，用 `FileAccess.GetOpenError()` 取原因。
