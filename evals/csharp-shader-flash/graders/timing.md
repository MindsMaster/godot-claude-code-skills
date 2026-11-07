---
type: llm
criteria: 下面只有 Enemy.cs 着色器和材质由别的评分项检查 这里假定 flash 实例参数为 1 时敌人变白 为 0 时是原色 只判 Enemy.cs 的逻辑 受伤后变白 约 0.1 秒内恢复原色 每帧都调用 TakeDamage 时也能正常工作 期间持续白色或反复闪烁都算对 停止调用后约 0.1 秒内恢复 不会停止后仍卡在白色 不会抛异常 能通过 C# 编译 只按结果判 不因为没用某个特定 API 或写法判失败
focus: { source: file, path: Enemy.cs }
---
