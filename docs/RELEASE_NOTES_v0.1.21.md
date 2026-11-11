# StashKit v0.1.21 — 统一订阅配置入口

本版取消公开 `StashKit-SelfHosted.yaml` 独立自建模板，唯一推荐的在线入口为 [StashKit.yaml](../StashKit.yaml)。在本地把 `proxy-providers.Airport.url` 换成真实 HTTPS Clash/Stash YAML 节点订阅；示例 `example.invalid` 不可用。

- 保留 40 个策略组（`Proxy` 固定 Auto、Fallback、REJECT），38 个需节点组继续使用 `Airport` Provider。
- 不修改 DNS、路由规则、55 份远程规则快照及图标。
- 需要在本机维护个人静态节点时，可使用 `scripts/build_loon_selection.py --layout flat` 生成私人配置；仓库不再提供单独自建版下载入口。
- CI 能验证配置结构，但**无法模拟 iOS Stash VPN**。应在受影响设备对照 VPN 开关、节点刷新前后的选项。

私人订阅地址、节点密码和 Token 不应提交到公开仓库。
