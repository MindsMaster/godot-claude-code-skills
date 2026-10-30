---
name: godot-multiplayer
description: 写联机 多人 主机权威 同步 后加入 断线重连时用。ENetMultiplayerPeer 建连、@rpc 与 multiplayer_authority、MultiplayerSpawner MultiplayerSynchronizer 与可见性、传输模式与通道、NAT 与端口转发、ENetConnection 自建传输、预测与校正、两进程无头验收。客户端看不到主机的效果、后加入缺状态、奖励只发给主机时也用。multiplayer rpc replication late join netcode client prediction.
---

# Godot 联机

用高层多人 API 或 `ENetConnection` 搭主机权威的联机，并验证客户端看到的和主机一致。不管单机物理确定性和回放，见 `godot-animation`。两进程测试的通用写法见 `godot-headless-testing`。

## 先查内置

| 需求 | 用这个 | 别自己写 |
|---|---|---|
| 建连 | `ENetMultiplayerPeer.create_server` `ENetMultiplayerPeer.create_client` | 直接开 `PacketPeerUDP` 拼可靠重传 |
| 远程调用 | `@rpc`，C# 用 `[Rpc]` | 手写消息类型分发 |
| 运行时生成实体 | `MultiplayerSpawner` | 每种实体各写一个生成 RPC |
| 持续同步属性 | `MultiplayerSynchronizer` | 每帧发一条位置 RPC |
| 按玩家裁剪同步 | `MultiplayerSynchronizer.set_visibility_for` `MultiplayerSynchronizer.add_visibility_filter` | 在 RPC 里逐个 `rpc_id` 过滤 |
| 入房鉴权 | `SceneMultiplayer.auth_callback` | 连上后再发第一条 RPC 校验 |
| 接自定义传输 | `MultiplayerPeerExtension` | 改写上层调用 |
| 点对点 穿透 NAT | `WebRTCMultiplayerPeer` 加 `WebRTCPeerConnection.initialize` 的 `iceServers` | 自己打洞 |

引擎不提供：大厅、好友邀请、客户端预测、校正重放、按接收者的流量预算。

ENet 不做 NAT 穿透，公网玩家连家用主机要转发 UDP 端口。免转发有两条路：`WebRTCMultiplayerPeer` 配 STUN 和 TURN 服务器，要自己搭信令服务，原生平台还要装 webrtc-native 扩展；或者接第三方平台的传输。

## 建连

```gdscript
extends Node

const PORT := 7000
const MAX_CLIENTS := 3

func host() -> Error:
	var peer := ENetMultiplayerPeer.new()
	var error := peer.create_server(PORT, MAX_CLIENTS)
	if error != OK:
		return error
	multiplayer.multiplayer_peer = peer
	return OK

func join(address: String) -> Error:
	var peer := ENetMultiplayerPeer.new()
	var error := peer.create_client(address, PORT)
	if error != OK:
		return error
	multiplayer.multiplayer_peer = peer
	return OK
```

`create_client` 返回 `OK` 只代表开始连接，连上要等 `MultiplayerAPI.connected_to_server`，失败看 `MultiplayerAPI.connection_failed`。服务器 peer id 固定是 1。

## 客户端请求走主机校验

客户端只发意图，结果由主机算。

```gdscript
extends Node

const OPEN_RANGE := 3.0

var players: Dictionary[int, Node3D] = {}
var chest_position := Vector3.ZERO
var opened := false

func request_open() -> void:
	open_chest.rpc_id(1)

@rpc("any_peer", "call_local", "reliable")
func open_chest() -> void:
	if not multiplayer.is_server() or opened:
		return
	var player: Node3D = players.get(multiplayer.get_remote_sender_id())
	if player == null or player.global_position.distance_to(chest_position) > OPEN_RANGE:
		return
	opened = true
```

- 主机本人也是玩家时要 `call_local`，否则主机自己点了没反应
- 身份只取 `MultiplayerAPI.get_remote_sender_id`，不信参数里的玩家 id。它只在 RPC 同步执行期间有效，`await` 之后是 0，先存进局部变量
- 同一意图要能抗重复：扣费类请求带版本号或请求 id，否则连点两次按两次算

`@rpc` 默认 `authority` `call_remote` `reliable`，通道 0，C# 的 `[Rpc]` 同样默认可靠。高频数据要显式写传输模式，否则全走可靠。两端的 RPC 配置要一致，引擎按全部 RPC 的校验和比对。

## 传输模式

| 模式 | ENet 标志 | 用途 |
|---|---|---|
| `TRANSFER_MODE_RELIABLE` | RELIABLE | 请求 回执 生成 销毁 死亡 |
| `TRANSFER_MODE_UNRELIABLE_ORDERED` | UNRELIABLE_FRAGMENT | 位置快照，晚到的旧包丢弃 |
| `TRANSFER_MODE_UNRELIABLE` | UNSEQUENCED 加 UNRELIABLE_FRAGMENT | 可乱序的高频数据 |

- 不可靠和可靠走不同 ENet 通道，互相没有先后保证。可靠的生成包丢一次要等重传，后发的不可靠快照可能先到，接收方要容忍实体暂时不存在
- 通道号大于 0 时按该号建独立通道，慢消息不挡快消息
- 走不可靠的数据单包控制在 1364 字节内。默认 MTU 1392，减去 ENet 头 4 字节和分片头 24 字节

## 用 Spawner 和 Synchronizer 复制

```gdscript
extends MultiplayerSpawner

@export var enemy_scene: PackedScene

func _ready() -> void:
	spawn_function = _create_enemy

func _create_enemy(data: Dictionary) -> Node:
	var enemy: Node3D = enemy_scene.instantiate()
	enemy.position = data["position"]
	return enemy
```

主机调用 `MultiplayerSpawner.spawn`，`spawn_function` 在所有对端执行，返回未入树的节点。

- 自动生成只认 `spawn_path` 的直接子节点，场景要在可生成列表里，`add_child(node, true)` 的第二个参数要开，否则名字无效
- 用 `MultiplayerSpawner.spawn` 时初始值写在 `spawn_function` 里，所有端走同一份
- 同步的是属性，不支持 `Resource` 这类 `Object` 属性，也不能同步实例 id 和 RID
- 单个节点的同步状态超过 `SceneMultiplayer.max_sync_packet_size` 时不发送，只报错，默认 1350
- `MultiplayerSynchronizer.replication_interval` 默认 0，表示每个网络帧都同步，按需调大

## 后加入与重连

连上后 Spawner 生成的实体和 Synchronizer 状态会补发给新对端。下列内容不会补发，要自己进全量状态：

- 已发过的 RPC。预警、Boss 阶段、门的开关如果只靠一次性 RPC，后来的玩家看不到
- 场景里预置节点的变化。主机上销毁的预置物，后加入者本地场景里还在，碰撞也在
- 有存续时间的区域效果。只发一次开始事件时，存续期间进房的人看不到，但伤害还在结算

判断标准：这个状态在事件发生 10 秒后进房的人眼里应该是什么样。答案不是初始值，它就属于状态。逐项检查表见 `references/sync-checklist.md`。

## 表现默认不同步

AI 和玩法脚本只在权威端跑时，里面的动作、隐藏和节点生成都只有主机看得见，单机和主机验证全部通过。写法上分三层：

- 权威端决定发生了什么
- 复制层把结果变成状态或事件
- 每个端的表现层只读状态和事件

新增一个技能或交互时，同时写一条客户端断言。漏同步靠人眼在主机上看不出来。

## 自建传输

在 `ENetConnection` 上自己写协议时看 `references/custom-transport.md`。默认标志 0 的超长包会被改成可靠分片，这一条只有低层 API 会遇到。

## 预测与校正

引擎不提供，要自己写时看 `references/authoritative-movement.md`。校正消息要带全部影响位移的状态，这是最容易漏的一条。

## 陷阱

- `SceneTree.multiplayer_poll` 开启时轮询每个渲染帧执行一次，暂停也跑，RPC 按渲染帧到达，不按物理帧
- 自己轮询 `ENetConnection.service` 的节点要 `PROCESS_MODE_ALWAYS`，否则暂停时连接超时
- `MultiplayerPeer.close` 不触发 `MultiplayerPeer.peer_disconnected`，清理逻辑不能只挂这个信号
- 奖励 治疗 全队效果要遍历所有玩家。写成本地玩家时，单机和主机测试都通过
- 远端输入只存当前状态时，一次轮询内按下又松开的短按会丢，要做按下锁存
- 主机退出时客户端要回到干净状态。局内数据如果存在全局单例里，走主动离开和被断开两条路径都要清

## 验证

```bash
godot --headless --path . res://tests/net_smoke.tscn -- --host 27400
godot --headless --path . res://tests/net_smoke.tscn -- --join 127.0.0.1 27400
```

- 用 `OS.get_cmdline_user_args` 读 `--` 之后的参数
- 主机日志出现就绪标记后再起客户端
- 两边各自断言并以退出码报告，只看主机通过不算验收
- 本机回环没有延迟和丢包。给传输层包一层加延迟抖动丢包，否则预测和时序问题测不出来
- 超时按两端加载耗时之和留余量，不要贴着实测值。贴得太近时测试会偶发失败

## 参考

- `references/sync-checklist.md`：新增同步内容时的逐项检查
- `references/custom-transport.md`：`ENetConnection` 的发送 超时 断开语义
- `references/authoritative-movement.md`：预测 校正 重放的不变量
- [High-level multiplayer](https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html)
- [MultiplayerSynchronizer](https://docs.godotengine.org/en/stable/classes/class_multiplayersynchronizer.html)
- [ENetConnection](https://docs.godotengine.org/en/stable/classes/class_enetconnection.html)
