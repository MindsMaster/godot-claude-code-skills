# 测试

```
python3 tests/check.py [lint] [api] [gd] [cs] [--only 路径子串] [--strict]
```

| 步骤 | 查什么 | 依赖 |
| --- | --- | --- |
| lint | frontmatter、SKILL.md 行数、断链、禁用措辞 | 无 |
| api | 行内代码的类名、`Class.member`、项目设置路径、代码块里的已弃用类、版本标注 | `tests/data/godot_api.json.gz` |
| gd | GDScript 代码块逐个无头加载 未标类型按错误算 | `GODOT_BIN` |
| cs | C# 代码块用 Godot.NET.Sdk 编译 开 IDE0011 | `DOTNET_BIN` .NET 8 SDK |

每个检查一个文件，从头读到尾就是这一项的全部逻辑：

| 文件 | 内容 |
| --- | --- |
| `check.py` | 入口 收集 skills 下的 md 依次跑各项 |
| `markdown.py` | 把 md 拆成正文行和代码块 读 frontmatter |
| `lint.py` | 格式与措辞 |
| `api.py` | 对照 `data/godot_api.json.gz` |
| `gdscript.py` | 生成临时工程 用 Godot 加载每个片段 |
| `csharp.py` | 生成临时 csproj 编译所有片段 |
| `build_api_index.py` | 从引擎源码生成 API 索引 升级版本时跑 |

`data/allow_names.txt` 放引擎类参考里查不到但确实存在的名字：示例里自定义的类型、旧版本类名、未写进文档的项目设置。

代码块上一行的标记：

```
<!-- check: skip -->
<!-- check: extends CharacterBody2D -->
<!-- check: deprecated -->
```

`deprecated` 用于故意展示旧写法的代码块。

# 参考副本

```
mkdir -p ref && cd ref
git clone --depth 1 --filter=blob:none --branch 4.7.2-stable https://github.com/godotengine/godot.git
git clone --depth 1 https://github.com/godotengine/godot-docs.git
git clone --depth 1 https://github.com/godotengine/godot-cpp.git
```

# 升级 API 索引

```
python3 tests/build_api_index.py --godot-cpp ref/godot-cpp --godot ref/godot --target 4.7
```

`--godot` 要指向对应稳定版标签的引擎源码，弃用标记和项目设置取自它的 `doc/classes`。
