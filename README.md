![godot-claude-code-skills](.github/banner.jpg)

# godot-claude-code-skills

中文 | [English](README.en.md)

[![check](https://github.com/MindsMaster/godot-claude-code-skills/actions/workflows/check.yml/badge.svg)](https://github.com/MindsMaster/godot-claude-code-skills/actions/workflows/check.yml)
[![Godot](https://img.shields.io/badge/Godot-4.4%20~%204.7.2-478CBF?logo=godotengine&logoColor=white)](https://godotengine.org/)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-join-5865F2?logo=discord&logoColor=white)](https://discord.invite.azuramc.cc/)

面向 Godot 4 的 Claude Code 插件，包含 16 个 skill。引导 Claude Code 优先使用引擎内置的节点、资源与项目设置，并规避常见误用。覆盖 2D、3D、UI、动画、音频、数据、着色器、编辑器扩展与无头测试，支持 GDScript 与 C#。

# 示例

安装后无需指定 skill，Claude Code 按需求自动加载。以下列需求为例：

> 给玩家加一个跟随相机：平滑跟随，不能拍到关卡外面，受伤时震屏。玩家掉坑后在检查点复活，复活瞬间镜头要立刻到位。

加载 `godot-2d` 后的实现：

- `Camera2D` 开启 `position_smoothing_enabled`，以 `limit_*` 限定关卡范围
- 震屏修改 `offset`，噪声取自 `FastNoiseLite`
- 复活代码设置 `global_position` 后立即调用 `reset_smoothing()`

其他场景：

| 需求 | 内置方案 |
| --- | --- |
| 瓦片关卡与挖地 | `TileMapLayer`、`TileSet` terrain、`set_cells_terrain_connect` |
| 策划可编辑的数值表 | 自定义 `Resource` 存为 `.tres`，外部表格在导入期转换 |
| 血条与 HUD | `ProgressBar`、Container 布局、项目级 `Theme` |
| 3D 场景中的 2D 角色 | `Sprite3D` billboard 与 `alpha_cut` 投影 |
| 对白时压低音乐 | 总线上的 `AudioEffectCompressor`，`sidechain` 指向 Voice |
| 大量敌人共用材质并各自闪白 | `instance uniform` 与 `Tween` |

# 验证

- API：正文中的类名与成员名均对照 Godot 引擎源码的类参考校验
- GDScript：全部示例在 Godot 4.7.2 中运行，正文所述行为以断言验证，渲染相关示例经软件 Vulkan 渲染后读取像素校验
- C#：全部示例以 Godot.NET.Sdk 4.7.2 编译
- CI：每次推送执行全部检查

以最新稳定版 4.7.2 为准，兼容 4.4 及以上。4.5 及以后新增的 API 在正文中标注版本。

# 评测

`evals/` 中每个用例给出一项开发需求，在安装与未安装插件两种条件下分别运行。由正则断言与 LLM 评审判定是否采用内置方案、结果在引擎中是否成立，全部判定项通过记为通过。

2026 年 10 月，Claude Code 2.1.309 默认模型。每种条件各运行 3 次，无头运行用例在 skill 修订后重跑 6 次：

| 需求 | 安装 | 未安装 | 未通过的原因 |
| --- | --- | --- | --- |
| 跟随相机与复活 | 3/3 | 0/3 | 每帧比较相机位移推测传送，未在复活处调用 `reset_smoothing()` |
| 音量设置与对白时压低音乐 | 3/3 | 1/3 | 逐帧读取 Voice 总线峰值，以脚本调整音乐音量 |
| C# 共用材质的受击闪白 | 3/3 | 1/3 | 着色器重新采样 `TEXTURE`，未使用已含 modulate 的 `COLOR` |
| 3D 场景中的像素角色 | 3/3 | 1/3 | 未读取贴图像素，角色脚底悬空 1 像素 |
| 策划数据与导出 | 3/3 | 2/3 | `waves.csv` 未改为 keep 导入，导出包中读不到 |
| 瓦片关卡与挖地 | 3/3 | 0/3 | 挖地后以地面 terrain 重算邻格，邻格瓦片不更新 |
| HUD 与统一字体 | 3/3 | 0/3 | `.tscn` 缺少 `node_paths`，导出的玩家引用在运行时为空 |
| 无头运行修复脚本错误与警告 | 6/6 | 2/6 | 未开启警告输出即判定无警告 |
| 合计 | 27/27 | 7/27 | |

复现：

```
claude plugin eval . --scaffold --trust-plugin --allow-tools Edit Write Bash
```

授予 Bash 需要 `bubblewrap` 与 `socat`。无头运行用例从 `GODOT_BIN` 或 PATH 上的 `godot` 复制 Godot 可执行文件。

# 内容

| skill | 范围 |
| --- | --- |
| `godot-builtin-first` | 总入口，编写功能前检索内置方案并转至细分 skill |
| `godot-scene-architecture` | 场景组合、节点引用、信号、分组、autoload、状态机、生命周期 |
| `godot-gdscript` | 静态类型、注解、信号与 await、警告设置 |
| `godot-csharp` | 命名映射、源码生成器、StringName 缓存、生命周期、热重载 |
| `godot-2d` | CharacterBody2D、TileMapLayer、Camera2D、Parallax2D、像素风、2D 光照 |
| `godot-3d` | CharacterBody3D、物理引擎、光照与 GI、导入管线、LOD、骨骼修改器 |
| `godot-2d-in-3d` | Sprite3D billboard、alpha 裁剪与阴影、SubViewport、HD-2D 后处理 |
| `godot-ui` | Container 布局、Theme、血条、RichTextLabel、拉伸模式、本地化 |
| `godot-animation` | AnimationPlayer、AnimationTree、Tween、SpriteFrames、确定性回放 |
| `godot-input` | InputMap 动作、手柄、死区、改键存档 |
| `godot-audio` | 总线布局、音量设置、AudioStreamRandomizer、复音、动态音乐 |
| `godot-resources-data` | 自定义 Resource、线程加载、存档、导入期烘焙、内置曲线资源 |
| `godot-shaders-vfx` | shader 参数、instance uniform、粒子、Environment、后处理、CompositorEffect |
| `godot-editor-tooling` | @tool、EditorPlugin、Inspector 插件、导入插件、撤销、快捷键 |
| `godot-headless-testing` | 无头命令行、冒烟场景、退出码、CI、GUT、gdUnit4 |
| `godot-performance` | Profiler 与 Monitor、MultiMesh、物理插值、WorkerThreadPool、shader 编译卡顿 |

# 安装

建议仅在 Godot 项目中启用。用户级安装时，16 个 skill 的 description 共约 3400 字符，会进入所有项目每一轮对话的上下文。skill 正文仅在调用时加载。

在 Godot 项目目录中按项目级安装：

```
claude plugin marketplace add MindsMaster/godot-claude-code-skills
claude plugin install godot-skills@godot-claude-code-skills --scope project
```

省略 `--scope project` 即为用户级安装。

为项目全体成员启用，在该项目中提交 `.claude/settings.json`：

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

成员打开项目并信任该目录后生效。

市场须从 Git 仓库添加。仅提供 `marketplace.json` 链接时，插件的相对路径 `"source": "."` 无法解析。

# 更新

插件不设版本号，每个提交即一个版本。第三方市场默认不自动更新，可选以下方式：

- 手动：执行 `claude plugin update godot-skills@godot-claude-code-skills`，或在会话中打开 `/plugin`，于 Installed 中选择插件并点击 Update now
- 自动：在会话中打开 `/plugin`，于 Marketplaces 中选择 `godot-claude-code-skills` 并点击 Enable auto-update。此后每次会话发出首条消息后 10 分钟内检查一次

更新后执行 `/reload-plugins` 或重启会话生效。

# 贡献

欢迎提交 issue 与 PR。报告 skill 内容与引擎行为不符时，请附 Godot 版本与最小复现。

编写规范见 `CLAUDE.md`。本地调试时执行 `claude plugin marketplace add ./godot-claude-code-skills` 指向本地克隆，每次会话启动时读取当前文件。

提交 PR 前运行全部测试：

```
GODOT_BIN=/path/to/godot DOTNET_BIN=/path/to/dotnet python3 tests/check.py
```

依次执行 lint、api、gd、run、cs。run 逐个运行 GDScript 示例，示例所需的场景、资源与调用定义在 `tests/run/<skill>.md` 夹具中，输出错误或警告、断言失败、超时均判为失败。渲染相关示例需要 `xvfb-run` 与 Vulkan 驱动，无 GPU 时安装 `mesa-vulkan-drivers`。详见 `tests/README.md`。

# 社区

- Discord：<https://discord.invite.azuramc.cc/>
- QQ 群：1046048297

# 许可

MIT，见 `LICENSE`。

横幅与图标使用的第三方素材：

- 背景：Godot 示例项目 [tps-demo](https://github.com/godotengine/tps-demo) 截图，作者 Juan Linietsky、Fernando Miguel Calabró，以 [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) 授权。已裁切并叠加渐变
- Godot 标志：作者 Andrea Calabró，以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 授权
- Claude 标志：Anthropic 的商标

本项目与 Anthropic 及 Godot 基金会无隶属关系。
