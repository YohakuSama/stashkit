# StashKit

独立的 Stash 原生分流配置，基于 [LoonKit v7.0.10](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9) 正式规则。全部规则自本仓库托管，不依赖旧的 `loonkit/stashkit` 目录。

当前配置版本 **v0.1.4**。最低文档支持范围为 **Stash iOS/tvOS 3.6+、macOS 4.3+**，用于加密 DNS bootstrap 和独立的节点域名解析；不适用于把同名字段直接套到旧版 Clash 或 Loon。[变更记录](./docs/CHANGELOG.md) · [真机验收步骤](./docs/VALIDATION.md) · [架构审计与剩余风险](./docs/ARCHITECTURE_AUDIT.md)。

## 导入

**配置 URL：**

```text
https://raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.yaml
```

从 Stash 配置管理界面通过 URL 导入 [StashKit.yaml](./StashKit.yaml)。**需自行添加节点或兼容 Clash/Stash 的订阅**；项目不含个人节点或密钥。可参照 [订阅覆写示例](./overrides/provider.stoverride.example)，将 `example.invalid` 替换成合法的订阅 URL 后在 Stash 中应用。确认 Proxy、ALL、Auto、Fallback 节点池已加载并实际选路；Bing 测速不保证地区解锁。

测速参数按 Stash 官方机制配置在节点或 `proxy-providers` 的 `benchmark-url` / `benchmark-timeout` 上；同一节点在多个组中共享测速结果。示例统一使用 Bing HTTP 测速，组内仅设置测试间隔，不使用 Clash 风格的组级 `url`。

**安全默认值：Proxy 初始选择 `REJECT`，而不是 `Auto`。**这是因为 Stash 官方说明空的远程代理集可能回落到 `DIRECT`，若自动组在无节点时生效，可能误将预期走代理的服务直连。导入个人订阅并确认节点正常后，需要在 Stash 策略页将 `Proxy` **手动切换**到 `Auto`、`Fallback` 或 `ALL`（并对 ALL 选择真实节点）。已安装的旧配置可能保留之前的策略选择，更新后也要手动核对。故意选择 Auto/Fallback 且订阅为空的情况，仍不能保证阻断。

Auto、Fallback、ALL 中的 `REJECT` 仅为尚未配置节点池时的占位。Stash 官方说明空远程代理集可能以 DIRECT 替代，因此这里**不宣称空订阅时一定阻断**；必须按真机验收步骤分别测试空列表、下载失败和旧缓存场景。正常使用前应确认 provider 实际包含节点，并在 ALL 中明确选择可用节点。

## 规则与策略

- 以 LoonKit 43 份正式源文件的 **196,561** 条匹配器为基准，经[明确列出的本地修正](./build/adjustments.json)生成 **54 个 Stash 原生规则集**：43 domain、7 ipcidr、4 classical ASN，共 **196,570** 条文件匹配器；另内嵌 **133** 条私网匹配器，合计 **55** 个 provider。
- 保留原有 39 个策略组，另新增 ALL 全量节点池（共 **40** 组）。保留策略首选项及 IP 子集 `no-resolve`；内网、GitHub Raw 和 Steam 国内 CDN 的优先级修正见[路由说明](./docs/ROUTING.md)。
- AdBlockBalanced **76,903** 条、ChinaDirect **114,705** 条按域名/IP 类型拆分；不把大型规则直接作为顺序匹配的 classical。
- 使用 **Stash 自身的 Fake-IP + AliDNS DoH**。上游 DNS 与代理节点域名解析采用独立的 DNS 配置；不照搬 Loon 的 `real-ip` / `hijack-dns` 等指令，且 **DoH 加密不等于 DNS 一定经代理**。
- 原 Loon 专用插件/脚本不冒充 Stash 兼容组件。

## DNS 保护边界与 Stash 原生配置

- `dns.default-nameserver: https://223.5.5.5/dns-query`：使用 **IP 地址直连的加密 DoH** 解析 DoH 服务器的主机名，避免原先 `223.5.5.5` / `223.6.6.6` 普通 UDP DNS 的明文引导查询。CI 会测试该 IPv4 HTTPS 端点的证书和 RFC8484 应答。
- `dns.nameserver: https://dns.alidns.com/dns-query`：Stash 的主 DNS 上游，默认**直连 DoH**，不是自动走代理。外部 DoH 服务商可看到需要真实解析的查询；Fake-IP 只能减少部分代理域名的本地 DNS 查询。
- `dns.proxy-server-nameserver`：专门解析节点服务器域名，避免递归 DNS；同样采用加密 DoH，节点服务器名仍可能被 DNS 服务商看到。
- 私有域名通过内嵌 `Private-local` 集合和限定范围的 `nameserver-policy` 使用 `system`，便于访问路由器、NAS 和内网服务；这部分查询可能使用局域网明文 DNS，公共域名仍交给 DoH。私有域名和 LAN 地址另有前置 `DIRECT` 规则；`fake-ip-filter` 本身不负责直连。企业自定义域名需自行补充对应内网 DNS policy。私网名单来自固定的 V2Fly `data/private`，源码和 SHA256 见 [私网源锁](./build/private-domains-lock.json)；精确域名、后缀和单标签 DNS 名称均内嵌配置，不再首次下载 GeoSite。
- `dns.fake-ip-filter`：仅保留私有域名、局域网、网络探测及游戏的有限兼容例外。**已移除 STUN 的 Real-IP 例外**，避免应用从这些域名直接获取真实目标地址；此设置本身不能阻止通过 IP 字面量访问的 WebRTC。此前还移除了 `+.apple.com`、`+.icloud.com` 大范围例外。
- `dns.follow-rule: false`：显式保留 Stash 官方默认行为，不把所有 DNS 强行代理（可能导致代理节点域名递归解析、CDN 延迟）。如需海外 DNS 全程代理，须根据自己的节点 IP/域名及 `proxy-server-nameserver` 单独设计，不能简单打开开关。
- **不保证绝对无 DNS 泄漏**：其他 App 的内置 DoH、直连路径、VPN/Network Extension 的接管情况都需要设备上验证；建议在 Stash 连接后检查 DNS 测试和请求记录。

Stash 官方参考：[DNS 服务](https://stash.wiki/features/dns-server) · [策略组](https://stash.wiki/proxy-protocols/proxy-groups) · [高效配置](https://stash.wiki/faq/effective-stash)。

## WebRTC 公网 IPv4 / IPv6 泄露缓解（规则与设备设置共同生效）

三份配置在普通内网和国内直连规则之前添加 `PROTOCOL,STUN,REJECT`，并封锁 3478/3479、5349/5350、19302–19309 目的端口（TCP/UDP），避免常见 STUN/TURN 经直连出口查询公网地址。还移除了 `fake-ip-filter` 中的 STUN 特例。这些规则**只处理进入 Stash 网络引擎的连接**；会降低 WebRTC 音视频、屏幕共享或游戏语音的可用性，部分连接可能失败。未知端口由 STUN 协议识别补足，但不能覆盖加密 TURN/TLS、非 STUN ICE 候选、绕过 Tunnel 的连接或浏览器直接暴露的网卡 IP。

**必须在设备上额外检查**：

1. 在 Stash 启用系统 Tunnel/VPN，而非仅使用浏览器 HTTP 系统代理；有原生 IPv6 的网络还需到 **Stash → 网络设置 → 启用 Tunnel IPv6 路由**。官方说明默认 Tunnel 只启用 IPv4。没有 IPv6 路由的环境需要单独验证兼容性，不能只依靠 YAML 的 `ipv6: false` / `dns.ipv6: false`，那两个选项仅影响 Stash 自身连接与 DNS/AAAA，不会移除浏览器从网卡收集的 IPv6 地址。
2. **浏览器层阻断非代理 ICE**：桌面 Chromium/Chrome 可由受支持的策略或设置将 `WebRtcIPHandling` 设为 `disable_non_proxied_udp`；Firefox 如可接受网站音视频功能失效，可在 `about:config` 将 `media.peerconnection.enabled` 设为 `false`。其他浏览器需核实各自的 WebRTC/IP 隐私能力；Stash 配置无法替浏览器修改这些设置。
3. 在**同一网络**分别记录关闭与开启 Stash 时 [BrowserLeaks WebRTC](https://browserleaks.com/webrtc) 的 `host` / `srflx` / `relay` 候选和 IPv4/IPv6 地址；与 HTTP 出口及真实运营商地址比较。启用后不得看到真实公网 IPv4 或全局 IPv6；若看到 `host` 全局 IPv6，即使 STUN 已被阻断也**仍是浏览器层暴露**。`.local` mDNS 候选或 RFC1918 私网地址不等同于公网 IP 泄漏。还应在 Wi-Fi、蜂窝网络切换后重测。

在 Stash 的连接记录中确认目的端口命中 `REJECT`，以及使用 [HTTP API /rules/match](https://stash.wiki/features/http-api) 分别查询 `network=udp&port=3478`、`network=udp&port=19302` 的出口；`PROTOCOL,STUN` 需要真 UDP 报文才能识别，静态 /rules/match 查询并不能模拟协议解析。**这是一项针对受接管流量的防护措施，而非在任意浏览器、系统与 IPv6 网络下零泄漏的保证。**

规则类型：[Stash 官方 PROTOCOL / DST-PORT](https://stash.wiki/rules/rule-types) · [Stash IPv6 兼容性](https://stash.wiki/faq/ipv6-compatible) · [Chrome WebRTC IP Handling](https://support.google.com/chrome/a/answer/2657289?hl=en)。

## v0.1.4：广告修正、内嵌私网与不可变规则

**在线配置（推荐）：**

```text
https://raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.yaml
```

54 个规则 URL 固定到单独发布的规则快照 commit `f4feec81dfc9bde9824d297b6959fa977d5dc39b`，而不是可变 `main`。所有规则使用 **`path: ./rules/v0.1.4/<文件名>`**，Stash 会先读本地缓存，后台更新成功后覆写缓存。这避免了不同发布版本共享缓存路径，也降低重启时的网络依赖；**首次无缓存、GitHub Raw 被屏蔽时仍需要人工离线安装**。更新发布应先在仓库提交并验证规则，再发布一份指向该不可变提交的新配置；不能一次提交新规则并让配置引用未出现的版本。

**离线资源包（GitHub Actions 产物）：** 在 [CI 工作流](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) 最新成功的 `main` 运行记录中下载 `StashKit-v0.1.4-offline`；包含 `StashKit-Local.yaml`、54 份规则文件和 `SHA256SUMS.txt`。也可自行运行 `python scripts/build_offline_bundle.py` 制作同一 ZIP。

离线配置：[StashKit-Local.yaml](./StashKit-Local.yaml)（**文件规则仅引用本地 `path`，私网规则内嵌；不进行远程规则下载**）。重要：**Stash 不会因为打开 ZIP 就自动将规则文件复制进其管理的资源目录。** 必须先把 ZIP 内 `rules/v0.1.4/*.txt` 按相同相对路径放入 Stash 的受管理规则资源目录，确认 54 个文件 provider 和内嵌私网 provider 都已加载，才可启用本地配置。路径管理需按 Stash 实际版本的界面和 iCloud 目录操作；若设备不允许手动写入资源目录，不要把离线方式当成一键方案。参见 [Stash 官方 rule-provider 缓存说明](https://stash.wiki/rules/rule-set)。

**严格 DNS 隐私配置（直接导入可选）：**

```text
https://raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit-Privacy.yaml
```

[StashKit-Privacy.yaml](./StashKit-Privacy.yaml) 直接开启 `dns.follow-rule: true`，并把 `dns.alidns.com` 的 DoH 请求优先交给 Proxy。与普通配置相比，**54 份文件规则、1 个内嵌私网集合和 40 个策略组一致**，但必须先添加并选定可用节点，否则 DNS 可能失败。此配置不是全设备防泄漏保证：节点 DNS bootstrap 和私有 LAN DNS 仍通过独立直连链路。

**DNS 隐私模式（覆写现有普通配置，可选）：** 配好真实节点、让 `Proxy` 组实际使用节点后，启用 [DNS 隐私覆写](./overrides/dns-privacy.stoverride.example)，另存为 `.stoverride`。它将 `dns.follow-rule` 设为 `true`，并将 `dns.alidns.com` 的 DoH 连接先于国内直连规则交给 `Proxy`。如果节点失效、尚未选节点或网络阻断，该模式可能导致**DNS 解析失败或变慢**；故不作为通用默认值。代理节点自身的加密 DNS bootstrap、节点域名解析仍走独立直连 DoH；内网 `system` DNS 仍会经局域网链路。此模式也不能保证设备上所有程序的 DNS 都被代理。

**策略组图标（独立托管）：** [icons/](./icons/) 中保留 38 张原始 LoonKit PNG，更新 HBO 图标并为 ALL 新增独立图标，共 40 张。普通、严格 DNS 和本地规则配置均从 StashKit 固定提交 `3778671c7d4141ac49d734a8dfd45452a5147949` 加载图标；不依赖旧 LoonKit 仓库。若手机仍显示缓存图标，请更新或重新导入配置。CI 校验 PNG Git blob 与远程 URL 的字节一致性；离线状态下图标可能暂不显示（不影响规则）。

广告规则补齐 Google Ads / DoubleClick / Analytics 的常用域名及 `-cn` 变体，并让已有 Copilot 遥测拦截规则优先生效。`AdBlock` 改选 `DIRECT` 会直接放行已命中的请求，不会继续后续服务分流；误拦请按域名添加指向正确服务组的精确例外。共享域名的策略范围见 [路由说明](./docs/ROUTING.md)。

## 自动校验

[GitHub Actions](./.github/workflows/ci.yml) 校验：固定上游及本地修正、源 SHA256、集合内重复项、54 个引用地址、策略名称、匹配顺序及 YAML 结构；另运行离线路由、策略引用环、字段/类型和 DNS 异常应答回归测试。配置校验器只覆盖本项目使用的 Stash 字段，采用新功能时需同步扩展校验器，不能将其当成全部 Stash 功能的通用 schema。CI 还会真实探测 DoH bootstrap 的证书身份，以及完整的成功 DNS 应答；PR 检查候选提交的全部 54 个远程文件，主分支检查生产地址，并比对字节，包括两个大型文件。

为保证可复现，源版本固定在 [LoonKit commit 5f272104](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9)，防止上游改动自动变更生产策略。手动验证：

```sh
git clone https://github.com/YohakuSama/stashkit.git
cd stashkit
git clone https://github.com/YohakuSama/loonkit.git upstream/loonkit
git -C upstream/loonkit checkout 5f272104fc1207612c1cbd18f3e19d861d459ed9
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/verify.py
python scripts/check_remote.py
python scripts/build_offline_bundle.py --check
```

生成新规则：`python scripts/build_rules.py`；仅检查可复现性：`python scripts/build_rules.py --check`。生成器先核对[源锁](./build/source-lock.json)、[冻结清单](./build/release_manifest.json)、全部源 SHA256、规则数量和遗留文件，再暂存输出并逐文件原子替换。输入校验失败不会部分改写规则。更新固定基准、调整清单及主配置前必须审查变更，不能自动替换为 beta 候选。

**验证边界**：静态规则、配置语法和远程 HTTP 文件校验，不能替代 Stash iOS/macOS 真机导入、DNS、规则更新、性能、广告和流媒体解锁验收。

## 许可

遵循 [GPL-2.0-only](./LICENSE)，保留 [第三方声明](./docs/THIRD_PARTY_NOTICES.md) 及 LoonKit 规则来源。禁止提交私人订阅 URL 或节点凭据。
