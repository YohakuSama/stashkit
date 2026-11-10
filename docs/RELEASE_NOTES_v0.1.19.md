# StashKit v0.1.19

策略组可读格式与选择顺序修正候选：针对 VPN 启动后 Proxy 只列出节点、丢失 Auto/Fallback/REJECT 的报告。

- 40 个策略组恢复多行 YAML，Proxy 明确先写 `Auto → Fallback → REJECT`，然后才引用 `Airport` 或自建节点。各业务组同样先列固定策略，再声明节点来源。
- 高级原生生成器修复曾将 REJECT 排在具体节点之后的问题，输出顺序现在固定为 `Auto → Fallback → REJECT → 节点`。
- 保留 v0.1.18 的远程规则架构：55 个固定提交的远程规则 Provider，其中 Crypto 为 LoonKit v7.0.13 的 219 条规则；不新增大批本地域名。
- 加入 CI 组字段顺序校验及 Stash 控制器运行时检查，检测固定选项被动态节点覆盖或错序的情况。

**必须真机确认：** YAML 的 Flow Mapping 与 Block Mapping 语义相同，格式回退不保证能修复 Stash 在 VPN 启动后的动态组加载故障。请实际对比 VPN 开启前/后的 Proxy 成员及 Stash 网络设置中的排序方式；若运行时只剩节点，仍须继续定位 App 具体行为。

[验收方法](./VALIDATION.md) · [路由与架构](./ARCHITECTURE_AUDIT.md)

**兼容回退**：如果动态 Provider 混用的运行时问题仍存在，可以按 README 使用 `--layout flat` 从自己的节点来源生成明确选项的个人配置。此方法只将个人节点明确列在配置中，55 份业务规则仍为远程引用。静态节点需手动重新生成，不要把生成的私人配置提交到公共仓库。
