# RichTextLabel

BBCode 开关与安全、标签速查、链接点击、打字机、自定义 RichTextEffect、与翻译配合。

## 开关

| 属性或方法 | 用法 |
|---|---|
| `bbcode_enabled` | true 才解析 BBCode |
| `text` | 赋值会重新解析整段 |
| `append_text()` | 运行时追加 |
| `clear()` | 清空 |
| `context_menu_enabled` `selection_enabled` | 默认 false，要复制才开 |
| `threaded` | true 时后台排版，日志窗口与长文本用 |

- 玩家输入或外部字符串进 BBCode 前，把 `[` 换成 `[lb]`
- 不转义时输入 `[url]` 能注入标签

## 标签速查

| 目的 | 写法 |
|---|---|
| 粗体 斜体 | `[b]x[/b]` `[i]x[/i]` |
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

- `[b]` `[i]` 默认由基础字体合成
- 真字形在主题 RichTextLabel 类型下配 `bold_font` `italics_font` `bold_italics_font`
- `[code]` 只有主题里配了等宽字体才生效
- `[img]` 写 `res://` 路径
- 运行时加载的 Texture2D 用 `add_image()` 插入

## 链接点击

`[url]` 默认点击无反应，要连 `meta_clicked`。

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

```csharp
public partial class QuestText : RichTextLabel
{
    public override void _Ready()
    {
        BbcodeEnabled = true;
        Text = "[url=quest:12]接受任务[/url]";
        MetaClicked += OnMetaClicked;
    }

    private void OnMetaClicked(Variant meta)
    {
        string s = meta.AsString();
        if (s.StartsWith("quest:"))
        {
            GD.Print("quest id ", s.TrimPrefix("quest:").ToInt());
        }
        else
        {
            OS.ShellOpen(s);
        }
    }
}
```

- BBCode 里写的参数永远是 String
- 结构化数据编码成 JSON 或键值字符串再解析
- 传非 String 用 `push_meta()`

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

```csharp
public partial class Typewriter : RichTextLabel
{
    private Tween _tween;

    public void Say(string line, float charsPerSecond = 40.0f)
    {
        Text = line;
        VisibleRatio = 0.0f;
        _tween?.Kill();
        _tween = CreateTween();
        float duration = GetTotalCharacterCount() / charsPerSecond;
        _tween.TweenProperty(this, "visible_ratio", 1.0f, duration);
    }
}
```

- 时长按 `get_total_character_count()` 算，它不计 BBCode 标签
- 不用 `line.length()` 算时长
- 点击跳过：`_tween.kill()` 后 `visible_ratio = 1.0`
- 逐字音效用 `visible_characters` 变化驱动
- 音效节流到每 2 到 3 个字一次

## 自定义 RichTextEffect

继承 RichTextEffect，`bbcode` 成员定义标签名，`_process_custom_fx` 对每个字形调用一次。

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

```csharp
[Tool]
[GlobalClass]
public partial class RichTextGhost : RichTextEffect
{
    string bbcode = "ghost";

    public override bool _ProcessCustomFX(CharFXTransform charFX)
    {
        float speed = charFX.Env.TryGetValue("freq", out Variant f) ? f.AsSingle() : 5.0f;
        float span = charFX.Env.TryGetValue("span", out Variant sp) ? sp.AsSingle() : 10.0f;
        float phase = (float)charFX.ElapsedTime * speed + charFX.Range.X / span;
        Color color = charFX.Color;
        color.A = Mathf.Sin(phase) * 0.5f + 0.5f;
        charFX.Color = color;
        return true;
    }
}
```

- 用法 `[ghost freq=5 span=10]text[/ghost]`
- 返回 false 放弃整段自定义效果
- 必须注册，否则标签原样显示
- 注册：Inspector Markup 分类的 Custom Effects 数组，或 `install_effect(RichTextGhost.new())`
- `@tool` 让效果在编辑器里也运行
- C# 的 `bbcode` 字段名照写小写，引擎按这个名字读
- `env` 的参数自动转成 bool、int、float、Color，其余是字符串
- 带自定义效果的 RichTextLabel 每帧处理，项目暂停除外
- 不在屏幕上时设 `visible = false`，省电

| `CharFXTransform` 成员 | 含义 |
|---|---|
| `elapsed_time` | 效果已运行秒数 |
| `range` | 字形在标签内的区间 |
| `relative_index` | 相对序号 |
| `offset` | 位移 |
| `color` | 颜色 |
| `visible` | 显示 |
| `transform` | 变换 |
| `env` | 标签参数字典 |
| `outline` | true 时在绘制描边，效果要同时作用到描边 |

## 与翻译配合

- BBCode 标签随译文一起进翻译表，译者可移动标签位置
- 变量在 `tr()` 之后用 `format()` 替换
- 标签内部的参数不拆给译者
