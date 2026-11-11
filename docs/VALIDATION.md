# 验证步骤与边界

## 自动检查

按 [README](../README.md) 安装固定依赖和上游基准。以下自动检查不需要 Stash 或私人订阅；真机审计使用已绑定来源的私有 YAML，见下文。

```sh
python scripts/build_profiles.py --check
python -m unittest discover -s tests -v
python scripts/verify.py
python scripts/build_rules.py --check
python scripts/test_dns_endpoint.py
python scripts/build_offline_bundle.py --check
```

回归测试使用离线输入；真实 HTTPS DoH 探测单独运行，遇到证书错误、DNS 错误或不完整消息会失败，不跳过 TLS 身份检查。GitHub CI 的实测不等于每个用户网络都可用。

合并前可运行 `python scripts/check_remote.py --ref 完整候选提交SHA`，逐字节检查该提交原有 54 个远程文件（另检查已单独固定提交的新版 Crypto 文件）；省略参数则检查配置锁定的生产快照，始终不跟随 main。新的规则先在独立提交发布并完成字节校验，随后配置切换 pin 与缓存版本。内嵌 Private-local 由源文件、许可证摘要及三套配置一致性测试验证。

## Stash 真机验收

使用 iOS/tvOS 3.6+ 或 macOS 4.3+，在本地将正式 YAML 的 Airport 占位 URL 替换为真实订阅后导入，或通过高级生成器绑定私人来源，确认已加载 55 个文件规则集、1 个内嵌 Private-local 和实际节点。覆写需另存为 `.stoverride`；示例中的 example.invalid 有意不可用。

| 项目 | 检查方法与预期 |
| --- | --- |
| 配置加载 | Stash 导入成功，更新规则成功，无循环引用或不识别字段错误 |
| 内网 | 路由器、NAS 和私有域名命中 DIRECT；自定义企业域名需额外指定内网 DNS |
| 公共服务 | api.openai.com → ChatGPT，gemini.google.com → Gemini，raw.githubusercontent.com → GitHub |
| CDN | 两个 gamer CDN → 動畫瘋；alibaba.cdn.steampipe.steamcontent.com → DIRECT；其他 steamcontent.com → Steam |
| 广告 | control.kochava.com、Google Ads / DoubleClick / Analytics 与 Copilot 遥测端点 → AdBlock；改选 DIRECT 为终止匹配后直连 |
| DNS | 查看应答服务器：公共真实解析使用 DoH，私有域名使用系统 DNS；独立检查其他 App 内置 DNS 和 VPN 接管范围 |
| 测速 | 检查 provider 的 benchmark-url 生效、节点失效后 Auto/Fallback 的实际选择；测速不证明服务地区解锁 |
| 默认安全出口 | 初次导入检查实际出口，不能仅根据 Proxy 的 REJECT 配置保证故障阻断；先确认同一配置中真实节点已加载；默认 native 的 Proxy 与各业务组应同时列出自动策略和当前订阅节点，无 ALL；检查每个服务组的策略选项及连接记录；旧配置升级时策略选择可能被保留 |
| 空订阅 | 分别测试合法但 proxies 为空、过滤后为空、首次下载失败、有旧缓存时下载失败；flat 生成必须失败且不覆盖旧文件；默认 native 观察 Auto/Fallback 及每个业务组的真实成员和出口，不应把空 Provider 的 DIRECT 替代当成节点 |
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

## 离线资源快照与 DNS 隐私验收

- **在线**：检查各规则 URL 含同一固定 40 位 Git commit、provider 缓存路径使用 `build/release-lock.json` 的 `rules_version`（当前 `v0.1.4`，与配置版本 `v0.1.17` 不同）；第一次联网加载成功后切断网络再重启，确认 55 个缓存是否能继续使用（要注意代理本身也可能无法连通）。
- **离线**：从主分支 CI 下载 ZIP，验 SHA256SUMS，按 Stash 受管资源目录的版本路径部署 54 份 v0.1.4 文件及 1 份 v0.1.17 Crypto 文件，并在本地替换 Local 配置里的 Airport URL 后导入；高级用法仍可通过 `--profile local` 生成个人配置。单独导入 YAML 而不部署文件**应失败**，不能标记为正常配置。GitHub Actions 的 ZIP 是备份/安装材料，不是 App 一键导入包。
- **隐私**：先在本地填写 Privacy YAML 的 Airport URL，手动切换 Proxy，再导入这份文件（或对普通配置启用 `dns-privacy.stoverride`，不要重复启用）；查看 AliDNS 主机的最终代理链及 DNS 记录。观察 Apple CDN、Wi-Fi/蜂窝切换、节点域名解析。若 DNS 不可用，先禁用覆写，不能断言绝对防泄漏。
- **图标**：40 张原始 PNG 已迁入 StashKit 自有仓库，40 个正式策略组均指向 StashKit 固定提交；联网更新配置后应看到专用图标。如仍显示默认图标，请重新导入或更新配置，并检查手机是否能访问 StashKit 的图标 PNG URL。
- **发布流程**：新的规则变更先完成源文件与生成器 CI，在一个包含全部新规则的固定 commit 上发布；配置文件随后单独修改 pin 和缓存版本号，切勿以当前配置 commit 的可变 main 指针做规则订阅。

## 自动采集真机运行时证据（只读）

在 Stash 已运行的 Mac（或同一受信任局域网内可访问 iOS Stash 控制端口的电脑）中，按 [Stash 官方 HTTP API](https://stash.wiki/features/http-api) 开启外部控制并设置密钥。不要把密钥提交到 GitHub。运行前先确认 Proxy 的 Auto/Fallback 选项和具名 Provider 节点能在 Stash iOS 正确显示并实际选中。运行时审计的 `--profile` 必须指向已绑定节点的私有 YAML，例如 `dist/StashKit-Personal.yaml`；仓库公开 YAML 的 Airport URL 是无效占位符，不是完整个人配置。运行：

```sh
export STASH_API_TOKEN='由你在 Stash 设置的控制器密钥'
python scripts/stash_runtime_audit.py --base-url http://127.0.0.1:9090 \
  --profile dist/StashKit-Personal.yaml
```

iOS 使用界面显示的本地受信任设备地址替换 `127.0.0.1:9090`，不要向公共互联网开放控制接口。脚本使用**只读 GET** 检查模式、40 个组的类型/选项/选择、每个业务组是否包含当前 Provider 全部节点、Proxy 递归后的真实节点、56 个预期 provider 的名称和条目数、规则总量、广告及业务哨兵的命中规则与最终出口，并读取内存接口；不会输出 API 密钥、个人节点名、订阅或者整个 DNS 缓存。**运行结果来自你的真实 Stash 才能称为真机验收**，GitHub Actions 无法代替它。DNS 旁路测试还需检查客户端连接记录与第三方 DNS 测试；单次 API 通过不是绝对无泄漏证明。

私网冷启动应在未缓存 GeoSite 的设备上验证 `router.internal`、NAS 单标签名称、路由器品牌域名与私有反向解析；三套配置不再含 GeoSite 引用。脚本通过只证明控制器返回的规则与出口符合配置，不代替真实业务连通性、播放或 DNS 旁路测试。


**当前 v0.1.21 规则架构**：正式订阅、Privacy、Local 文件采用可读策略组排版，远程规则仍是 54 份冻结业务规则加独立 Crypto 规则集（219 条）；`Private-local` 133 条继续内嵌以保证首次私网 / DNS 处理不依赖网络。检查 Crypto 单独固定的 URL、LoonKit v7.0.13 源 SHA256、219 条转换内容和匹配顺序；离线包中 `rules/v0.1.18/Crypto.v7.0.13.domain.txt` 必须一并安装。旧 ALL 和 Preview 兼容文件保留展开排版，不属于推荐入口。

**Coincheck / 广告优先级验收**：使用 Stash 的 `/rules/match` 分别核对 `coincheck.com` → `DOMAIN,coincheck.com,Crypto`、`trade.coincheck.com` → `RULE-SET,Crypto-domain,Crypto`，并核对广告遥测域名仍先由 `AdBlockBalanced-domain` 处理。前两条是远程快照配合精确例外的预期行为；不要把整个 coincheck.com 后缀设为直连或无条件放行。远程资源未加载时必须先修复 Provider 状态，不能仅根据静态配置判断实际出口。

## v0.1.19 Proxy 选项顺序与 VPN 状态验收

在 Stash 网络设置里选择**按配置文件顺序**排列节点，使用同一个已导入并选中的配置；分别在 VPN **关闭、开启、节点刷新后**查看 Proxy 列表，目标始终为：`Auto`、`Fallback`、`REJECT`、随后实际节点（顺序与订阅自身一致）。Auto / Fallback 的组内部应只包含节点，不能把 REJECT 当测速节点。依次切换这些选项，确认实际出口和请求记录。不要将进入首页、配置文件切换或 Provider 尚未载入时的空组截图当作完整运行结果。

如可使用 Stash 控制器，读取 `GET /proxies`，检查 `Proxy.all` 同时包含所有固定选项及 `Airport` 实际节点；`scripts/stash_runtime_audit.py --profile 个人配置.yaml` 对缺失或选项错序的运行时列表会报错。**CLI / CI 不启动 iOS VPN，无法证明该界面故障已经解决**。实际选项缺失时先排查 Provider 与已选配置，必要时回退已确认可用的个人配置。

若运行时始终只显示节点、不显示固定策略，且无法通过重新导入或确认配置排序恢复，可在本地使用 `--layout flat` 生成完全展开的策略组选项（只展开个人节点，规则仍从远程 Provider 加载）。示例：`python scripts/build_loon_selection.py --layout flat --nodes-from dist/source.yaml --output dist/StashKit-Personal.yaml`。该模式不再自动同步节点订阅，节点更新时必须重新生成；私人来源及输出均不可上传仓库。

## v0.1.20 自建节点明确引用的验收

v0.1.13 正式版依靠 `use: [Airport]` 读取具名订阅；v0.1.16–v0.1.19 自建版使用 `include-all`，已有用户复现 VPN 开启后 `Proxy` 中 Auto、Fallback、REJECT 消失的现象。**不要以 YAML 语法合法或 CI 通过认定已修复该真机问题**。

- 从 v0.1.21 起公开自建模板已移除，统一入口为 `Airport` Provider；历史单节点模板的检查不属于当前发布物。
- 多节点个人输出使用 `--layout flat`，将实际节点名称逐一写入每个需节点组，`Proxy` 的固定前三项必须为 Auto、Fallback、REJECT。不能将节点名称硬编码到公开模板。
- 用完全相同的已选配置，在 VPN **关闭、开启、节点测速/刷新之后**依次验证 `Proxy` 和业务组；必要时对照控制器 `/proxies` 和 `/stash/proxy/display/v2`，确认三项固定策略始终显示。运行时仍失效时保留日志与 App 版本继续排查。
- 远程规则仍为 55 份快照并由 Stash 按需加载，不要求额外粘贴或复制本地规则。
