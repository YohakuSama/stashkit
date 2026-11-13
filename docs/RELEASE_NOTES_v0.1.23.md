# StashKit v0.1.23

本版按 LoonKit v7.0.16 完成 Apple Intelligence、New Siri 和 Stripe 的远程分流同步。

- Apple 规则库增加 Apple PCC 的 `apple-relay.cloudflare.com`、`apple-relay.fastly-edge.com`、`cp4.cloudflare.com`。既有 Siri 域名继续由 Apple 后缀覆盖。
- AppleOTA、Apple 两份 `RULE-SET` 移到通用 Cloudflare 之前，保持 AppleOTA 优先于 Apple；其余 Cloudflare 流量不变。
- `SharedInfrastructure-domain` 增加 `+.stripe.com`、`+.stripe.network`，由原有 Proxy 接管 Stripe 支付和风控。
- 四条 Apple EdgeKey 旧规则已经被原有上级后缀完全覆盖，故删除冗余。
- 40 个策略组、55 份远程规则 Provider、133 条 Private-local 内嵌规则、最终 `MATCH,Final` 以及个人节点绑定方式不变。
- 默认 Stash、Privacy、Local、兼容 ALL 与 Preview 配置统一更新，离线规则包可在正式 Release 中获取。

更新 Stash 配置后刷新远程规则缓存。修改过 `Airport` 私人订阅的用户应备份配置并在新版填回原 URL。CI 只能验证静态配置与下载资源，真机 DNS、GeoIP 和出口结果以 Stash 记录为准。
