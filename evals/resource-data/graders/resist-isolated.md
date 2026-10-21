---
type: llm
criteria: 元素抗性每项做成带 @export 字段的子资源或等价可在 Inspector 逐项编辑的结构 enemy.gd 的 apply_corrosion 只改当前敌人 如果抗性是子资源数组并且腐蚀时直接改其中每项的比例 那么当前敌人持有的数据必须先用 duplicate(true) 或 duplicate_deep 深拷贝 或者每个子资源也设了 resource_local_to_scene 只对外层资源 duplicate() 或只给外层勾 resource_local_to_scene 再去改数组里子资源的比例 会改到所有同种敌人共用的子资源 判不通过 把抗性比例拷进节点自己的变量或字典里再减半也算通过 轨迹中间被省略的写入看不到时 以能看到的写入内容和最终回复对做法的描述为依据 看不到不等于违规
focus: trace
---
