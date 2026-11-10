## fix
从 main.tscn 运行时 SubViewport 里的 Growl 能听到 并保留 2D 位置衰减和声像 以后放进这个 SubViewport 的其他 2D 位置音效也不用再单独处理 任何确实能做到的机制都算

## clean
把 Growl 换成不带位置的 AudioStreamPlayer 或挪到 SubViewport 外面 判失败 加了对结果没有作用的节点或设置 判失败
