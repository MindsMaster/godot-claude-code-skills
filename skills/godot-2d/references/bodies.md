# 单向平台与刚体

单向平台、下穿平台、角色推动刚体、直接改刚体状态。

## 单向平台

- 平台的 `CollisionShape2D` 勾 `one_way_collision`，从下穿过，从上站住
- 形状在 `Area2D` 下时该属性无效
- 高速物体漏过时加大 `one_way_collision_margin`，默认 1 像素
- `one_way_collision_direction` 改单向朝向 4.7+

## 下穿平台

- 平台放独立 layer
- 按下键时对角色 `set_collision_mask_value(层号, false)`
- 落到平台下方后恢复该位

## 推动刚体

- `CharacterBody2D` 撞上 `RigidBody2D` 不推动它
- `move_and_slide` 后遍历 `get_slide_collision(i)`
- 每物理帧对 `get_collider()` 得到的刚体调 `apply_central_force`
- 力的方向取碰撞法线的反方向
- `apply_central_impulse` 与时间无关，每帧调随帧率变化，只用于一次性冲击

## 改刚体状态

- `RigidBody2D` 的位置和速度归物理模拟
- 直接改 `position` 或 `linear_velocity` 行为不可预测
- 要改放进 `_integrate_forces(state)`
