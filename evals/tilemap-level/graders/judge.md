---
type: llm
criteria: 地图用 TileMapLayer 节点加 TileSet 资源 TileSet 配置了 physics layer 并给瓦片画了碰撞多边形 没有使用已弃用的 TileMap 节点 没有手写脚本逐格实例化 StaticBody2D 或 CollisionShape2D 来造地面 没有用 Polygon2D 或 _draw 自绘关卡 预置的地面和浮台格子真的能被引擎读出 如果手写了 tile_map_data 字节 其格式头为 0 且每格 12 字节 或者用 set_cell 加保存场景的脚本生成 或者实际运行 godot 确认读出了格子 回复如实说明预置格子是否经引擎验证
focus: trace
---
