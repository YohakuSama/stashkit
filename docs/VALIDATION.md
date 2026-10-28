# 验证步骤与边界

## 自动检查

按 [README](../README.md) 安装固定依赖和上游基准，然后运行：

```sh
python -m unittest discover -s tests -v
python scripts/verify.py
python scripts/build_rules.py --check
python scripts/test_dns_endpoint.py
python scripts/build_offline_bundle.py --check
```

回归测试使用离线输入；真实 HTTPS DoH 探测单独运行，遇到证书错误、DNS 错误或不完整消息会失败，不跳过 TLS 身份检查。GitHub CI 的实测不等于每个用户网络都可用。

合并前可运行 `python scripts/check_remote.py --ref 完整候选提交SHA`，逐字节检查该提交已发布的 54 个远程资产；省略参数则检查生产 main。测试 PR 配置时，其 rule-providers 默认仍指向 main；需要手动把测试副本的远程规则 URL 中 main 替换为候选提交 SHA，避免误用旧资产，不能把临时测试 URL 提交回生产配置。

## Stash 真机验收

使用 iOS/tvOS 3.6+ 或 macOS 4.3+，导入主配置和填好个人订阅地址的覆写，确认已加载 54 个规则集和实际节点。覆写需另存为 `.stoverride`；示例中的 example.invalid 有意不可用。

| 项目 | 检查方法与预期 |
| --- | --- |
| 配置加载 | Stash 导入成功，更新规则成功，无循环引用或不识别字段错误 |
| 内网 | 路由器、NAS 和私有域名命中 DIRECT；自定义企业域名需额外指定内网 DNS |
| 公共服务 | api.openai.com → ChatGPT，gemini.google.com → Gemini，raw.githubusercontent.com → GitHub |
| CDN | 两个 gamer CDN → 動畫瘋；alibaba.cdn.steampipe.steamcontent.com → DIRECT；其他 steamcontent.com → Steam |
| 广告 | control.kochava.com → AdBlock；测试改变 AdBlock 的选项是否符合预期 |
| DNS | 查看应答服务器：公共真实解析使用 DoH，私有域名使用系统 DNS；独立检查其他 App 内置 DNS 和 VPN 接管范围 |
| 测速 | 检查 provider 的 benchmark-url 生效、节点失效后 Auto/Fallback 的实际选择；测速不证明服务地区解锁 |
| 默认安全出口 | 初次导入检查 Proxy 是否选中 REJECT；确认订阅有真实可用节点后，主动改选 Auto/Fallback/ALL，再检查 ChatGPT 等服务最终出口；旧配置升级时策略选择可能被保留 |
| 空订阅 | 分别测试合法但 proxies 为空、过滤后为空、首次下载失败、有旧缓存时下载失败；观察 Auto/Fallback/ALL 的真实出口，不能由 REJECT 占位推断绝对阻断 |
| 网络变化 | Wi-Fi/蜂窝切换、IPv4/IPv6、断网重连；检查节点域名解析与规则缓存 |
| 性能与播放 | 检查内存和请求记录，实际播放对应流媒体；离线路由测试不能证明播放或地区解锁 |

Stash 开启外部控制并设置本机 API 密钥后，可以用[官方 HTTP API](https://stash.wiki/features/http-api) 的 `GET /rules/match?target=...` 检查规则和最终代理链，`GET /providers/rules` 检查集合，`GET /dns/record` 检查 DNS。API 地址和密钥以本机设置为准，不能把密钥提交到仓库。

例如在本机控制器确实监听 127.0.0.1:9090 时：

```sh
curl --get 'http://127.0.0.1:9090/rules/match' \
  -H "Authorization: Bearer $STASH_API_TOKEN" \
  --data-urlencode 'target=192.168.1.1'
```

验收记录应写明 Stash 版本、平台、网络和实际出口。当前仓库的 CI 不启动 Stash，因此真机项目不能标成已由 CI 验证。

## v0.1.3 离线和隐私验收

- **在线**：检查各规则 URL 含同一固定 40 位 Git commit、provider 缓存 path 含 `v0.1.3`；第一次联网加载成功后切断网络再重启，确认 54 个缓存是否能继续使用（要注意代理本身也可能无法连通）。
- **离线**：从主分支 CI 下载 ZIP，验 SHA256SUMS，按 Stash 受管资源目录的版本路径部署 54 份文件，再加载 `StashKit-Local.yaml`。单独导入 YAML 而不部署文件**应失败**，不能标记为正常配置。GitHub Actions 的 ZIP 是备份/安装材料，不是 App 一键导入包。
- **隐私**：先通过个人订阅加载节点，手动切换 Proxy 再启用 `dns-privacy.stoverride`；查看 AliDNS 主机的最终代理链及 DNS 记录。观察 Apple CDN、Wi-Fi/蜂窝切换、节点域名解析。若 DNS 不可用，先禁用覆写，不能断言绝对防泄漏。
- **图标**：39 个旧图标 URL 已移除，策略页应使用 Stash 默认图标。
- **发布流程**：新的规则变更先完成源文件与生成器 CI，在一个包含全部新规则的固定 commit 上发布；配置文件随后单独修改 pin 和缓存版本号，切勿以当前配置 commit 的可变 main 指针做规则订阅。
