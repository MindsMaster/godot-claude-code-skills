# 阴影细节

Sprite3D 阴影的实测数据、背光与 `double_sided`、相机转动时的稳定影子。

## 背光与 double_sided

- `double_sided` 默认 true
- 设为 false 后，光从精灵背面来时不投影
- 实测同一光照下双面投 320 像素，单面 0 像素
- billboard 精灵正面朝相机，背光主光会让单面精灵的阴影消失
- 要投影就保持双面

## 相机转动时的稳定影子

billboard 精灵的影子随相机转向变形，光从相机侧面来时变窄。实测 4.7.2 Compatibility，同一精灵同一光照：

| 光与相机夹角 | billboard 影子像素 | 副本方案影子像素 |
|---|---|---|
| 顺光 | 2016 | 2016 |
| 45 度 | 1383 | 1991 |
| 侧光 | 0 | 1978 |

副本方案：

1. 可见精灵 `cast_shadow` 设 `SHADOW_CASTING_SETTING_OFF`
2. 加一个同贴图、同 `alpha_cut`、同 `offset`、不开 billboard 的 Sprite3D
3. 副本 `cast_shadow` 设 `SHADOW_CASTING_SETTING_SHADOWS_ONLY`
4. 副本正面朝主光的水平方向

- 副本方案各角度的差别来自像素取样
