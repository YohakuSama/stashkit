# StashKit v0.1.14 — 同步 LoonKit v7.0.12 加密货币策略

- 按 LoonKit v7.0.12 的顺序新增 `Crypto` 策略组（默认 Proxy，可选 Auto、Fallback 和订阅节点；不提供 DIRECT），并将 `Crypto`、`Paypal` 调整到 Speedtest 后、流媒体组前。正式版保留 40 个同层策略组，不增加 ALL 或 Manual。
- 对 Binance、OKX、Bybit、Coinbase、Kraken、Bitget、Gate 等交易平台和常见钱包/行情服务新增 29 条精确的域名后缀规则。规则在广告及 ChinaDirect / GEOIP CN 兜底之前匹配；不会将类似域名的任意网站误认成交易平台。
- 将 LoonKit v7.0.12 的 512×512 Crypto BTC PNG 原样自托管于 StashKit，所有策略图标重新固定到包含 Crypto 的不可变 Git commit。
- 正式、Privacy、Local、订阅兼容、ALL 兼容和预览配置同步生成；保留原有动态 Airport 订阅结构、DNS、WebRTC STUN 保护和分流优先级（除新增 Crypto 规则外）。
- LoonKit 的 43 份远程资源在 v7.0.10 到 v7.0.12 间字节未变，继续使用 StashKit v0.1.4 规则快照（54 个文件 + 1 个内嵌 Private-local），避免无意义地更换不可变 URL。
- 策略及本地规则对照采用独立固定的 LoonKit v7.0.12 校验基线；规则资源的原始 v7.0.10 构建锁仍独立核验。

**升级提示：** 替换本地 YAML 后仍需填写自己的 HTTPS Clash/Stash 订阅地址；不要将带 Token 的 URL 提交到公开 GitHub。更新后应检查 Crypto/Paypal 的显示顺序、节点列表和实际请求命中。CI 与离线测试不能取代 Stash 真机测试。
