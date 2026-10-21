---
type: llm
criteria: 角色用 Sprite3D 或 AnimatedSprite3D 节点 开启 billboard 模式而不是在脚本里每帧 look_at 相机 billboard 用 BILLBOARD_FIXED_Y 即 billboard = 2 保持竖直 而不是随相机俯仰后仰的 BILLBOARD_ENABLED 精灵原点放在脚底 通过 offset 或节点位置让脚贴地 texture_filter 设为 nearest 保持像素清晰 投影用 alpha_cut 为 DISCARD 或 OPAQUE_PREPASS 的精灵 可以是角色精灵自己投影 也可以是同贴图同 alpha_cut 的 cast_shadow 为 SHADOWS_ONLY 的副本精灵 没有用方块 圆片等网格冒充影子 没有手写 QuadMesh 加材质来冒充角色 没有为朝向或阴影手写 shader 轨迹中间被省略的写入看不到时 以能看到的写入内容和最终回复对做法的描述为依据 看不到不等于违规
focus: trace
---
