# StashKit 路由决策

规则按先后顺序匹配。域名出现在多个集合中，不代表每个策略都能控制它。

## 服务直连与代理选择

LoonKit v7.0.10 的直连能力在 StashKit 保持为两层：

- **规则直接直连**：`DomesticCore`、`DomesticSupplement`、`DomesticAI`、`SteamCN` 和国内 IP 命中对应规则后直接走 `DIRECT`，独立于 `Proxy` 当前选中什么。
- **服务策略可以直连**：`Apple`、`Microsoft`、`Bilibili`、`Line`、`Speedtest` 的首选项为 `DIRECT`；`Steam` 可手动选 `DIRECT`，但默认仍为 `Proxy`。这些组还能直接选择 `Auto`、`Fallback` 或订阅节点。
- **海外服务不自动直连**：`ChatGPT`、`Gemini`、`Claude` 等保留 LoonKit 的默认代理逻辑。`Proxy` 不添加 `DIRECT` 选项，避免把多个海外服务一次性切成直连。

策略组选择仅对**实际命中该策略组的请求**有效。例如广告规则先命中 `AdBlock`、国内服务先命中 `DIRECT` 时，之后的 Apple / Steam 组不会再覆盖它们。Stash 可能保留更新前设备上的旧选择，需在策略界面明确检查当前选中项。

| 目标 | 策略 | 原因 |
| --- | --- | --- |
| 私有域名、LAN 地址 | DIRECT | Private-local 内嵌精确域名、后缀与单标签匹配，不依赖首次下载 GeoSite；Fake-IP 过滤不等于直连 |
| raw.githubusercontent.com | GitHub | 默认仍经 Proxy，手动切换 GitHub 组时同时生效 |
| alibaba.cdn.steampipe.steamcontent.com | DIRECT | 将 ChinaDirect 已有的精确国内 CDN 规则前移到 SteamCN |
| 其他 steamcontent.com | Steam | 不把整个全球下载域名当成国内 CDN |
| gamer-cds.cdn.hinet.net、gamer2-cds.cdn.hinet.net | 動畫瘋 | 仅保留已知流媒体 CDN，不包含整个 HiNet 域名 |
| DigiCert、其他 HiNet 域名 | 后续普通规则或 Final | 通用证书服务和运营商流量不绑定到動畫瘋 |
| control.kochava.com、Disney 集合中的统计域名 | AdBlock | 广告/统计拦截优先，不因出现在服务集合中而整体放行 |
| Google Ads / DoubleClick / Analytics 常用端点及 -cn 变体 | AdBlock | v0.1.4 通过本地调整补齐，优先于 Google 服务集合 |
| copilot-telemetry.githubusercontent.com | AdBlock | 移除前置 AI 覆盖，保留广告集中原有遥测拦截；Copilot 建议 API 仍交给 AI |
| www.amazon.com、Amazon 共用图片主机 | PrimeVideo | 沿用既有集合；购物请求也可能命中此组 |
| gvt1.com、gvt2.com 及其子域名 | YouTube | 沿用既有集合；共享域名上的其他请求也由此组控制 |
| api.statsig.com | Proxy | 功能配置共用接口；没有整体封禁 Statsig |
| challenges.cloudflare.com | Cloudflare | 沿用 Cloudflare 后缀规则；独立选节点时可能与业务出口不同 |
| graph.facebook.com | Whatsapp | 沿用上游对共享 Meta 接口的优先级；会同时影响其他使用此域名的服务 |

生成器通过 [adjustments.json](../build/adjustments.json) 应用可审查的增删；固定的上游源不被修改。HiNet 的精确 CDN 域名来自[巴哈姆特站务诊断记录](https://forum.gamer.com.tw/C.php?bsn=60404&page=2&snA=27729)；播放服务可能改变 CDN，新增域名应根据实际请求记录单独补充，不能扩大到整个运营商。

域名遮蔽不全是错误。例如 YouTube 优先于 Google、广告拦截优先于服务统计，属于明确的策略选择。优化时应使用预期路由用例，而不是自动删除所有重叠项。

`GEOIP,CN,DIRECT,no-resolve` 以及 CIDR/ASN 的 `no-resolve` 保留了上游避免主动解析的取舍：域名若未命中域名集合，这些规则不会为了判断国家而触发 DNS；没有已有目标 IP 的请求会进入 Final。因此此配置不保证所有国内域名自动直连。

`tests/test_routing.py` 只对显式域名规则、文本规则集和私有 IP 做离线检查；完整 GeoSite/GeoIP/ASN 数据、嗅探、DNS 缓存与协议行为，仍需 Stash 真机 `/rules/match` 和连接记录验收。

`AdBlock → DIRECT` 是终止匹配后直连，不是跳过广告规则继续分流。对某个业务需要放行时，在广告规则之前使用精确域名例外并指向其正确服务组。域名规则无法区分同一主机上的业务路径和广告路径。

54 份文件规则的 URL 固定提交，定时更新只获取同一快照。发布新规则时需切换规则 pin 与版本缓存目录；不自动追随可变上游。
