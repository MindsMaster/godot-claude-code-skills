---
name: godot-builtin-first
description: 在 Godot 4 项目里写任何功能之前先用。查引擎自带的节点 资源 项目设置 编辑器功能能不能直接做，再决定写代码，并指向细分 skill。Use before implementing any feature in a Godot 4 project (GDScript or C#), when a project.godot exists, or when about to write a custom camera, animation, tween, state machine, UI layout, JSON parser, loader, input mapping, audio pool, particle system, editor tool. Triggers on Godot, godot, .tscn, .gd, project.godot, Node2D, Node3D, scene tree, 造轮子, 最佳实践.
---

# 先用内置

Godot 的节点、资源和编辑器已经覆盖了大部分游戏功能。自己写之前先确认三件事：版本、内置方案、验证方式。细节去对应的细分 skill。

## 第一步 读项目

```
grep -E 'config/features|run/main_scene|stretch|renderer|physics_engine' project.godot
ls *.csproj *.sln 2>/dev/null
```

- `config/features` 里的版本号决定能用哪些 API。本套 skill 以 4.7.2 为准，标了 `4.5+` 之类的要对照项目版本
- 有 `.csproj` 是 C# 工程，改完先 `dotnet build`
- `rendering/renderer/rendering_method` 决定能用哪些渲染特性，Compatibility 下没有 SDFGI VoxelGI 体积雾

## 第二步 查内置

| 想做 | 用这个 | 去哪个 skill |
| --- | --- | --- |
| 节点树 组件 引用 状态机 | PackedScene、`@export` 节点引用、`%UniqueName`、信号、分组 | godot-scene-architecture |
| 配置数据 角色数值 关卡定义 | 自定义 `Resource` + `.tres` | godot-resources-data |
| 异步加载 加载界面 | `ResourceLoader.load_threaded_request` | godot-resources-data |
| 存档 设置 | `ConfigFile`、`FileAccess`、`user://` | godot-resources-data |
| 位移 渐变 一次性过渡 | `Tween` | godot-animation |
| 关键帧动画 角色动画状态 | `AnimationPlayer`、`AnimationTree` | godot-animation |
| 曲线 渐变色数据 | `Curve`、`Gradient` | godot-animation |
| 2D 移动 碰撞 | `CharacterBody2D.move_and_slide`、碰撞层 | godot-2d |
| 2D 地图 | `TileMapLayer` | godot-2d |
| 相机跟随 边界 平滑 震屏 | `Camera2D` 的 limit 和 smoothing、`offset` + `FastNoiseLite` | godot-2d |
| 视差背景 | `Parallax2D` | godot-2d |
| 是否在屏幕内 | `VisibleOnScreenNotifier2D`/`3D` | godot-2d godot-performance |
| 3D 角色 光照 GI 导入 | `CharacterBody3D`、`WorldEnvironment`、glTF 导入 | godot-3d |
| 2D 角色放进 3D 场景 | `Sprite3D` billboard、`SubViewport` | godot-2d-in-3d |
| HUD 菜单 布局 | Container + anchors + 项目级 `Theme` | godot-ui |
| 血条 | `ProgressBar`、`TextureProgressBar` | godot-ui |
| 多语言 | `tr()`、翻译 CSV/PO | godot-ui |
| 按键 手柄 改键 | InputMap 动作、`Input.get_vector` | godot-input |
| 音量分组 随机音效 动态音乐 | Audio bus、`AudioStreamRandomizer`、`AudioStreamInteractive` | godot-audio |
| 粒子 后处理 辉光 | `GPUParticles2D`/`3D`、`Environment.glow_enabled`、shader | godot-shaders-vfx |
| 编辑数据的工具 | `@tool`、`EditorPlugin`、Inspector 编辑 Resource | godot-editor-tooling |
| 大量同类物体 线程 卡顿 | `MultiMeshInstance3D`、`WorkerThreadPool`、Profiler | godot-performance |
| 改完自己验证 | `godot --headless` 加载与冒烟场景 | godot-headless-testing |
| GDScript 写法 | 静态类型 信号 await | godot-gdscript |
| C# 写法 | 源码生成器 `StringName` 缓存 生命周期 | godot-csharp |

表里没有的需求，先在类参考里搜关键词：

```
grep -ril '<关键词>' <godot源码>/doc/classes | head
```

或者打开 `https://docs.godotengine.org/en/stable/classes/class_<小写类名>.html`。

## 第三步 验证

写完至少做到：

- GDScript：`godot --headless --path . --import` 后无 `SCRIPT ERROR` 和 `Parse Error`
- C#：`dotnet build` 无错误
- 改到运行时行为：写一个冒烟场景无头跑几帧并断言，见 godot-headless-testing

不确定某个方法是否存在时，不要猜，查：

```
godot --headless --doctool /tmp/godot-doc
grep -l 'name="move_and_slide"' /tmp/godot-doc/doc/classes/*.xml
```

## 什么时候可以自己写

内置方案不满足硬约束时才自研，并在代码里留一条注释写明约束：

- 锁步联机或回放要逐帧复现：内置物理和 `Tween` 不保证确定性
- 要按任意帧 seek 重算表现：`Tween` 不能 seek，`AnimationPlayer.seek` 可以，先试它
- 引擎没有对应节点的第三方格式：用 `RenderingServer` 直接画，自己管 RID 释放
- profiler 证明内置节点是瓶颈：大量子弹改用 `PhysicsServer2D` 和 `RenderingServer`

## 陷阱

- 网上大量教程是 Godot 3，`KinematicBody2D`、`yield`、`export var`、`onready var`、`TileMap` 都是旧写法
- `TileMap`、`ParallaxBackground`、`ParallaxLayer` 在 4.7 已弃用，新代码用 `TileMapLayer`、`Parallax2D`
- 代码里 `new` 一整棵节点树会让场景在编辑器里不可见不可调，能做成 `.tscn` 的就做成 `.tscn`
- 静态字段持有 `Texture2D`、`Material` 等引擎对象，会碰到退出顺序和 C# 热重载问题，`ResourceLoader` 自带缓存
