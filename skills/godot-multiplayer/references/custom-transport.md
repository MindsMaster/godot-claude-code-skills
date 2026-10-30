# 在 ENetConnection 上自建传输

高层 API 够用时不要走这条路。自己写协议时下面这些语义来自 Godot 4.7.2 附带的 ENet 源码。

## 发送

- `ENetPacketPeer.send` 只入队。实际发出在 `ENetConnection.service` 或 `ENetConnection.flush`
- 轮询放在帧开头、发送放在帧后面时，每条消息要等到下一次轮询才发出。发完调一次 `ENetConnection.flush` 可以省掉这一拍
- `ENetConnection.broadcast` 发给所有已连接对端

## 超长包

标志 0 表示不可靠有序。包长超过分片长度时，分支是这样的：

| 标志 | 分片方式 |
|---|---|
| 0 | 可靠分片，要确认，会重传 |
| `ENetPacketPeer.FLAG_UNRELIABLE_FRAGMENT` | 不可靠分片，丢一片整包丢 |

高层的 `TRANSFER_MODE_UNRELIABLE_ORDERED` 带了这个标志，低层默认不带。走标志 0 的通道上，一个超长包会静默变成可靠发送。

分片长度等于 MTU 减 28 字节，默认 MTU 1392 时是 1364。

## 顺序

- 同一通道上的不可靠包，比已收到序号旧的直接丢弃
- 不同通道之间没有顺序。把可靠消息放通道 0、不可靠放通道 1 时，后发的不可靠包可能先到
- `ENetPacketPeer.FLAG_UNSEQUENCED` 不排序

## 超时与断开

- 超时断开的事件数据字是 0。主动断开传的原因码要避开 0，否则分不清
- `ENetPacketPeer.set_timeout` 的三个参数要求 `timeout <= timeout_min <= timeout_max`
- `ENetPacketPeer.peer_disconnect_later` 等排队的包发完再断，踢人前的最后一条消息靠它送达
- `ENetPacketPeer.peer_disconnect_now` 不产生断开事件，对端也不保证收到
- 默认每 500 ms 发一次可靠 ping，超时检查依赖有未确认的可靠包
