---
type: llm
criteria: 下面只有 flash.gdshader 脚本由别的评分项检查 这里只判着色器 节点 modulate 的 alpha 为 0.4 时 敌人平时半透明 闪白期间也保持半透明 canvas_item 的 fragment 里 COLOR 默认已是纹理色乘以 modulate 和顶点色 用 texture(TEXTURE, UV) 重新采样作底色又没乘回 COLOR 时 modulate 丢失 判失败 只按结果判 不因为没用某个特定 API 或写法判失败
focus: { source: file, path: flash.gdshader }
---
