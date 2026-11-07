---
type: llm
criteria: 下面只有 player.gd TileSet 的 terrain 配置由别的评分项检查 这里假定配置与图集一致 只判挖地逻辑 按 ui_down 挖掉玩家脚下一格 挖后周围瓦片的边缘和转角自动变成与地形笔刷涂出的一致 只 erase_cell 或 set_cell 擦掉而邻格不变 判失败 erase_cell 之后把邻格以地面 terrain 传给 set_cells_terrain_connect 也判失败 因为引擎不会因此改变邻格瓦片 只按结果判 不因为没用某个特定 API 或写法判失败
focus: { source: file, path: player.gd }
---
