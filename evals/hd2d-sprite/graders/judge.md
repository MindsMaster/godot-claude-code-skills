---
type: llm
criteria: 角色用 Sprite3D 或 AnimatedSprite3D 节点 开启 billboard 模式而不是在脚本里每帧 look_at 相机 billboard 用 BILLBOARD_FIXED_Y 即 billboard = 2 保持竖直 而不是随相机俯仰后仰的 BILLBOARD_ENABLED 精灵原点放在脚底 通过 offset 或 centered 或节点位置让脚贴地 texture_filter 设为 nearest 保持像素清晰 设置 alpha_cut 为 DISCARD 或 OPAQUE_PREPASS 让阴影按角色轮廓 由角色精灵自己投影 没有另建一个不跟随朝向的阴影替身精灵或阴影网格 没有手写 QuadMesh 加材质来冒充 没有为朝向或阴影手写 shader
focus: trace
---
