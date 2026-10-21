---
type: llm
criteria: 闪白只影响被打的那个敌人 共用同一份材质 shader 里 flash 改为 instance uniform 用 SetInstanceShaderParameter 或 Tween 驱动 instance_shader_parameters/flash 没有 Material.Duplicate 或 ResourceLocalToScene 给每个敌人复制材质 参数名或属性路径缓存为 static readonly StringName 或 NodePath 字段 没有每次受击用字符串插值拼路径 没有每帧 new StringName 或 new NodePath 受击重复触发时 不会叠出多个互相打架的 Tween 或先 Kill 旧的 没有手写 Timer 加计时变量自己插值
focus: trace
---
