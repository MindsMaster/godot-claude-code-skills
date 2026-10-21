---
type: llm
criteria: C# 代码改的是 flash 着色器参数 用 CreateTween 配 TweenMethod 或 TweenProperty 驱动 或者用 static readonly StringName 缓存参数名 再设置参数 不在 _Process 里每帧传 flash 字符串字面量 也没有每帧 new StringName 或 new NodePath 受击重复触发时 不会叠出多个互相打架的 Tween 或先 Kill 旧的 没有手写 Timer 加计时变量自己插值
focus: trace
---
