# RichTextLabel 细节

## 开关

- `bbcode_enabled = true` 才解析 BBCode。设 `text` 属性会重新解析，运行时拼接用 `append_text()`，清空用 `clear()`
- 玩家输入或外部字符串进 BBCode 前，把 `[` 换成 `[lb]`，否则输入 `[url]` 能注入标签
- 控件是只读展示用途时，`context_menu_enabled` 默认 false，`selection_enabled` 默认 false，需要复制才开
- `threaded = true` 在后台排版长文本，日志窗口与大段文本用

## 标签速查

| 目的 | 写法 |
|---|---|
| 粗体 斜体 | `[b]x[/b]` `[i]x[/i]`，需要主题里配粗体斜体字体 |
| 颜色 | `[color=red]x[/color]` `[color=#ff8800]x[/color]` |
| 字号 | `[font_size=32]x[/font_size]` |
| 描边 | `[outline_size=4][outline_color=black]x[/outline_color][/outline_size]` |
| 对齐 | `[center]x[/center]` `[right]x[/right]` `[fill]x[/fill]` |
| 链接 | `[url=quest:12]x[/url]`，接 `meta_clicked` |
| 悬停提示 | `[hint="说明"]x[/hint]` |
| 图片 | `[img=32x32]res://ui/icons/coin.png[/img]` |
| 表格 | `[table=2][cell]a[/cell][cell]b[/cell][/table]` |
| 列表 | `[ul]` `[ol type=1]` |
| 转义 | `[lb]` `[rb]` |
| 内置动效 | `[wave amp=50 freq=5]` `[shake rate=20 level=5]` `[tornado]` `[pulse]` `[fade start=4 length=14]` `[rainbow]` |

- `[code]` 标签只有在主题里配了等宽字体才生效
- `[img]` 写 `res://` 路径。图标来自运行时加载的 Texture2D 时，用 `add_image()` 在代码里插入

## 链接点击

`[url]` 默认点击无反应，要连接 `meta_clicked`。参数永远是 String，需要结构化数据就编码成 JSON 或键值字符串再解析：

```gdscript
extends RichTextLabel

func _ready() -> void:
	bbcode_enabled = true
	text = "[url=quest:12]接受任务[/url]"
	meta_clicked.connect(_on_meta_clicked)

func _on_meta_clicked(meta: Variant) -> void:
	var s := str(meta)
	if s.begins_with("quest:"):
		print("quest id ", s.trim_prefix("quest:").to_int())
	else:
		OS.shell_open(s)
```

## 打字机

```gdscript
extends RichTextLabel

var _tween: Tween

func say(line: String, chars_per_second: float = 40.0) -> void:
	text = line
	visible_ratio = 0.0
	if _tween:
		_tween.kill()
	_tween = create_tween()
	var duration := get_total_character_count() / chars_per_second
	_tween.tween_property(self, "visible_ratio", 1.0, duration)
```

- `get_total_character_count()` 不计 BBCode 标签，按它算时长，`bbcode_enabled` 要在设 `text` 之前开
- 点击跳过：`_tween.kill()` 后 `visible_ratio = 1.0`
- 打字机每个字弹一声音效，用 `visible_characters` 变化驱动，节流到每 2 到 3 个字一次，不要每字播放

## 自定义 RichTextEffect

继承 RichTextEffect，`bbcode` 成员定义标签名，`_process_custom_fx` 对每个字形调用一次。返回 true 表示处理成功，返回 false 会放弃整段自定义效果。

```gdscript
@tool
class_name RichTextGhost
extends RichTextEffect

var bbcode: String = "ghost"

func _process_custom_fx(char_fx: CharFXTransform) -> bool:
	var speed: float = char_fx.env.get("freq", 5.0)
	var span: float = char_fx.env.get("span", 10.0)
	var phase := char_fx.elapsed_time * speed + char_fx.range.x / span
	char_fx.color.a = sin(phase) * 0.5 + 0.5
	return true
```

用法 `[ghost freq=5 span=10]text[/ghost]`。

- 必须注册，否则标签原样显示：Inspector 的 Markup 分类 Custom Effects 数组里添加，或代码 `install_effect(RichTextGhost.new())`
- `@tool` 让效果在编辑器里也运行
- `CharFXTransform` 常用成员：`elapsed_time` 效果已运行秒数，`range` 字形在标签内的区间，`relative_index` 相对序号，`offset` 位移，`color` 颜色，`visible` 显示，`transform` 变换，`env` 标签参数字典
- 带自定义效果的 RichTextLabel 持续每帧处理，除非暂停。不在屏幕上时设 `visible = false`，电池敏感的平台尤其要注意
- `outline` 为 true 时是在绘制描边，效果要同时作用到描边

## 与翻译配合

BBCode 文本进翻译表时，标签一起放进译文，译者可以移动标签位置。带变量用 `.format()` 在 `tr()` 之后替换，标签内部的参数不要拆给译者。
