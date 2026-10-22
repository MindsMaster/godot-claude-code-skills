# godot-claude-code-skills

给 Claude Code 用的 Godot 4 skills。目的是让 AI 写 Godot 代码时先用引擎和编辑器自带的节点、资源、项目设置，不再重复造轮子，并避开照直觉会写错的地方。

跟最新稳定版，现在是 4.7.2，最低照顾 4.4。所有 API 名对照引擎源码的类参考检查过。184 个 GDScript 示例在 Godot 4.7.2 里真跑，正文说的行为用断言验证，其中 30 个用软件 Vulkan 真渲染读像素。21 个 C# 示例用 Godot.NET.Sdk 4.7.2 编译通过，没有真跑。CI 每次推送全部重跑。

# 安装

内部使用，不发布到官方目录。仓库是私有的，本机 git 要能无交互拉取：ssh-agent 里有 key，或 `gh auth login` 后 `gh auth setup-git`。

推荐只在 Godot 项目里启用。装在用户级别时，16 个 skill 的 description 共约 7700 字符，会出现在每个项目的每一轮上下文里。正文只在调用时加载，非 Godot 项目里基本不会被调用，但这部分开销照算。

在 Godot 项目目录里装到项目级别：

```
claude plugin marketplace add MindsMaster/godot-claude-code-skills
claude plugin install godot-skills@godot-claude-code-skills --scope project
```

想在所有项目里用，去掉 `--scope project`。

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

队友打开项目并信任该目录后生效。

市场要从 Git 仓库添加，只给 `marketplace.json` 的链接时插件的相对路径 `"source": "."` 会失效。

# 更新

`plugin.json` 和 `marketplace.json` 都不写 `version`，插件版本就是安装目录的提交 SHA，每次推送新提交用户都能拿到。以后也不要加 `version`，加了但推送时没改，用户收不到新内容。

第三方市场默认不自动更新，两种方式任选：

- 手动：`claude plugin update godot-skills@godot-claude-code-skills`，或会话里 `/plugin` 的 Installed 里选插件点 Update now
- 自动：会话里 `/plugin`，Marketplaces 里选 `godot-claude-code-skills`，点 Enable auto-update。之后每次会话发出第一条消息后 10 分钟内检查一次

更新装好后当前会话用 `/reload-plugins` 生效，或下次启动生效。

本地调试：`claude plugin marketplace add ./godot-claude-code-skills` 指向本地克隆，每次启动会话都读当前文件，不用更新。

# 内容

| skill | 内容 |
| --- | --- |
| `godot-builtin-first` | 总入口 写功能前先查内置方案 指向细分 skill |
| `godot-scene-architecture` | 场景组合 节点引用 信号 分组 autoload 状态机 生命周期 |
| `godot-gdscript` | 静态类型 注解 信号与 await 警告设置 |
| `godot-csharp` | 命名映射 源码生成器 StringName 缓存 生命周期 热重载 |
| `godot-2d` | CharacterBody2D TileMapLayer Camera2D Parallax2D 像素风 2D 光照 |
| `godot-3d` | CharacterBody3D 物理引擎 光照与 GI 导入管线 LOD 骨骼修改器 |
| `godot-2d-in-3d` | Sprite3D billboard alpha 裁剪与阴影 SubViewport HD-2D 后处理 |
| `godot-ui` | Container 布局 Theme 血条 RichTextLabel 拉伸模式 本地化 |
| `godot-animation` | AnimationPlayer AnimationTree Tween SpriteFrames 确定性回放 |
| `godot-input` | InputMap 动作 手柄 死区 改键存档 |
| `godot-audio` | 总线布局 音量设置 AudioStreamRandomizer 复音 动态音乐 |
| `godot-resources-data` | 自定义 Resource 线程加载 存档 导入期烘焙 内置曲线资源 |
| `godot-shaders-vfx` | shader 参数 instance uniform 粒子 Environment 后处理 CompositorEffect |
| `godot-editor-tooling` | @tool EditorPlugin Inspector 插件 导入插件 撤销 快捷键 |
| `godot-headless-testing` | 无头命令行 冒烟场景 退出码 CI GUT gdUnit4 |
| `godot-performance` | Profiler 与 Monitor MultiMesh 物理插值 WorkerThreadPool shader 编译卡顿 |

`evals/` 是 `claude plugin eval` 用例，对比装与不装插件时 AI 是否选用内置方案。

# 测试

```
GODOT_BIN=/path/to/godot DOTNET_BIN=/path/to/dotnet python3 tests/check.py
```

依次跑 lint、api、gd、run、cs。run 把每个 GDScript 示例真跑一遍，示例要的场景、资源和调用写在 `tests/run/<skill>.md` 夹具里，有错误或警告输出、断言失败、超时都算失败。真渲染的示例要 `xvfb-run` 和 Vulkan 驱动，没有显卡时装 `mesa-vulkan-drivers`。

细节见 `tests/README.md`，编写规则见 `CLAUDE.md`。
