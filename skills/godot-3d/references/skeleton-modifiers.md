# 骨骼修改器

4.3 起 `SkeletonModifier3D` 是骨骼后处理的统一基类。作为 `Skeleton3D` 的子节点，在 `AnimationPlayer` `AnimationTree` 播放之后运行，多个修改器按子节点顺序依次处理。

## 版本表

| 类 | 版本 | 用途 |
|---|---|---|
| `SkeletonModifier3D` | 4.3+ | 基类 自写 IK 约束 骨骼物理时继承 |
| `PhysicalBoneSimulator3D` | 4.3+ | 布娃娃 配合 `PhysicalBone3D` |
| `LookAtModifier3D` | 4.4+ | 骨骼看向目标 带角度限制与缓动 |
| `SpringBoneSimulator3D` | 4.4+ | 头发 布料 尾巴的惯性摆动 链式 会回到原姿势 |
| `SpringBoneCollision3D` 及 Sphere Capsule Plane 子类 | 4.4+ | 弹簧骨骼的碰撞体 与物理服务器无关 不是 `SpringBoneSimulator3D` 的子节点则无效 |
| `RetargetModifier3D` | 4.4+ | 把父骨架姿势传给不同静止姿势的子骨架 |
| `BoneConstraint3D` | 4.5+ | 约束基类 |
| `CopyTransformModifier3D` | 4.5+ | 把参考骨骼的变换复制到目标骨骼 |
| `ConvertTransformModifier3D` | 4.5+ | 按轴重映射参考骨骼的变换 |
| `AimModifier3D` | 4.5+ | `LookAtModifier3D` 的简化版 无角度限制与时间插值 |
| `ModifierBoneTarget3D` | 4.5+ | 像 `BoneAttachment3D` 一样跟随骨骼 但参与修改器顺序 适合当别的修改器的目标 |
| `IKModifier3D` `ChainIK3D` `IterateIK3D` | 4.6+ | IK 基类 |
| `TwoBoneIK3D` | 4.6+ | 两段骨骼解析解 需要极向量 手臂 腿 |
| `FABRIK3D` | 4.6+ | 位置法 适合无约束的简单链 目标靠近根部时出现之字形抖动 |
| `CCDIK3D` | 4.6+ | 旋转法 适合有限制的链 目标靠近根部时可能关节翻转与振荡 |
| `JacobianIK3D` | 4.6+ | 同时算所有关节 平滑 适合生物动作 收敛慢 |
| `SplineIK3D` | 4.6+ | 让骨骼沿 `Path3D` 排列 |
| `LimitAngularVelocityModifier3D` | 4.6+ | 限制骨骼旋转角速度 压住抖动与突变 |
| `BoneTwistDisperser3D` | 4.6+ | 把末端骨骼的扭转分摊到父骨骼 配合 Copy 与 IK |
| `SkeletonIK3D` | 4.3 到 4.7 的类参考都标为已弃用 | 新项目用 4.6+ 的 IK 系列 |

低于 4.6 的项目没有 IK 系列，自己继承 `SkeletonModifier3D` 实现，或用 `SkeletonIK3D`。

## 通用属性

- `active` 开关，`influence` 0 到 1 的权重，用 `Tween` 做淡入淡出
- 自写修改器重写 `_process_modification_with_delta(delta)`，4.5+。老的 `_process_modification()` 已弃用。不要在里面自己乘 `influence`，`Skeleton3D` 会统一应用
- `Skeleton3D.modifier_callback_mode_process` 默认空闲帧更新，可选物理帧或手动，手动时用 `Skeleton3D.advance()` 4.5+
- 骨骼名与索引都可设，名字更稳
- 修改结果只在 `Skeleton3D.skeleton_updated` 或 `SkeletonModifier3D.modification_processed` 发出的那一刻读得到，其余时刻 `get_bone_global_pose()` 返回未修改的姿势。要读修改后的骨骼位置，在这两个信号的回调里读
- IK 与弹簧骨骼的每条链是一个索引项：先设 `setting_count`，再对每个索引调用 `set_root_bone_name(index, name)` 一类方法
- `IKModifier3D` 与 `SpringBoneSimulator3D` 的 `mutable_bone_axes` 默认 true，每帧从姿势取骨轴。设 false 只用静止姿势并缓存，略快但忽略之前对位置的改动

## 看向目标

```gdscript
extends Skeleton3D

func look_with_head(target: Node3D) -> void:
	var look: LookAtModifier3D = LookAtModifier3D.new()
	add_child(look)
	look.bone_name = "Head"
	look.target_node = look.get_path_to(target)
	look.forward_axis = SkeletonModifier3D.BONE_AXIS_PLUS_Z
	look.use_angle_limitation = true
	look.primary_limit_angle = deg_to_rad(70.0)
	look.duration = 0.2
```

- 同时给父骨与子骨加多个 `LookAtModifier3D` 时，父骨的节点要排在上面
- `forward_axis` 默认 `BONE_AXIS_PLUS_Z`，模型朝向不同要改
- `duration` 是时间插值的时长，在更换目标节点或角度限制造成轴翻转时触发，默认 0 即不插值
- 目标更换时想平滑，设 `duration`。想整体淡出，用 `influence`

## 两段 IK

```gdscript
extends Skeleton3D

func setup_leg_ik(foot_target: Node3D, knee_pole: Node3D) -> TwoBoneIK3D:
	var ik: TwoBoneIK3D = TwoBoneIK3D.new()
	add_child(ik)
	ik.setting_count = 1
	ik.set_root_bone_name(0, "UpperLeg_L")
	ik.set_middle_bone_name(0, "LowerLeg_L")
	ik.set_end_bone_name(0, "Foot_L")
	ik.set_target_node(0, ik.get_path_to(foot_target))
	ik.set_pole_node(0, ik.get_path_to(knee_pole))
	return ik
```

需要 4.6+。目标节点通常是脚下射线命中点的 `Marker3D`，每个物理帧移动它。中间有多根骨骼时，其旋转被忽略，按根到中间、中间到末端的直线当作虚拟骨骼。

## 弹簧骨骼

- 设置里给根骨与末骨，一条链一个设置，不支持分叉的 Y 形链
- 数值可用 `Curve` 沿链分布，或开 individual config 逐关节设 `set_joint_stiffness()` 等
- 碰撞：把 `SpringBoneCollisionSphere3D` 等放成修改器的子节点，设 `bone_name` 让它跟随骨骼。每条链用 `set_enable_all_child_collisions()` 切换全部子碰撞体生效或手动用 `set_collision_path()` 登记
- 不要缩放 `SpringBoneSimulator3D` 或其父骨架，缩放后行为不对
- 它会回到原姿势，与 `PhysicalBoneSimulator3D` 的自由物理不同

## 其他

- 路径 IK 要让路径跟随骨骼时，在 `SplineIK3D` 之前放 `ModifierBoneTarget3D`，把 `Path3D` 作为它的子节点
- 单纯把节点挂在骨骼上用 `BoneAttachment3D`。要在修改器链里被引用用 `ModifierBoneTarget3D` 4.5+
- 重定向动画（不同骨架共用动画）先看 `retargeting_3d_skeletons` 的 `BoneMap` 与导入面板，`RetargetModifier3D` 用于运行时

## 参考

- https://docs.godotengine.org/en/stable/classes/class_skeletonmodifier3d.html
- https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/retargeting_3d_skeletons.html
