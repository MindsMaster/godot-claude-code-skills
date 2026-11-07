---
type: llm
criteria: HUD 是单独场景 实例化进 main.tscn 通过导出变量拿到玩家节点 运行时这个引用不为空 用 @export 的 Node 类型变量时 .tscn 里该节点头必须带 node_paths=PackedStringArray 列出这个属性 否则运行时为 null 判失败 用 NodePath 类型导出再 get_node 也算对 只按结果判 不因为没用某个特定 API 或写法判失败 轨迹中间被省略的写入看不到时 以能看到的写入内容和最终回复的描述为依据 看不到不等于违规
focus: trace
---
