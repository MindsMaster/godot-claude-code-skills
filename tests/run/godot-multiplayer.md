# godot-multiplayer

## SKILL.md `func host`

```gdscript
expect(node.host() == OK, "主机监听成功")
expect(node.multiplayer.is_server(), "主机侧 is_server 为真")
expect(node.multiplayer.get_unique_id() == 1, "服务器 peer id 固定是 1")
node.multiplayer.multiplayer_peer.close()
expect(node.join("127.0.0.1") == OK, "join 返回 OK")
var status := node.multiplayer.multiplayer_peer.get_connection_status()
expect(status == MultiplayerPeer.CONNECTION_CONNECTING, "返回 OK 时还在连接中")
node.multiplayer.multiplayer_peer.close()
node.multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
```

## SKILL.md `func request_open`

```gdscript
var player := Node3D.new()
node.add_child(player)
node.players[1] = player
player.position = Vector3(10.0, 0.0, 0.0)
node.request_open()
expect(not node.opened, "超出距离的请求被拒")
player.position = Vector3(1.0, 0.0, 0.0)
node.request_open()
expect(node.opened, "主机本人经 call_local 走到校验")
```

## SKILL.md `func _create_enemy`

```gdscript
var template := Node3D.new()
var scene := PackedScene.new()
scene.pack(template)
template.free()
node.enemy_scene = scene
var holder := Node3D.new()
node.add_child(holder)
node.spawn_path = node.get_path_to(holder)
var enemy: Node3D = node.spawn({"position": Vector3(1.0, 2.0, 3.0)})
expect(enemy.position == Vector3(1.0, 2.0, 3.0), "初始值写在 spawn_function 里")
expect(enemy.get_parent() == holder, "返回的节点由 Spawner 加进树")
```
