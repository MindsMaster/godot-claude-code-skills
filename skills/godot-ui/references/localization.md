# 本地化

翻译表格式、导入与注册、脚本里的翻译调用、语言选择、测试、字体回退、数字与书写方向。

## 格式

| 格式 | 适合 | 注意 |
|---|---|---|
| CSV | 小团队，表格里直接改，键用 `MENU_START` 这类大写键 | 一个文件含所有语言，复数与上下文列 4.6+ |
| PO、MO | 有专业译者与翻译平台，英文原文当键 | 要 POT 提取与 gettext 工具链 |

- 两种可在同一项目混用，注册后合并查找

## CSV

第一行是表头，第一列是键，其余列是语言代码。

```
keys,en,zh_CN,ja
MENU_START,Start,开始,スタート
MENU_QUIT,Quit,退出,終了
```

- 语言列头用 locale 代码，如 `zh_CN` `en_GB`
- 列头以 `_` 开头的列当注释，不导入
- 左上角单元格忽略
- 键区分大小写
- 含逗号与换行的单元格用双引号包住，表格软件导出时自动处理
- 导入后同目录生成压缩的翻译资源，每种语言一个
- Import 面板改压缩选项，改完 Reimport
- 导入不等于生效，必须注册

### 复数列

4.6+ 可加 `?plural` 列，不能放第一列。第二行起行头是单数形式，译文按语言需要的形式往下写：

```
en,?plural,fr,ru
?pluralrule,,nplurals=2; plural=(n >= 2);,
There is %d apple,There are %d apples,Il y a %d pomme,Есть %d яблоко
,,Il y a %d pommes,Есть %d яблока
,,,Есть %d яблок
```

- `?pluralrule` 行给每种语言写 gettext 复数规则
- 带复数列的表，控件不自动翻译，只能用 `tr_n()`
- 单数行头同时是查找键
- `tr_n()` 前两个参数写单数行头和 `?plural` 列的文本，缺翻译时回退到它们
- 单数行头用 `ITEM_ONE` 这类键名时，回退文本不含 `%d`
- 此时 `%` 报 `String formatting error`

### 上下文列

4.6+ 可加 `?context` 列，不能放第一列，用英文原文当键时区分同形异义。

```
en,?context,fr
Letter,Alphabet,Lettre
Letter,Message,Courrier
```

- 带上下文的行要手动调 `tr()` 或 `tr_n()`

## PO

| 步骤 | 做法 |
|---|---|
| 列出提取源 | `internationalization/locale/translations_pot_files` 填场景与脚本 |
| 生成 POT | 项目设置 Localization 页点 Generate，指定 `.pot` 路径 |
| 各语言 `.po` | `msginit` 从 POT 生成 |
| 同步新字符串 | `msgmerge` |
| 编译 `.mo` | `msgfmt`，引擎也能直接读 `.po` |

| 提取对象 | 内容 |
|---|---|
| 场景属性 | `text` `*_text` `title` `tooltip_text` `accessibility_name` 等 |
| 脚本调用 | `tr()` `tr_n()` `atr()` |
| 脚本赋值 | 对 `text` `placeholder_text` `tooltip_text` 的赋值 |

- `auto_translate_mode` 设成 disabled 的节点不提取
- 不提取的字符串在同一行或上一行写 `NO_TRANSLATE` 注释
- 给译者的说明写 `TRANSLATORS:` 注释
- `msgmerge` 后源文变动的条目带 `fuzzy` 标记，去掉前引擎不读

## 注册与资源重映射

- 注册：`internationalization/locale/translations`，Localization 页 Translations 标签
- CSV 导入出的每个翻译资源、每个 `.po` 都要注册
- `internationalization/locale/translation_remaps` 按语言替换整个资源，如带字贴图、配音
- 重映射不支持字体，字体用回退链
- 模组与 DLC 语言包：运行时 `TranslationServer.add_translation(translation)`
- 移除用 `TranslationServer.remove_translation`

## 脚本里的翻译

```gdscript
extends Node

func _ready() -> void:
	print(tr("MENU_START"))
	print(tr("PICKED_UP").format({item = tr("ITEM_SWORD")}))
	print(tr("Close", "Distance"))
	print(tr_n("There is %d apple", "There are %d apples", 3) % 3)
	print(atr("MENU_QUIT"))
```

```csharp
public partial class TranslateDemo : Node
{
    public override void _Ready()
    {
        GD.Print(Tr("MENU_START"));
        GD.Print(Tr("PICKED_UP").Replace("{item}", Tr("ITEM_SWORD")));
        GD.Print(Tr("Close", "Distance"));
        GD.Print(TrN("There is %d apple", "There are %d apples", 3).Replace("%d", "3"));
        GD.Print(Atr("MENU_QUIT"));
    }
}
```

| 函数 | 说明 |
|---|---|
| `tr()` | 任何 Object 上可用 |
| `TranslationServer.translate()`、`TranslationServer.translate_plural()` | 非 Object 的静态上下文 |
| `atr()` | Node 上，同 `tr()`，遵守 `auto_translate_mode` |

- 找不到翻译时返回原键，界面上直接显示 `MENU_START`
- `tr_n()` 缺翻译时 n 为 1 返回第一个参数，其余返回第二个
- `%` 占位符顺序固定，多个变量用 `{name}` 命名占位符
- 复数只用于正整数与 0
- C# 字符串没有 Godot 的 format 与 `%`，占位符用 Replace 替换

### 响应语言切换

```gdscript
extends Label

func _notification(what: int) -> void:
	if what == NOTIFICATION_TRANSLATION_CHANGED:
		text = tr("MENU_TITLE")
```

```csharp
public partial class TitleLabel : Label
{
    public override void _Notification(int what)
    {
        if (what == NotificationTranslationChanged)
        {
            Text = Tr("MENU_TITLE");
        }
    }
}
```

- 节点进树时也收到一次该通知，此时子节点可能未就绪
- 要访问子节点先判 `is_node_ready()`

## 选语言

```gdscript
extends Node

func apply_language(saved: String) -> void:
	var locale := saved
	if locale.is_empty() or locale == "automatic":
		locale = OS.get_locale_language()
	TranslationServer.set_locale(locale)
```

```csharp
public partial class LanguageSetter : Node
{
    public void ApplyLanguage(string saved)
    {
        string locale = saved;
        if (string.IsNullOrEmpty(locale) || locale == "automatic")
        {
            locale = OS.GetLocaleLanguage();
        }
        TranslationServer.SetLocale(locale);
    }
}
```

- `OS.get_locale_language()` 取系统语言的 2 或 3 位代码
- `TranslationServer.set_locale()` 把 `en-US` 规整成 `en_US`
- 语言代码丢掉地区，`zh_TW` 只得到 `zh`，会匹配 `zh_CN` 的翻译
- 简繁并存时用 `OS.get_locale()` 取完整 locale
- 系统语言不在支持列表时用 `internationalization/locale/fallback`，默认 `en`
- 相近程度：`TranslationServer.compare_locales(a, b)` 返回 0 到 10
- 已加载语言：`TranslationServer.get_loaded_locales()`
- `TranslationServer.get_locale_name("zh_CN")` 返回英文名，如 Chinese, China
- 语言菜单显示各语言本地名，自己维护一张表
- 玩家选择存进设置文件，启动时读出来调一次

| Linux 的 `LANG` | 结果 |
|---|---|
| `C.UTF-8`，服务器与 CI 常见 | 得到 `C`，`set_locale` 规整成 `en` |
| 空串 | `set_locale` 报 `Locale cannot be an empty string` |

## 测试

- `godot --language fr` 临时用某语言启动，可带地区如 `zh_CN`
- `internationalization/locale/test` 非空时覆盖系统语言，导出后仍生效
- 只在编辑器里测，用 `editor` 特性标签覆盖该设置
- CJK 与泰语换行要字典，开 `internationalization/locale/include_text_server_data`
- 该项导出约增 4 MB

### 伪本地化

`internationalization/pseudolocalization/use_pseudolocalization` 打开后，翻译文本替换成带重音的字符串，用来找硬编码文本与溢出的布局。

| 项 | 行为 |
|---|---|
| 长度 | 默认不拉长，设 `expansion_ratio` 或 `double_vowels` |
| `%d` `%s` | 保留 |
| `{item}` 花括号占位符 | 被加重音，`format()` 替换不到 |
| 其他选项 | 同目录下，如 `fake_bidi` |
| 运行时开关 | `TranslationServer.pseudolocalization_enabled` |

## 字体回退

- 中日韩字形不在拉丁字体里
- 主字体的 `fallbacks` 里挂 CJK 字体，缺字时自动换用
- 主字体设在 `gui/theme/custom_font`
- 字体体积大时用 SystemFont 取系统字体，各平台字形不同

## 数字与方向

- `TranslationServer.format_number("123", "ar")` 4.6+ 转成目标语言的数字系统
- Control 的 `localize_numeral_system` 默认 true，SpinBox 与 ProgressBar 自动转换
- 文本里的数字不转
- 阿拉伯语与希伯来语从右到左
- `layout_direction` 默认继承父级
- 根节点由 `internationalization/rendering/root_node_layout_direction` 决定
- 该设置默认 `Control.LAYOUT_DIRECTION_APPLICATION_LOCALE`，跟随语言
- 容器自动镜像排列，图标与箭头不翻转，用 `is_layout_rtl()` 判断后自己翻
