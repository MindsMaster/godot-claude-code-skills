# 导入与循环

音频素材选格式、导入设置与循环点。改完 `.import` 后重新导入。

## 导入格式

| 素材 | 格式 | 导入设置 |
|---|---|---|
| 短音效 | WAV | `compress/mode` 默认 Quite OK Audio，约 PCM 的 1/5 |
| 音乐 长环境声 | Ogg Vorbis 或 MP3 | 动态音乐的 `bpm` `beat_count` 只有这两种有 |
| 3D 定位音源 | 单声道 WAV | 打开 `force/mono` |

- 游戏里比原文件闷，先查播放器和总线，转 Ogg 只多一层有损压缩
- 96 kHz 素材开 `force/max_rate`，`force/max_rate_hz` 设 48000
- 立体声素材在 3D 播放器里保留声像宽度，定位不如单声道准

## 循环

改 `.import` 的 `[params]`，改完重新导入：

```ini
edit/loop_mode=2
edit/loop_begin=0
edit/loop_end=-1
```

| 格式 | 选项 | 取值 |
|---|---|---|
| WAV | `edit/loop_mode` | 0 读 WAV 元数据，1 关闭，2 正向，3 往返，4 反向 |
| WAV | `edit/loop_begin` `edit/loop_end` | 采样数，`loop_end` -1 取末尾 |
| Ogg Vorbis MP3 | `loop` `loop_offset` | `loop=true`，偏移以秒计 |

- 运行时改共享 stream 的 `loop_mode` 影响所有引用者
- 循环音频的播放器不发 `finished`
