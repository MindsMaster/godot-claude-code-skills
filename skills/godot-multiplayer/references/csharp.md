# C# 对照

SKILL.md 各节示例的 C# 写法和 C# 独有的要点。

## 建连

```csharp
public partial class Network : Node
{
    private const int Port = 7000;
    private const int MaxClients = 3;

    public Error Host()
    {
        var peer = new ENetMultiplayerPeer();
        Error error = peer.CreateServer(Port, MaxClients);
        if (error != Error.Ok)
        {
            return error;
        }
        Multiplayer.MultiplayerPeer = peer;
        return Error.Ok;
    }

    public Error Join(string address)
    {
        var peer = new ENetMultiplayerPeer();
        Error error = peer.CreateClient(address, Port);
        if (error != Error.Ok)
        {
            return error;
        }
        Multiplayer.MultiplayerPeer = peer;
        return Error.Ok;
    }
}
```

## 主机校验

```csharp
public partial class Chest : Node
{
    private const float OpenRange = 3.0f;

    private readonly Dictionary<int, Node3D> _players = new();
    private Vector3 _chestPosition = Vector3.Zero;
    private bool _opened;

    public void RequestOpen()
    {
        RpcId(1, MethodName.OpenChest);
    }

    [Rpc(MultiplayerApi.RpcMode.AnyPeer, CallLocal = true, TransferMode = MultiplayerPeer.TransferModeEnum.Reliable)]
    private void OpenChest()
    {
        if (!Multiplayer.IsServer() || _opened)
        {
            return;
        }
        int sender = Multiplayer.GetRemoteSenderId();
        if (!_players.TryGetValue(sender, out Node3D player) || player.GlobalPosition.DistanceTo(_chestPosition) > OpenRange)
        {
            return;
        }
        _opened = true;
    }
}
```

- RPC 方法名用 `MethodName` 常量传给 `Node.Rpc` `Node.RpcId`
- RPC 参数须是 Variant 兼容类型

## 复制

```csharp
public partial class EnemySpawner : MultiplayerSpawner
{
    [Export] public PackedScene EnemyScene { get; set; }

    public override void _Ready()
    {
        SpawnFunction = Callable.From<Variant, Node>(CreateEnemy);
    }

    private Node CreateEnemy(Variant data)
    {
        var enemy = EnemyScene.Instantiate<Node3D>();
        enemy.Position = data.AsGodotDictionary()["position"].AsVector3();
        return enemy;
    }
}
```

- `MultiplayerSpawner.SpawnFunction` 是 `Callable`，用 `Callable.From<Variant, Node>` 包装
