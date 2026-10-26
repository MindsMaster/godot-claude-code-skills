---
name: godot-builtin-first
description: 在 Godot 4 项目里动手写任何功能之前先用，看到 project.godot .tscn .gd，或要自己写相机 缓动 状态机 UI 布局 JSON 加载 输入映射 音频池 存档 场景切换 编辑器工具时。先查引擎有没有现成的节点 资源 项目设置，再指向细分 skill。Use before implementing any feature in a Godot 4 project, GDScript or C#.
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
- `rendering/renderer/rendering_method` 决定能用哪些渲染特性，没写这一项就是默认的 Forward+。SDFGI VoxelGI 体积雾只有 Forward+ 有，Mobile 和 Compatibility 都没有

## 第二步 查内置

| 想做 | 用这个 | 去哪个 skill |
| --- | --- | --- |
| 节点树 组件 引用 状态机 | PackedScene、`@export` 节点引用、`%UniqueName`、信号、分组 | godot-scene-architecture |
| 全局状态 跨场景数据 | autoload 只放真全局状态，其余用信号和 `Resource` | godot-scene-architecture godot-resources-data |
| 暂停菜单 场景切换 | `SceneTree.paused` 加 `Node.process_mode`、`change_scene_to_file`、`change_scene_to_packed` | godot-scene-architecture |
| 配置数据 角色数值 关卡定义 | 自定义 `Resource` + `.tres` | godot-resources-data |
| 异步加载 加载界面 | `ResourceLoader.load_threaded_request` | godot-resources-data |
| 存档 | JSON 加 `FileAccess` 写到 `user://`，不 `load()` 玩家可写的 `.tres` | godot-resources-data |
| 设置 | `ConfigFile` 写到 `user://` | godot-resources-data |
| 曲线 渐变色 路径数据 | `Curve`、`Gradient`、`Curve2D`、`Curve3D`，给 shader 用 `CurveTexture`、`GradientTexture1D` | godot-resources-data godot-animation |
| 位移 渐变 一次性过渡 | `Tween` | godot-animation |
| 关键帧动画 角色动画状态 | `AnimationPlayer`、`AnimationTree` | godot-animation |
| 逐帧精灵 | `AnimatedSprite2D` 加 `SpriteFrames` | godot-animation |
| 2D 移动 碰撞 | `CharacterBody2D.move_and_slide`、碰撞层 | godot-2d |
| 拾取 伤害区 触发区 | `Area2D`/`Area3D` 加信号 | godot-2d godot-3d |
| 2D 地图 | `TileMapLayer` | godot-2d |
| 相机跟随 边界 平滑 震屏 | `Camera2D` 的 limit 和 smoothing、`offset` + `FastNoiseLite` | godot-2d |
| 视差背景 | `Parallax2D` | godot-2d |
| 2D 光照 阴影 压暗 | `PointLight2D`、`LightOccluder2D`、`CanvasModulate` | godot-2d |
| 是否在屏幕内 离屏暂停 | `VisibleOnScreenNotifier2D`/`3D`、`VisibleOnScreenEnabler2D`/`3D` | godot-2d godot-3d godot-performance |
| 2D 寻路 | `NavigationRegion2D` 加 `NavigationAgent2D`，格子地图用 `AStarGrid2D` | godot-2d |
| 3D 寻路 避让 | `NavigationRegion3D` 加 `NavigationAgent3D` | godot-3d |
| 3D 角色 光照 GI 导入 | `CharacterBody3D`、`WorldEnvironment`、glTF 导入 | godot-3d |
| 第三人称相机不穿墙 | `SpringArm3D` | godot-3d |
| 3D 射线 范围查询 | `RayCast3D`、`ShapeCast3D`、`PhysicsDirectSpaceState3D.intersect_ray` | godot-3d |
| 头部看向 IK 尾巴摆动 | `LookAtModifier3D`、`SpringBoneSimulator3D`，腿臂 IK 用 `TwoBoneIK3D` 4.6+，都是骨骼修改器 | godot-3d |
| 灰盒关卡 网格拼装 LOD 遮挡剔除 | CSG、`GridMap`、`OccluderInstance3D`、`visibility_range_end` | godot-3d |
| 2D 角色放进 3D 场景 | `Sprite3D` billboard、`SubViewport` | godot-2d-in-3d |
| HD-2D 后处理 景深 雾 | `WorldEnvironment` 的 `Environment` 加 `CameraAttributesPractical` | godot-2d-in-3d godot-3d |
| HUD 菜单 布局 | Container + anchors + 项目级 `Theme` | godot-ui |
| 血条 | `ProgressBar`、`TextureProgressBar` | godot-ui |
| 打字机效果 拖放 悬浮提示 | `RichTextLabel.visible_ratio`、`Control._get_drag_data`、`tooltip_text` | godot-ui |
| 多语言 | `tr()`、翻译 CSV/PO、`TranslationServer` | godot-ui |
| 按键 手柄 改键 | InputMap 动作、`Input.get_vector` | godot-input |
| 音量分组 随机音效 动态音乐 | Audio bus、`AudioStreamRandomizer`、`AudioStreamInteractive` | godot-audio |
| 粒子 | `GPUParticles2D`/`3D` 加 `ParticleProcessMaterial` | godot-shaders-vfx |
| 辉光 雾 色调映射 | `Environment`，2D 另需 `rendering/viewport/hdr_2d` | godot-shaders-vfx godot-2d |
| 描边 溶解 闪白 | 先看 `StandardMaterial3D`、`CanvasItemMaterial` 的属性，再写 shader | godot-shaders-vfx |
| 编辑数据的工具 | `@tool`、`EditorPlugin`、Inspector 编辑 Resource | godot-editor-tooling |
| 大量同类物体 线程 卡顿 | 管理器统一驱动、`MultiMeshInstance2D`/`3D`、`WorkerThreadPool` 分块、Profiler，不降画面与数量 | godot-performance |
| 延时 周期 数值靠近目标 | `Timer`、`create_timer`、`move_toward`、`lerp` | godot-gdscript |
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

- GDScript：新增 `class_name` 或资源后先 `godot --headless --path . --import`，再对每个改动的脚本 `godot --headless --path . --check-only -s x.gd`
- C#：`dotnet build` 无错误
- 改到运行时行为：写一个冒烟场景无头跑几帧并断言，见 godot-headless-testing

判失败不能只看退出码。`--import` 打开工程后退出码恒为 0，导入错误和脚本语法错误都一样，运行时 `SCRIPT ERROR` 和 `--quit-after` 到点也是 0。每条命令的输出都要 grep `SCRIPT ERROR|Parse Error|^ERROR:`，有就算失败。现成的 `gdrun` 函数和退出码表见 godot-headless-testing。

不确定某个方法是否存在时，不要猜，查：

```
mkdir -p /tmp/godot-doc
godot --headless --doctool /tmp/godot-doc
grep -l 'name="move_and_slide"' /tmp/godot-doc/doc/classes/*.xml
```

导出的 XML 说明文字是空的，只能确认名字和签名。要看行为说明去类参考网页，或者在脚本里用 `ClassDB.class_has_method`。

## 什么时候可以自己写

内置方案不满足硬约束时才自研，并在代码里留一条注释写明约束：

- 锁步联机或回放要逐帧复现：内置物理不保证确定性，官方物理介绍页明确写了无论哪个物理引擎都一样。模拟用自己的定点数和计时，表现层再用内置节点
- 要按任意帧 seek 重算表现：`Tween` 没有 seek，`custom_step` 只能向前推，`AnimationPlayer.seek` 可以跳到任意秒，先试它
- profiler 证明内置节点是瓶颈：大量子弹改用 `PhysicsServer2D` 和 `RenderingServer`，自己管 RID 释放，先试 `MultiMesh` 和对象池，见 godot-performance

## 陷阱

- 网上大量教程是 Godot 3，`KinematicBody2D`、`yield`、`export var`、`onready var`、`instance()` 都是旧写法
- `TileMap`、`ParallaxBackground`、`ParallaxLayer` 在 4.7 已弃用，新代码用 `TileMapLayer`、`Parallax2D`
- 代码里 `new` 一整棵节点树会让场景在编辑器里不可见不可调，能做成 `.tscn` 的就做成 `.tscn`
- 静态字段或字典缓存 `Texture2D`、`Material` 会持有强引用，资源不随引用归零释放，而且 `ResourceLoader` 已经按路径缓存
