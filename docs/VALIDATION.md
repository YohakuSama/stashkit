# 验证步骤与边界

## 自动检查

按 [README](../README.md) 安装固定依赖和上游基准，然后运行前先将 Proxy 从 REJECT 切换到有效节点；停留在 REJECT 会使服务验收失败。使用 `--profile StashKit-Privacy.yaml` 或 `--profile StashKit-Local.yaml` 可指定正在验收的版本。运行：

```sh
python scripts/build_profiles.py --check
python -m unittest discover -s tests -v
python scripts/verify.py
python scripts/build_rules.py --check
python scripts/test_dns_endpoint.py
python scripts/build_offline_bundle.py --check
```

回归测试使用离线输入；真实 HTTPS DoH 探测单独运行，遇到证书错误、DNS 错误或不完整消息会失败，不跳过 TLS 身份检查。GitHub CI 的实测不等于每个用户网络都可用。

合并前可运行 `python scripts/check_remote.py --ref 完整候选提交SHA`，逐字节检查该提交的 54 个远程文件；省略参数则检查配置锁定的生产快照，始终不跟随 main。新的规则先在独立提交发布并完成字节校验，随后配置切换 pin 与缓存版本。内嵌 Private-local 由源文件、许可证摘要及三套配置一致性测试验证。

## Stash 真机验收

使用 iOS/tvOS 3.6+ 或 macOS 4.3+，导入主配置和填好个人订阅地址的覆写，确认已加载 54 个文件规则集、1 个内嵌 Private-local 和实际节点。覆写需另存为 `.stoverride`；示例中的 example.invalid 有意不可用。

| 项目 | 检查方法与预期 |
| --- | --- |
| 配置加载 | Stash 导入成功，更新规则成功，无循环引用或不识别字段错误 |
| 内网 | 路由器、NAS 和私有域名命中 DIRECT；自定义企业域名需额外指定内网 DNS |
| 公共服务 | api.openai.com → ChatGPT，gemini.google.com → Gemini，raw.githubusercontent.com → GitHub |
| CDN | 两个 gamer CDN → 動畫瘋；alibaba.cdn.steampipe.steamcontent.com → DIRECT；其他 steamcontent.com → Steam |
| 广告 | control.kochava.com、Google Ads / DoubleClick / Analytics 与 Copilot 遥测端点 → AdBlock；改选 DIRECT 为终止匹配后直连 |
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

## WebRTC / 公网 IPv4+IPv6 真机验收（不能由 CI 代替）

- 分别导入普通、Privacy 和 Local 配置，确认规则顺序：隐私版首条为 AliDNS DoH Proxy，之后所有配置先匹配 `PROTOCOL,STUN,REJECT` 和常见 STUN/TURN `DST-PORT`，再执行 LAN/国内直连。
- 打开 Stash Tunnel/VPN。在有 IPv6 的 Wi-Fi、蜂窝网络分别检查实际出口；IPv6 Tunnel 路由的 `Auto` 已通过测试时可保持，不需要强制切换到 Always。仅修改 DNS 的 IPv6 设置不能代替 Tunnel 接管。
- 使用 Stash 官方 `/rules/match` API 检查 `target=stun.l.google.com&network=udp&port=19302`、`target=1.1.1.1&network=udp&port=3478`、`target=[2606:4700:4700::1111]&network=udp&port=3478`（IPv6 `target` 语法以本机实际 API 为准），预期命中 REJECT 端口规则。再发真实 UDP STUN 探测到**非标准端口**，在连接日志确认 PROTOCOL STUN 拦截；静态 API 无法验证协议嗅探。
- 对照直连真实运营商 IPv4/IPv6、代理 HTTP 出口、[BrowserLeaks WebRTC](https://browserleaks.com/webrtc) 的 ICE `host/srflx/relay` 候选。目标是不暴露真实公网地址；若是 `host` 全局 IPv6，需额外通过浏览器隐私策略或禁用 WebRTC 修复，不能归功于 Stash 规则。重测 Wi-Fi/蜂窝、浏览器重启和系统休眠恢复。
- 验收受影响的原生 App 语音、视频通话、游戏联机及视频会议；此防护可能拦截 STUN/TURN 及同端口 TCP/UDP 业务。浏览器检测只是一种泄露测试手段，不代表全部原生应用的连接行为。

上面仅是人工验收计划，本仓库的 GitHub Actions 无法启动 Stash 系统 Tunnel 或获取浏览器 ICE 候选，CI 全绿不代表已经修复每台设备。

## v0.1.4 离线和隐私验收

- **在线**：检查各规则 URL 含同一固定 40 位 Git commit、provider 缓存 path 含 `v0.1.4`；第一次联网加载成功后切断网络再重启，确认 54 个缓存是否能继续使用（要注意代理本身也可能无法连通）。
- **离线**：从主分支 CI 下载 ZIP，验 SHA256SUMS，按 Stash 受管资源目录的版本路径部署 54 份文件，再加载 `StashKit-Local.yaml`。单独导入 YAML 而不部署文件**应失败**，不能标记为正常配置。GitHub Actions 的 ZIP 是备份/安装材料，不是 App 一键导入包。
- **隐私**：先通过个人订阅加载节点，手动切换 Proxy，再导入 `StashKit-Privacy.yaml`（或对普通配置启用 `dns-privacy.stoverride`，不要重复启用）；查看 AliDNS 主机的最终代理链及 DNS 记录。观察 Apple CDN、Wi-Fi/蜂窝切换、节点域名解析。若 DNS 不可用，先禁用覆写，不能断言绝对防泄漏。
- **图标**：39 张原始 PNG 已迁入 StashKit 自有仓库，40 个策略组均指向 StashKit 固定提交；联网更新配置后应看到专用图标。如仍显示默认图标，请重新导入或更新配置，并检查手机是否能访问 StashKit 的图标 PNG URL。
- **发布流程**：新的规则变更先完成源文件与生成器 CI，在一个包含全部新规则的固定 commit 上发布；配置文件随后单独修改 pin 和缓存版本号，切勿以当前配置 commit 的可变 main 指针做规则订阅。

## 自动采集真机运行时证据（只读）

在 Stash 已运行的 Mac（或同一受信任局域网内可访问 iOS Stash 控制端口的电脑）中，按 [Stash 官方 HTTP API](https://stash.wiki/features/http-api) 开启外部控制并设置密钥。不要把密钥提交到 GitHub。运行前先将 Proxy 从 REJECT 切换到有效节点；停留在 REJECT 会使服务验收失败。使用 `--profile StashKit-Privacy.yaml` 或 `--profile StashKit-Local.yaml` 可指定正在验收的版本。运行：

```sh
export STASH_API_TOKEN='由你在 Stash 设置的控制器密钥'
python scripts/stash_runtime_audit.py --base-url http://127.0.0.1:9090
```

iOS 使用界面显示的本地受信任设备地址替换 `127.0.0.1:9090`，不要向公共互联网开放控制接口。脚本使用**只读 GET** 检查模式、Proxy 递归后的真实节点、55 个预期 provider 的名称和条目数、规则总量、广告及业务哨兵的命中规则与最终出口，并读取内存接口；不会输出 API 密钥、个人节点名、订阅或者整个 DNS 缓存。**运行结果来自你的真实 Stash 才能称为真机验收**，GitHub Actions 无法代替它。DNS 旁路测试还需检查客户端连接记录与第三方 DNS 测试；单次 API 通过不是绝对无泄漏证明。

私网冷启动应在未缓存 GeoSite 的设备上验证 `router.internal`、NAS 单标签名称、路由器品牌域名与私有反向解析；三套配置不再含 GeoSite 引用。脚本通过只证明控制器返回的规则与出口符合配置，不代替真实业务连通性、播放或 DNS 旁路测试。
