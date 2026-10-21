---
type: llm
criteria: 闪白只影响被打的那个敌人 共用同一份材质 shader 里 flash 改为 instance uniform 用 SetInstanceShaderParameter 或 Tween 驱动 instance_shader_parameters/flash 没有 Material.Duplicate 或 ResourceLocalToScene 给每个敌人复制材质 参数名或属性路径缓存为 static readonly StringName 或 NodePath 字段 没有每次受击用字符串插值拼路径 没有每帧 new StringName 或 new NodePath 恢复过程用 CreateTween 且重复触发时先 Kill 旧的 或者用只在闪白期间 SetProcess(true) 的计时衰减 没有常开 _Process 每帧轮询 没有另建 Timer 节点 flash.gdshader 的 fragment 以 COLOR 输入为底色混合闪白 不用 texture(TEXTURE, UV) 重新采样丢掉 modulate 和顶点色 半透明的敌人闪白时 alpha 不被还原为纹理原值 轨迹中间被省略的写入看不到时 以能看到的写入内容和最终回复对做法的描述为依据 看不到不等于违规
focus: trace
---
