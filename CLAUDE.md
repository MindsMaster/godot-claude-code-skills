# 本仓库

Claude Code 用的 Godot 4 skills，以插件形式发布。`skills/<name>/SKILL.md` 是入口，长内容放 `skills/<name>/references/`。

跟最新稳定版，现在是 4.7.2，最低照顾 4.4。4.5 以后才有的类和成员在正文写明 `4.5+` 这类版本号。dev 和 beta 里的新东西不写。

升级稳定版时：重跑 `tests/build_api_index.py --target <新版本>`，改 `tests/check.py` 的 `--sdk-version` 默认值和 `.github/workflows/check.yml` 的版本号，再跑全套测试。

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

两三句定位：解决什么 不管什么 转去哪个 skill

## 先查内置
表格：需求 | 用这个 | 别自己写

## 做法
按任务分小节 每节给最短可运行代码

## 陷阱
照直觉写会出错的点 每条一行到三行

## 参考
references 链接与 docs.godotengine.org 链接
```

SKILL.md 控制在 300 行内。细节表、长示例、少用的 API 放 references，并在 SKILL.md 里写清什么时候去读哪个文件。

# 写法

正文用中文，代码、类名、成员名、项目设置路径保持英文原样。语气照 `docs/StylePrompt.md` 的措辞部分：先给结论，数字直接给，不写"显著""其实""真正""值得注意的是"，不用破折号，不用引号强调。

行内代码里的 `Class.member` 会被测试按引擎 API 查一遍，写错会失败。

代码示例：

- GDScript 一律静态类型，`:=` 或显式类型，函数写返回类型。缩进用 tab
- GDScript 代码块必须是能独立解析的完整脚本。只写方法片段时在代码块上一行加 `<!-- check: extends Node2D -->` 指定基类
- C# 代码块写完整类，或只写成员并同样用 `<!-- check: extends CharacterBody2D -->` 指定基类。`if` 等一律带花括号
- 不能独立编译的示例，如引用了别处定义的类，在上一行加 `<!-- check: skip -->`，尽量少用
- 改了 GDScript 示例就同步改它的夹具，夹具里用 `expect` 验证正文说的行为
- 代码注释照 `docs/StylePrompt.md`：默认不写 只写陷阱和外部契约 不超过 15 字
- 场景文件、项目设置用 `ini` 代码块，着色器用 `glsl` 代码块，这两类不跑检查

GDScript 为主。C# 只在写法和 GDScript 不同或容易写错时给，C# 通用规则集中在 `godot-csharp`。

# 测试

```
python3 tests/check.py              # lint api gd run cs 全跑
python3 tests/check.py run          # 只真跑 GDScript 示例
python3 tests/check.py lint api     # 不需要 Godot 和 dotnet
python3 tests/check.py --only godot-2d
```

`GODOT_BIN` 指向 Godot 4.7.2 可执行文件，`DOTNET_BIN` 指向 .NET 8 SDK 的 dotnet。

- lint：frontmatter、行数、断链、禁用措辞
- api：行内代码的类名和成员、代码块里的已弃用类、版本标注
- gd：每个 GDScript 代码块用 Godot 无头加载，未标类型和引擎默认警告都按错误算
- run：每个 GDScript 代码块真跑一遍，有错误或警告输出就失败。缺的场景、资源、调用写在 `tests/run/<skill>.md` 夹具里，格式见 `tests/README.md`。render 模式要 `xvfb-run` 和 Vulkan 驱动，没有 GPU 时装 `mesa-vulkan-drivers`
- cs：所有 C# 代码块用 Godot.NET.Sdk 编译，开 IDE0011

未知类型名报警告。确实不是引擎类的名字，如示例里自定义的 `PlayerStats`，加进 `tests/data/allow_names.txt`。

# 提交

格式 `type(scope): 中文一句话`，不带正文，不加署名尾行。scope 用 skill 名去掉 `godot-` 前缀，如 `feat(2d-in-3d): 新增 Sprite3D 阴影与排序做法`。测试框架用 `tests`。
