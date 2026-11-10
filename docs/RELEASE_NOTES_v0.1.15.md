# StashKit v0.1.15 — 订阅 / 自建双入口

- README 首页提供两条明确下载路径：**StashKit-Subscription.yaml**（修改 proxy-providers.Airport.url）和 **StashKit-SelfHosted.yaml**（修改顶层 proxies 的 SelfHosted 节点定义）。
- 新增**完整单文件自建节点配置**：保留 40 个策略组、54 份远程规则资源及原有 DNS / STUN 防护；移除订阅版 Airport Provider，将 38 个需节点策略组直接绑定单个静态 SelfHosted 节点，Auto / Fallback 使用相同节点池。无需改动每个组，也无需额外本地代理文件。
- 自建版公开文件使用无效服务器地址和密码占位符；必须在本地替换真实协议、地址、端口和认证参数，节点名称应保持 SelfHosted。示例为 Shadowsocks，其他协议需按对应 Stash 语法填写。
- 订阅版依旧自动更新；StashKit.yaml 与 StashKit-Subscription.yaml 内容一致。其他正式和兼容配置只同步配置版本号，没有变更规则、DNS、策略组选项或图标。
- 将自建版加入确定性派生与结构回归；CI 不能代替真实 Stash App 对协议连接、DNS 和断线行为的设备验收。

请勿将私人订阅链接、凭证、UUID、私钥或自建服务器秘密提交到公开仓库。
