# 骨骼修改器

`SkeletonModifier3D` 系列的版本表、通用属性、看向目标、两段 IK、弹簧骨骼。

## 版本表

`SkeletonModifier3D` 4.3+ 是骨骼后处理的统一基类，作为 `Skeleton3D` 的子节点在动画播放之后运行，多个修改器按子节点顺序处理。

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

- 低于 4.6 的项目没有 IK 系列，继承 `SkeletonModifier3D` 自己实现，或用 `SkeletonIK3D`

## 通用属性

| 属性或方法 | 说明 |
|---|---|
| `active` | 开关 |
| `influence` | 0 到 1 的权重，用 `Tween` 做淡入淡出 |
| `_process_modification_with_delta(delta)` | 自写修改器重写它，4.5+，旧 `_process_modification()` 已弃用 |
| `Skeleton3D.modifier_callback_mode_process` | 默认空闲帧，可选物理帧或手动 |
| `Skeleton3D.advance()` | 手动模式下推进，4.5+ |
| `setting_count` | IK 与弹簧骨骼每条链一个索引，先设数量再按索引设骨骼 |
| `mutable_bone_axes` | 默认 true 每帧从姿势取骨轴，false 只用静止姿势，略快 |

- 自写修改器里不乘 `influence`，`Skeleton3D` 统一应用
- 骨骼名与索引都可设，名字更稳
- 修改结果只在 `Skeleton3D.skeleton_updated` 或 `SkeletonModifier3D.modification_processed` 时读得到
- 其余时刻 `get_bone_global_pose()` 返回未修改的姿势

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

```csharp
public partial class HeadLook : Skeleton3D
{
    public void LookWithHead(Node3D target)
    {
        var look = new LookAtModifier3D();
        AddChild(look);
        look.BoneName = "Head";
        look.TargetNode = look.GetPathTo(target);
        look.ForwardAxis = SkeletonModifier3D.BoneAxis.PlusZ;
        look.UseAngleLimitation = true;
        look.PrimaryLimitAngle = Mathf.DegToRad(70.0f);
        look.Duration = 0.2f;
    }
}
```

- 父骨与子骨各加 `LookAtModifier3D` 时，父骨的节点排在上面
- `forward_axis` 默认 `BONE_AXIS_PLUS_Z`，模型朝向不同要改
- `duration` 默认 0，更换目标或角度限制翻轴时按它插值
- 整体淡出用 `influence`

## 两段 IK

4.6+。目标节点通常是脚下射线命中点的 `Marker3D`，每个物理帧移动它。

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

```csharp
public partial class LegIk : Skeleton3D
{
    public TwoBoneIK3D SetupLegIk(Node3D footTarget, Node3D kneePole)
    {
        var ik = new TwoBoneIK3D();
        AddChild(ik);
        ik.SettingCount = 1;
        ik.SetRootBoneName(0, "UpperLeg_L");
        ik.SetMiddleBoneName(0, "LowerLeg_L");
        ik.SetEndBoneName(0, "Foot_L");
        ik.SetTargetNode(0, ik.GetPathTo(footTarget));
        ik.SetPoleNode(0, ik.GetPathTo(kneePole));
        return ik;
    }
}
```

- 中间有多根骨骼时其旋转被忽略
- 按根到中间、中间到末端的直线当作虚拟骨骼

## 弹簧骨骼

- 一条链一个设置，给根骨与末骨，不支持 Y 形分叉链
- 数值可用 `Curve` 沿链分布，或开 individual config 逐关节设 `set_joint_stiffness()` 等
- 碰撞：`SpringBoneCollisionSphere3D` 等放成修改器的子节点，设 `bone_name` 跟随骨骼
- 每条链用 `set_enable_all_child_collisions()` 切换全部子碰撞体
- 或用 `set_collision_path()` 手动登记
- 不缩放 `SpringBoneSimulator3D` 或其父骨架
- 它会回到原姿势，与 `PhysicalBoneSimulator3D` 的自由物理不同

## 其他

- 路径跟随骨骼：`SplineIK3D` 之前放 `ModifierBoneTarget3D`，`Path3D` 作为它的子节点
- 节点挂在骨骼上用 `BoneAttachment3D`
- 要在修改器链里被引用用 `ModifierBoneTarget3D` 4.5+
- 不同骨架共用动画先看导入面板的 `BoneMap` 重定向
- `RetargetModifier3D` 用于运行时重定向
