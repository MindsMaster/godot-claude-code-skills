---
type: llm
criteria: 指出 add_group_task 的 high_priority 默认 false 低优先级任务同时只能占 threading/worker_pool/low_priority_thread_ratio 默认 0.3 比例的线程 8 核机器上大约两个线程 这就是只有两个核忙的原因 并把 high_priority 传 true 指出 add_group_task 每个元素调用一次 Callable 不会自动分块 改成元素数传块数 每块处理一段连续下标 单位数 4000 不变 每帧都算 转向公式和读写数组的方式不变 结果与原来一致 没有改成隔帧计算 没有在线程任务里调用场景树或改变数组大小 轨迹中间被省略的写入看不到时 以能看到的写入内容和最终回复对做法的描述为依据 看不到不等于违规
focus: trace
---
