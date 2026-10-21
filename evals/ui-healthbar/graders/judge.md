---
type: llm
criteria: 血条用 ProgressBar 或 TextureProgressBar 通过 value 和 max_value 驱动 没有用 ColorRect 改 size 当血条 布局用 Container 或 anchors 和 offsets 而不是写死 position 数值 字体通过项目级 Theme 资源统一 在 project.godot 的 gui/theme/custom 设置或根 Control 的 theme 属性 而不是每个 Label 单独 add_theme_font_override 信号连到 HUD 更新数值 HUD 脚本用 @export 的 Node 类型变量引用玩家时 .tscn 里该节点头带 node_paths=PackedStringArray 列出这个属性 否则运行时为 null 如果改用 NodePath 类型导出加 get_node 或 %UniqueName 也算对 轨迹中间被省略的写入看不到时 以能看到的写入内容和最终回复对做法的描述为依据 看不到不等于违规
focus: trace
---
