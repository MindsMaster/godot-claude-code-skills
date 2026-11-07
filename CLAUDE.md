# 本仓库

Claude Code 用的 Godot 4 skills，以插件形式发布。`skills/<name>/SKILL.md` 是入口，长内容放 `skills/<name>/references/`。

跟最新稳定版，现在是 4.7.2，最低照顾 4.4。4.5 以后才有的类和成员在正文写明 `4.5+` 这类版本号。dev 和 beta 里的新东西不写。

升级稳定版时：重跑 `tests/build_api_index.py --target <新版本>`，改 `tests/check.py` 的 `--sdk-version` 默认值和 `.github/workflows/check.yml` 的版本号，再跑全套测试。

`plugin.json` 和 `marketplace.json` 不写 `version`，用户按提交 SHA 拿更新。加了却忘改，用户收不到新内容。

# 依据

API 只以引擎源码为准，不凭记忆写。

- 类、方法、属性、信号、枚举：`godot/doc/classes/*.xml`、`godot/modules/*/doc_classes/*.xml`，或 `tests/data/godot_api.json.gz`
- 跨版本差异：`godot-cpp/gdextension/extension_api-4-*.json`
- 用法和最佳实践：`godot-docs/tutorials/`
- C# 名字：引擎名转大驼峰，`move_and_slide` 对应 `MoveAndSlide`，`Object` 对应 `GodotObject`

本地参考副本放在仓库同级目录 `../ref`，没有就按 `tests/README.md` 拉取。

# SKILL.md 结构

```
---
name: 与目录同名
description: 何时用 中文加英文关键词 写清触发场景 不超过 1024 字符
---

# 标题

一句话定义本 skill 管什么 可再加一句默认做法

## 范围
表格：不含 | 去哪   列出相邻主题归哪个 skill

## 先查内置
表格：需求 | 用这个 | 别自己写

## 做法
### 每个任务一节   一句结论 最短可运行代码 要点列表

## 陷阱
表格：现象 | 做法

## 参考
references 链接 每条写清什么时候读 加 docs.godotengine.org 链接
```

`##` 只有这五个，按这个顺序，其他主题一律放 `## 做法` 下的 `###`。写了 `## 范围` 的 SKILL.md 由 lint 按此检查。

SKILL.md 控制在 300 行内。细节表、长示例、少用的 API、单次排查得出的偏门问题放 references，并在 SKILL.md 里写清什么时候去读哪个文件。

一个知识点只在一个 skill 里展开，别处在 `## 范围` 或正文里写一行转去哪。

references 文件结构：

```
# 标题

一句话写本文内容 何时读写在 SKILL.md 的参考节 这里不重复

## 主题
同 SKILL.md 的 ###：一句结论 代码 要点或表格
```

# GDScript 与 C#

两种语言都完整支持，每个 GDScript 示例都有 C# 对照。

- SKILL.md 只放 GDScript 代码。C# 对照放 `references/csharp.md`，它的 `##` 取 SKILL.md `## 做法` 下的 `###` 同名，含 GDScript 代码的 `###` 必须有，只写 C# 代码和 C# 独有的要点，不重复正文
- 其他 references 文件里，每个 GDScript 代码块后紧跟它的 C# 版本
- 只有 GDScript 才有的内容，如 GDScript 警告设置，在代码块上一行的 check 标记里加 `gdonly`，如 `<!-- check: extends Node; gdonly -->`
- 跨主题的 C# 通用规则放 `godot-csharp`：命名映射、源码生成器、`StringName` 缓存、生命周期、async
- SKILL.md 的 `## 参考` 第一条写 C# 项目先读 `references/csharp.md`
- C# 只验证编译，不跑。行为断言靠对应的 GDScript 夹具

# 写法

正文用中文，代码、类名、成员名、项目设置路径保持英文原样。语气照 `docs/StylePrompt.md` 的措辞部分：先给结论，数字直接给，不写"显著""其实""真正""值得注意的是"，不用破折号，不用引号强调。

读者是 Claude，按参考手册写，省 token：

- 一条列表只写一个事实或一条规则，40 字内，行内代码和链接按 1 字计，`## 参考` 不计。写不下就拆条或改表格
- 默认值、枚举取值、方案对比、现象与做法，用表格
- 标题用名词短语，写主题或类名，不写判断句
- 不写场景描述、比喻、心路历程。不写谁在什么情况下会怎样，直接写条件和结果
- 正文和陷阱不重复同一条，陷阱只收照直觉写会错、正文没覆盖的

行内代码里的 `Class.member` 会被测试按引擎 API 查一遍，写错会失败。

代码示例：

- GDScript 一律静态类型，`:=` 或显式类型，函数写返回类型。缩进用 tab
- GDScript 代码块必须是能独立解析的完整脚本。只写方法片段时在代码块上一行加 `<!-- check: extends Node2D -->` 指定基类
- C# 代码块写完整类，或只写成员并同样用 `<!-- check: extends CharacterBody2D -->` 指定基类。`if` 等一律带花括号
- 不能独立编译的示例，如引用了其他文件定义的类，在上一行加 `<!-- check: skip -->`，尽量少用
- 改了 GDScript 示例就同步改它的夹具和 C# 对照，夹具里用 `expect` 验证正文说的行为
- 代码注释照 `docs/StylePrompt.md`：默认不写 只写陷阱和外部契约 不超过 15 字
- 场景文件、项目设置用 `ini` 代码块，着色器用 `glsl` 代码块，这两类不跑检查

同一文件内的 C# 代码块共用一个命名空间，可以引用彼此的类，类名不能重复。

# 测试

```
python3 tests/check.py              # lint api gd run cs 全跑
python3 tests/check.py run          # 只真跑 GDScript 示例
python3 tests/check.py lint api     # 不需要 Godot 和 dotnet
python3 tests/check.py --only godot-2d
```

`GODOT_BIN` 指向 Godot 4.7.2 可执行文件，`DOTNET_BIN` 指向 .NET 8 SDK 的 dotnet。

- lint：frontmatter、行数、断链、禁用措辞。写了 `## 范围` 的 skill 另查骨架、范围表、列表长度、C# 对照
- api：行内代码的类名和成员、代码块里的已弃用类、版本标注
- gd：每个 GDScript 代码块用 Godot 无头加载，未标类型和引擎默认警告都按错误算
- run：每个 GDScript 代码块真跑一遍，有错误或警告输出就失败。缺的场景、资源、调用写在 `tests/run/<skill>.md` 夹具里，格式见 `tests/README.md`。render 模式要 `xvfb-run` 和 Vulkan 驱动，没有 GPU 时装 `mesa-vulkan-drivers`
- cs：所有 C# 代码块用 Godot.NET.Sdk 编译，开 IDE0011

未知类型名报警告。确实不是引擎类的名字，如示例里自定义的 `PlayerStats`，加进 `tests/data/allow_names.txt`。

# 提交

格式 `type(scope): 中文一句话`，不带正文，不加署名尾行。scope 用 skill 名去掉 `godot-` 前缀，如 `feat(2d-in-3d): 新增 Sprite3D 阴影与排序做法`。测试框架用 `tests`。
