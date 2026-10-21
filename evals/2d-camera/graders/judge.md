---
type: llm
criteria: 相机是 Camera2D 节点 用 limit_left limit_right limit_top limit_bottom 限制边界 用 position_smoothing_enabled 平滑 没有在 _process 里手写 lerp 跟随或手算边界 clamp 震屏改 Camera2D 的 offset 而不是移动相机 position 复活传送的代码处直接调用 Camera2D 的 reset_smoothing 让镜头立刻到位 而不是在相机脚本里每帧比较位移距离超过阈值来猜测是否传送 没有靠临时关闭平滑或手动改相机位置绕过 轨迹中间被省略的写入看不到时 以能看到的写入内容和最终回复对做法的描述为依据 看不到不等于违规
focus: trace
---
