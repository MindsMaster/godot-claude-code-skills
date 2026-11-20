# 贴图流送

4.8+ 按画面上的实际需要加载 3D 贴图的 mip 级别，看不见或离得远的只留低分辨率，省显存。

## 开启

```ini
[rendering]

textures/streaming/enabled=true
```

- 贴图在导入面板选 Texture2D Streamed，`.import` 里是 `importer="streamed_texture_2d"`
- 导入结果是 `StreamedTexture2D`，没改导入的贴图不参与
- Compatibility 渲染器不支持，启动时打印警告
- 只有 3D 材质的采样驱动流送

| 用法 | 1080p 下 4096² 贴图实测 |
|---|---|
| 3D 近景铺满屏幕 | 升到第 1 级，2.67 MB |
| `Sprite2D` 1:1 显示 | 一直停在第 3 级，0.17 MB，画面糊 |
| `TextureRect` 1:1 显示 | 同上 |

- 2D 与 UI 贴图用普通导入，不选 Streamed

## LOD 设置

级别 0 是全分辨率，数字越大越糊。4.8 类参考把 `min_lod` 与 `max_lod` 的说明写反了，见 godotengine/godot#125658，按下表。

| 项目设置 `rendering/textures/streaming/` | 默认 | 实际作用 |
|---|---|---|
| `min_lod` | 0 | 最清晰能加载到的级别，调大永久降分辨率 |
| `max_lod` | 3 | 最多降到的级别，刚加载时也在这一级 |
| `inactivity_decay_rate_ms` | 5000 | 看不见后每过这么久降一级，降到 `max_lod` 为止 |
| `max_ops_per_second` | 200 | 每秒最多加载卸载次数 |
| `memory_budget_enabled` | false | 开显存预算 |
| `memory_budget_mb` | 512 | 预算 MB，超出时先降不常用和占屏小的贴图 |

- `max_lod` 设 0 等于不省显存
- 想要更清晰，`min_lod` 保持 0，不要动 `max_lod`
- 降到 `max_lod` 仍超预算，打印 `Texture streaming budget cannot be satisfied even at minimum quality`

16 张 4096² 贴图，Vulkan，1920x1080，`Performance.RENDER_TEXTURE_MEM_USED` 实测，含引擎自带贴图约 37 MB：

| 设置 | 远景 | 近景 |
|---|---|---|
| 不开流送 | 208.3 MB | 208.3 MB |
| 默认 | 40.8 MB | 50.8 MB |
| `max_lod` 0 | 208.3 MB | 208.3 MB |
| `min_lod` 2 | 40.8 MB | 40.8 MB，近景糊 |

## 单张贴图覆盖

导入设置 `streaming/min_lod_override` `streaming/max_lod_override`，对应 `StreamedTexture2D` 的 `min_lod_override` `max_lod_override`。

| 值 | 含义 |
|---|---|
| 0 | 用项目设置 |
| 1 到 14 | 级别 0 到 13，检查器里显示为 0 到 13 |

- 主角脸、准星这类始终要清晰的，`max_lod_override` 设 1，即级别 0

## 运行时

| 需求 | 写法 |
|---|---|
| 画质菜单降贴图分辨率 | `TextureStreaming.min_lod_override = 1` |
| 取消覆盖 | 设 -1，读回 -1 表示没有覆盖 |
| 改预算 | `TextureStreaming.memory_budget_mb_override`，4294967295 表示用项目设置 |
| 流送贴图当前用量 | `TextureStreaming.get_memory_budget_bytes_used()` |
| 全部贴图显存 | `Performance.RENDER_TEXTURE_MEM_USED` |

切场景、传送后，贴图从 `max_lod` 逐级变清晰。加载画面关闭前一次加载到位：

```gdscript
extends CanvasLayer

func reveal() -> void:
	TextureStreaming.flush_texture_streaming()
	await TextureStreaming.flush_completed
	hide()
```

```csharp
public partial class LoadingCover : CanvasLayer
{
    public async void Reveal()
    {
        TextureStreaming.FlushTextureStreaming();
        await ToSignal(TextureStreaming.Singleton, TextureStreaming.SignalName.FlushCompleted);
        Hide();
    }
}
```

- `flush_completed` 用延迟调用发出，调用后再 `await` 不会错过
- 流送没开时也会发出
