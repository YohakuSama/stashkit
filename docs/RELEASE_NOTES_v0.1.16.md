# StashKit v0.1.16 — 修复自建多节点不显示

## 修复

- **问题**：v0.1.15 的 `StashKit-SelfHosted.yaml` 将 38 个需要节点的策略组固定为单个 `SelfHosted`，因此用户向顶层 `proxies:` 复制额外节点后，策略组不会自动列出新名字。
- **改进**：依照 [Stash 官方策略组说明](https://stash.wiki/proxy-protocols/proxy-groups)，自建版的 38 个节点策略组改为 `include-all: true`，自动引用顶层 `proxies:` 的全部本地节点（无远程 Provider）。保留 Auto / Fallback、业务分流组和原有固定候选选项；AdBlock / Final 保持原样。
- **使用方法**：下载 `StashKit-SelfHosted.yaml`，仅在顶层 `proxies:` 中填写 1 个或多个 Stash/Clash 格式节点，名称可以不同但不得重复；保持单个顶层 `proxies:` 字段。重新从本地文件导入 Stash，**选择并启用新导入的配置**，再检查 Proxy / Auto / ChatGPT 等策略组。
- **安全**：公开样例的地址与密码均无效；请仅在个人本地副本填写真实订阅与自建节点认证凭据。

## 保持不变

- 40 个原生策略组和分流规则；29 条 Crypto 规则及对应专属图标；已固定的 54 份远程规则；DNS 与 STUN / TURN 处理。
- `StashKit-Subscription.yaml` 和 `StashKit.yaml` 仍为 Airport 动态订阅，使用方式不变。兼容配置只同步版本号。
- 增加了任意三个不同节点名称及重名拒绝的结构回归。通过 CI 不等于 Stash App 已对实际节点连接和 DNS 做真机验收。

请勿把个人服务器地址、UUID、密码、订阅 Token 或其他密钥推送到公开仓库。
