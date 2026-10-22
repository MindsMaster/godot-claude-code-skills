# 本地化细节

SKILL.md 的本地化一节讲了 `tr()` 和自动翻译。本文讲表格式、导入、注册、运行时切换和测试。

## 选哪种格式

| 格式 | 适合 | 注意 |
|---|---|---|
| CSV | 小团队，表格里直接改，键用 `MENU_START` 这类大写键 | 一个文件包含所有语言。复数与上下文需要额外列，都是 4.6+ |
| PO / MO | 有专业译者与翻译平台，英文原文当键 | 要 POT 提取与 gettext 工具链 |

两种都可以在同一个项目里混用，注册后合并查找。

## CSV

第一行是表头，第一列是键，其余列是语言代码。

```
keys,en,zh_CN,ja
MENU_START,Start,开始,スタート
MENU_QUIT,Quit,退出,終了
```

- 语言列的列头用 locale 代码，如 `zh_CN` `en_GB`。列头以 `_` 开头的列当注释，不导入
- 左上角单元格忽略
- 键区分大小写
- 含逗号与换行的单元格用双引号包住，Excel 与 Google Sheets 导出时自动处理
- 导入后在同目录生成压缩的翻译资源，每种语言一个。Import 面板可以改压缩选项，改完点 Reimport
- 导入不等于生效，必须注册，见下文

### 复数列

4.6+ 可加一列 `?plural`，不能放第一列。第二行起的行头是单数形式，译文按语言需要的形式依次往下写：

```
en,?plural,fr,ru
?pluralrule,,nplurals=2; plural=(n >= 2);,
There is %d apple,There are %d apples,Il y a %d pomme,Есть %d яблоко
,,Il y a %d pommes,Есть %d яблока
,,,Есть %d яблок
```

`?pluralrule` 行给每种语言写 gettext 复数规则。带复数列的表，控件不会自动翻译，只能用 `tr_n()`。

单数行头同时是查找用的键，`tr_n()` 的前两个参数要写成单数行头和 `?plural` 列的文本，缺翻译时回退到它们。用 `ITEM_ONE` 这类键名当单数行头时，回退文本不含 `%d`，`%` 会报 `String formatting error`。

### 上下文列

4.6+ 可加 `?context` 列，不能放第一列。用英文原文当键时用它区分同形异义。带上下文的行同样要手动调 `tr()` 或 `tr_n()`。

```
en,?context,fr
Letter,Alphabet,Lettre
Letter,Message,Courrier
```

## PO

- 项目设置的 Localization 页：`internationalization/locale/translations_pot_files` 列出要提取的场景与脚本，点 Generate 指定输出的 `.pot` 路径
- 提取规则：场景里的 `text` `*_text` `title` `tooltip_text` `accessibility_name` 等属性，脚本里的 `tr()` `tr_n()` `atr()` 调用，以及对 `text` `placeholder_text` `tooltip_text` 的赋值
- 提取尊重 `auto_translate_mode`：设成 disabled 的节点不会被提取
- 不想提取的字符串在同一行或上一行写 `NO_TRANSLATE` 注释，给译者的说明写 `TRANSLATORS:` 注释
- `msginit` 从 POT 生成各语言 `.po`，`msgmerge` 同步新增字符串，`msgfmt` 编译 `.mo`。引擎直接读 `.po`，译者不用装工具就能测。`msgmerge` 后源文变动的条目带 `fuzzy` 标记，译文更新并去掉标记之前引擎不读

## 注册与资源重映射

- 注册位置：项目设置 Localization 页 Translations 标签，对应 `internationalization/locale/translations`。CSV 导入出的每个翻译资源或每个 `.po` 都要加
- 重映射 `internationalization/locale/translation_remaps`：按语言替换整个资源，如带文字的贴图和配音。不支持字体，字体用回退链
- 运行时可以 `TranslationServer.add_translation(translation)` 与 `remove_translation`，用于模组与 DLC 语言包

## 脚本里怎么翻

```gdscript
extends Node

func _ready() -> void:
	print(tr("MENU_START"))
	print(tr("PICKED_UP").format({item = tr("ITEM_SWORD")}))
	print(tr("Close", "Distance"))
	print(tr_n("There is %d apple", "There are %d apples", 3) % 3)
	print(atr("MENU_QUIT"))
```

- `tr()` 用在任何 Object 上，非 Object 的静态上下文用 `TranslationServer.translate()` 与 `TranslationServer.translate_plural()`
- `atr()` 在 Node 上，行为同 `tr()` 并遵守 `auto_translate_mode`
- 找不到翻译时返回原键，缺键在界面上直接显示成 `MENU_START`，很容易发现。`tr_n()` 缺翻译时 n 为 1 返回第一个参数，其余返回第二个
- `%` 占位符的顺序固定，`{name}` 命名占位符可以让译者调整顺序，多个变量时用后者
- 复数只用于正整数与 0

### 响应语言切换

```gdscript
extends Label

func _notification(what: int) -> void:
	if what == NOTIFICATION_TRANSLATION_CHANGED:
		text = tr("MENU_TITLE")
```

该通知在节点进树时也会到一次，此时子节点可能没就绪，要访问子节点先判 `is_node_ready()`。

## 选语言

```gdscript
extends Node

func apply_language(saved: String) -> void:
	var locale := saved
	if locale.is_empty() or locale == "automatic":
		locale = OS.get_locale_language()
	TranslationServer.set_locale(locale)
```

- `OS.get_locale_language()` 取系统语言的 2 或 3 位代码，`TranslationServer.set_locale()` 会把 `en-US` 规整成 `en_US`
- Linux 上系统语言只看 `LANG`。服务器与 CI 常见的 `C.UTF-8` 得到 `C`，`set_locale` 规整成 `en`。`LANG` 设成空串时得到空串，`set_locale` 报 `Locale cannot be an empty string`
- 语言代码丢掉地区，`zh_TW` 的系统只得到 `zh`，会匹配到 `zh_CN` 的翻译。简繁并存时改用 `OS.get_locale()` 取完整 locale
- 系统语言不在支持列表时，`internationalization/locale/fallback` 起作用，默认 `en`
- 比较相近程度用 `TranslationServer.compare_locales(a, b)`，返回 0 到 10。已加载的语言用 `TranslationServer.get_loaded_locales()`
- `TranslationServer.get_locale_name("zh_CN")` 返回英文名如 "Chinese, China"。语言选择菜单按惯例显示各语言的本地名，自己维护一张表
- 玩家选择存进设置文件，启动时读出来调一次，不依赖引擎记忆

## 测试

- 命令行 `godot --language fr` 临时用某语言启动，参数是小写 2 或 3 位语言代码，可带地区如 `zh_CN`
- `internationalization/locale/test` 非空时覆盖系统语言，导出后依然生效，只想在编辑器里测试要用 `editor` 特性标签覆盖
- 伪本地化：`internationalization/pseudolocalization/use_pseudolocalization` 打开后，所有翻译文本被替换成带重音的字符串，默认不拉长，拉长要设 `expansion_ratio` 或 `double_vowels`。用来找漏掉的硬编码文本与溢出的布局。`%d` `%s` 这类百分号占位符保留，`{item}` 这类花括号占位符会被加重音，`format()` 替换不到。其他可调项在同一目录下，如 `fake_bidi`。运行时开关是 `TranslationServer.pseudolocalization_enabled`
- 导出时 CJK 与泰语等换行需要字典，开 `internationalization/locale/include_text_server_data` 约增加 4 MB

## 字体回退

中日韩字形不在拉丁字体里。在主字体的 `fallbacks` 里挂 CJK 字体，Label 遇到缺字自动换用。主字体设在 `gui/theme/custom_font`。字体体积大的项目用 SystemFont 取系统字体，注意各平台字形不同。

## 数字与方向

- `TranslationServer.format_number("123", "ar")` 4.6+ 把西方数字转成目标语言的数字系统。Control 的 `localize_numeral_system` 默认 true，SpinBox 与 ProgressBar 的数值自动转换，文本里的数字不转
- 阿拉伯语与希伯来语从右到左，Control 的 `layout_direction` 默认继承父级，根节点由 `internationalization/rendering/root_node_layout_direction` 决定，默认 `Control.LAYOUT_DIRECTION_APPLICATION_LOCALE` 跟随语言。容器会自动镜像排列
- 布局为 RTL 时，图标与箭头不会自动翻转，用 `is_layout_rtl()` 判断后自己翻
