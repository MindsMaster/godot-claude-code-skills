---
type: llm
criteria: 下面只有 main.tscn TileSet 有一个 terrain set mode 与 peering bit 对得上 mode 为 MATCH_SIDES 时只写 side 位 MATCH_CORNERS 时只写 corner 位 MATCH_CORNERS_AND_SIDES 时 side 和 corner 都写 每块瓦片的 bit 只写朝向图集内部相邻瓦片的方向 3x3 九块的 bit 组合各不相同 只按结果判 不因为没用某个特定 API 或写法判失败
focus: { source: file, path: main.tscn }
---
