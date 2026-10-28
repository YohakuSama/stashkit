# StashKit 路由决策

规则按先后顺序匹配。域名出现在多个集合中，不代表每个策略都能控制它。

| 目标 | 策略 | 原因 |
| --- | --- | --- |
| 私有域名、LAN 地址 | DIRECT | 内网解析和连接保留在本地；Fake-IP 过滤不等于直连 |
| raw.githubusercontent.com | GitHub | 默认仍经 Proxy，手动切换 GitHub 组时同时生效 |
| alibaba.cdn.steampipe.steamcontent.com | DIRECT | 将 ChinaDirect 已有的精确国内 CDN 规则前移到 SteamCN |
| 其他 steamcontent.com | Steam | 不把整个全球下载域名当成国内 CDN |
| gamer-cds.cdn.hinet.net、gamer2-cds.cdn.hinet.net | 動畫瘋 | 仅保留已知流媒体 CDN，不包含整个 HiNet 域名 |
| DigiCert、其他 HiNet 域名 | 后续普通规则或 Final | 通用证书服务和运营商流量不绑定到動畫瘋 |
| control.kochava.com、Disney 集合中的统计域名 | AdBlock | 广告/统计拦截优先，不因出现在服务集合中而整体放行 |
| graph.facebook.com | Whatsapp | 沿用上游对共享 Meta 接口的优先级；会同时影响其他使用此域名的服务 |

生成器通过 [adjustments.json](../build/adjustments.json) 应用可审查的增删；固定的上游源不被修改。HiNet 的精确 CDN 域名来自[巴哈姆特站务诊断记录](https://forum.gamer.com.tw/C.php?bsn=60404&page=2&snA=27729)；播放服务可能改变 CDN，新增域名应根据实际请求记录单独补充，不能扩大到整个运营商。

域名遮蔽不全是错误。例如 YouTube 优先于 Google、广告拦截优先于服务统计，属于明确的策略选择。优化时应使用预期路由用例，而不是自动删除所有重叠项。

`GEOIP,CN,DIRECT,no-resolve` 以及 CIDR/ASN 的 `no-resolve` 保留了上游避免主动解析的取舍：域名若未命中域名集合，这些规则不会为了判断国家而触发 DNS；没有已有目标 IP 的请求会进入 Final。因此此配置不保证所有国内域名自动直连。

`tests/test_routing.py` 只对显式域名规则、文本规则集和私有 IP 做离线检查；完整 GeoSite/GeoIP/ASN 数据、嗅探、DNS 缓存与协议行为，仍需 Stash 真机 `/rules/match` 和连接记录验收。
