---
type: llm
criteria: 地图用 TileMapLayer 节点加 TileSet 资源 TileSet 配置了 physics layer 并给瓦片画了碰撞多边形 没有使用已弃用的 TileMap 节点 没有手写脚本逐格实例化 StaticBody2D 或 CollisionShape2D 来造地面 没有用 Polygon2D 或 _draw 自绘关卡 预置的地面和浮台格子真的能被引擎读出 如果手写了 tile_map_data 字节 其格式头为 0 且每格 12 字节 或者用 set_cell 加保存场景的脚本生成 或者实际运行 godot 确认读出了格子 回复如实说明预置格子是否经引擎验证 TileSet 建了一个 terrain set 且 mode 与 peering bit 对得上 mode 为 MATCH_SIDES 时只写 side 位 MATCH_CORNERS 时只写 corner 位 MATCH_CORNERS_AND_SIDES 时 side 和 corner 都写 每块瓦片的 bit 只写朝向图集内部相邻瓦片的方向 3x3 九块的 bit 各不相同 预置的地面和浮台格子按位置选边缘和转角瓦片 顶行用图集第一行 底行用第三行 最左最右列用左右边 内部用中间块 不是全铺同一块 挖地功能把被挖的格子本身以 terrain -1 传给 set_cells_terrain_connect 让引擎刷新邻格 只调用 erase_cell 或 set_cell 擦掉不通过 erase_cell 之后再把邻格以地面 terrain 传给 set_cells_terrain_connect 也不通过 因为引擎里邻格瓦片不会因此改变 轨迹中间被省略的写入看不到时 以能看到的写入内容和最终回复对做法的描述为依据 看不到不等于违规
focus: trace
---
