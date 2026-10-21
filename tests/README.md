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

代码块上一行的标记：

```
<!-- check: skip -->
<!-- check: extends CharacterBody2D -->
```

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
