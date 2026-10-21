# godot-claude-code-skills

给 Claude Code 用的 Godot 4 skills。目的是让 AI 写 Godot 代码时先用引擎和编辑器自带的节点、资源、项目设置，不再重复造轮子，并避开照直觉会写错的地方。

跟最新稳定版，现在是 4.7.2，最低照顾 4.4。所有 API 名对照引擎源码的类参考检查过，所有 GDScript 示例在 Godot 4.7.2 无头加载通过，所有 C# 示例用 Godot.NET.Sdk 4.7.2 编译通过。

# 安装

内部使用，不发布到官方目录。仓库是私有的，本机 git 要能无交互拉取：ssh-agent 里有 key，或 `gh auth login` 后 `gh auth setup-git`。

个人安装：

```
claude plugin marketplace add MindsMaster/godot-claude-code-skills
claude plugin install godot-skills@godot-claude-code-skills
```

让某个 Godot 项目的所有人自动启用，在那个项目提交 `.claude/settings.json`：

```json
{
  "extraKnownMarketplaces": {
    "godot-claude-code-skills": {
      "source": {
        "source": "github",
        "repo": "MindsMaster/godot-claude-code-skills"
      }
    }
  },
  "enabledPlugins": {
    "godot-skills@godot-claude-code-skills": true
  }
}
```

队友打开项目并信任该目录后生效。`plugin.json` 不写 `version`，每次更新都按最新提交拉取，用 `claude plugin update godot-skills` 更新。

本地调试：`claude plugin marketplace add ./godot-claude-code-skills` 指向本地克隆。

# 内容

<!-- skills-table -->

# 测试

```
GODOT_BIN=/path/to/godot DOTNET_BIN=/path/to/dotnet python3 tests/check.py
```

细节见 `tests/README.md`，编写规则见 `CLAUDE.md`。
