---
type: llm
criteria: 新建了带 class_name 的自定义 Resource 脚本 字段用 @export 标注 其中贴图是 Texture2D 类型 为现有的几种敌人各提供 .tres 资源文件 enemy.gd 改为使用该 Resource 而不是继续手写 JSON.parse_string 解析 也接受导入期转换方案 即用 EditorImportPlugin 或 tool 脚本把 json 转成 .tres 且策划改的是源数据 不接受仅仅保留 JSON 并加更多解析代码
focus: trace
---
