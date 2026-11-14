# StashKit v0.1.24

本版发布 v0.1.23 之后已合并至主分支的修复，精简无用入口与过期工作流。规则内容不变。

- 新导入的主配置将 `Proxy` 的 `REJECT` 放在第一位。确认订阅节点加载后，需手动选择 `Auto` 或实际节点。旧设备保留过的选择需要单独检查；已选择 Auto/Fallback 且节点集为空时，仍存在 DIRECT 回退风险。
- 删除与主配置完全重复的 `StashKit-Subscription.yaml`。日常使用统一导入 `StashKit.yaml`。
- 不再单独发布 Privacy 和 Local 配置。DNS 隐私继续通过 `overrides/dns-privacy.stoverride.example` 启用；离线 ZIP 会按需生成 `StashKit-Local.yaml`，仍需手动部署规则资源。
- 修复离线 ZIP 安装说明中的规则版本路径，并固定发布任务的 Python 3.12 和依赖安装步骤。
- 删除仅供 v0.1.22、v0.1.23 迁移使用的两份 one-time-sync GitHub Actions 工作流。

本次仅更新配置版本至 v0.1.24。54 份基础规则继续使用 v0.1.23 的固定提交与缓存路径，Crypto 单独沿用 v0.1.13 的规则来源和 v0.1.18 的离线路径。40 个策略组、55 份远程规则、133 条内嵌 Private-local 匹配器、DNS 默认行为、13 条 WebRTC 拦截规则及整体分流顺序均不变。

离线 ZIP 不支持一键导入。请按 `README-OFFLINE.txt` 部署 55 份规则并核对 SHA256SUMS。配置含无效 Airport 订阅占位符，需在本地换成自己的订阅地址。

GitHub CI 仅覆盖静态规则与资源校验。WebRTC 泄露、空节点回退和真实网络出口应在 Stash 真机及控制器日志中验收。
