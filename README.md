# godot-claude-code-skills

给 Claude Code 用的 Godot 4 skills。目的是让 AI 写 Godot 代码时先用引擎和编辑器自带的节点、资源、项目设置，不再重复造轮子，并避开照直觉会写错的地方。

跟最新稳定版，现在是 4.7.2，最低照顾 4.4。所有 API 名对照引擎源码的类参考检查过，所有 GDScript 示例在 Godot 4.7.2 无头加载通过，所有 C# 示例用 Godot.NET.Sdk 4.7.2 编译通过。

# 安装

作为插件：

```
/plugin marketplace add MindsMaster/godot-claude-code-skills
/plugin install godot-skills@godot-claude-code-skills
```

只想放进某个项目：把 `skills/` 下需要的目录拷到项目的 `.claude/skills/`。

# 内容

<!-- skills-table -->

# 测试

```
GODOT_BIN=/path/to/godot DOTNET_BIN=/path/to/dotnet python3 tests/check.py
```

细节见 `tests/README.md`，编写规则见 `CLAUDE.md`。
