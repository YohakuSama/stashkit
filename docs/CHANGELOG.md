# 变更记录

## 未发布 · 精简公开配置入口

- 删除独立 Privacy、Local YAML 及对应的 ALL 派生版本。日常使用统一从 `StashKit.yaml` 导入。
- DNS 隐私继续通过现有 `overrides/dns-privacy.stoverride.example` 启用，不改变主配置的 DNS 和路由规则。
- 离线 ZIP 仍按需生成 `StashKit-Local.yaml` 和 55 份规则资源，不再在仓库根目录维护该文件。
- 生成器仅保留正式默认模板；同步精简校验、测试与当前文档，不影响历史发布资产。

## v0.1.23 · 同步 LoonKit v7.0.16 Apple Intelligence、Siri 与 Stripe 分流

- Apple 增加三个私有云计算精确主机，保留既有 Siri 的 Apple 后缀覆盖，并移除四条被上级域名覆盖的冗余规则。
- AppleOTA、Apple 两份远程规则提前到 Cloudflare 前；普通 Cloudflare 业务仍使用 Cloudflare 策略组。
- Stripe 的 `stripe.com` 和 `stripe.network` 加入现有 SharedInfrastructure / Proxy 远程规则。
- 原有 40 个策略组、55 份远程文件规则、DNS 和 Final 保持不变。无需添加本地域名或新策略组。
- 同步正式 Stash、Privacy、Local、ALL 与 Preview 配置，远程链接继续固定到不可变 Git 提交。

## v0.1.22 · 同步 LoonKit v7.0.15 分流

- 夸克网盘继续直连，维基百科和多邻国国际站继续走代理。
- 新域名已合并到现有的国内补充和通用代理规则库，仍为 55 份远程规则，不新增策略组或本地域名规则。
- 其他规则、节点和 DNS 设置保持原样。更新配置后刷新远程规则。


## v0.1.21 — 取消独立自建模板，统一订阅入口

- 移除公开 `StashKit-SelfHosted.yaml`、专用生成逻辑及过时测试，推荐使用 `StashKit.yaml` 绑定私人 Clash/Stash YAML 订阅。
- 保留通用高级节点生成器，个人本地可使用 flat 模式显式展开节点，但不再发布独立自建入口。
- 原 40 个策略组、55 份远程规则、DNS 及节点 Provider 绑定保持不变；添加静态节点回归测试，VPN 状态仍需真机验收。
- 公开仓库不存储私人节点连接信息、密码或 Token。

## v0.1.20 — 自建版禁用 include-all，恢复明确策略选择

- 以用户确认正常的 v0.1.13 `use: [Airport]` 作为对照，识别后续单文件自建模板 `include-all` 与固定 `proxies` 混用为主要兼容性差异；v0.1.19 的排版调整没有消除实际故障。
- 自建公开模板现仅含一个不带真实凭据的 `SelfHosted` 占位节点；38 个需节点组明确引用它，不再使用 `include-all`。单节点可保持这个名称并更换完整连接参数。
- 多个或自定义名称的节点通过通用 `--layout flat --nodes-from` 从用户个人 YAML 自动展开 40 个策略组：Proxy 为 Auto → Fallback → REJECT → 实际节点。**公共仓库不硬编码任何用户的节点名或密钥**，静态节点变化后需重新生成。
- 保留 v0.1.19 的订阅版和 55 份远程规则资源，Crypto、AdBlock、DNS、LoonKit 40 组次序不变。添加回归断言；**CI 静态通过不代表 VPN 真机已验证**。


## v0.1.19 — 还原策略组可读结构与选择顺序

- 针对 VPN 启动后 `Proxy` 仅显示节点而不显示 Auto / Fallback / REJECT 的反馈，恢复 v0.1.16 使用的多行策略组 YAML，确保 `proxies` 固定选项写在 `use` / `include-all` 动态节点引用前。
- 将高级原生配置生成器的 `Proxy` 顺序从 Auto → Fallback → 节点 → REJECT 修正为 **Auto → Fallback → REJECT → 节点**，同时保留原有 40 组、远程节点 Provider 更新与 55 份远程规则集。
- 增加对源配置顺序、生成器和 Stash 运行时成员的检查：若启动后固定选项丢失或被挪到节点下方，运行时验收应失败并给出明确原因。
- **静态验证只能确认配置与测试模型**，v0.1.16 和 v0.1.18 在解析后策略组数据原本相同；此修改是对排序和可读格式的保守兼容调整，仍需在受影响设备上复测启动前后成员列表，不能宣称已证明 Stash 实际行为改变。


## v0.1.18 — 独立同步 LoonKit v7.0.13 Crypto 与文档

- 将 Crypto 从固定的 29 条后缀扩充为 **219 条 Stash 原生 domain 匹配器**（保留原 29 个根域），按完整 Git 提交引用独立远程资源，升级时不重写旧的 54 份冻结规则。
- 调整 AdBlock 与 Crypto 的顺序，保留广告优先；为旧 AdBlock 快照中误拦的 Coincheck 主页增加**一条精确域名例外**，其余子域仍受广告规则处理。
- 在线配置与所有衍生 / ALL / Preview 文件统一更新，离线包使用独立版本缓存目录；新增 LoonKit v7.0.13 源锁、固定 SHA256 与路由回归。
- README 参考 LoonKit 的信息架构重新整理：响应式标题、清晰的订阅/自建下载入口、首次导入、远程规则原理、常见问题和文档导航。
- [发布说明](./RELEASE_NOTES_v0.1.18.md)；**CI 静态验证不能替代 Stash 真机验收**。


## v0.1.17 — 主配置精简与 Crypto 远程化

- 正式主 YAML 从 983 行缩减至约 280 行：40 个策略组和 54 个远程 Provider 以紧凑 Stash 原生 YAML 编写，不减少分流功能。
- 将 29 条 Crypto 后缀规则解耦为固定提交的独立远程 `Crypto-domain`，使用 `RULE-SET,Crypto-domain,Crypto` 保持原匹配优先级。
- 133 条 Private-local 规则保持内嵌且完全不变，仅缩短排版，避免本地 DNS / 私网冷启动依赖远程下载。
- 离线包加入第 55 份 Crypto 文件，兼容 ALL 和 Preview 仍保持之前的布局；更新验证、路由哨兵、不可变 URL 字节检查。


## v0.1.16 — 修复自建多个节点不显示

- 修复 v0.1.15 自建模板只引用固定 SelfHosted 节点、额外粘贴的节点不出现在策略组的问题。
- 38 个需节点的策略组改用 Stash 支持的 include-all: true，动态引用顶层 proxies 列表中任意数量、任意名称的静态节点。保留 Proxy/Auto/Fallback 及 40 个策略组的原有固定选项；AdBlock/Final 不变。
- README 增加三节点示例、单一顶层 proxies 键与名称去重说明，以及导入新版 YAML / 启用配置的检查方法。
- 添加多节点引用结构回归，不改动订阅版 DNS、业务规则、图标和固定规则资源。


## v0.1.15 — 订阅和自建节点双配置

- README 改为两个主入口，直观说明机场订阅修改 proxy-providers.Airport.url、自建修改顶层 proxies.SelfHosted 节点。
- 新增单文件 StashKit-SelfHosted.yaml：静态单节点供 38 个需节点的策略组直接引用，保留 Auto/Fallback 与 40 个原生组，不需要订阅或另一个 Provider 文件。
- 订阅入口 StashKit-Subscription.yaml 保持与 StashKit.yaml 一致；其余派生配置只变更版本头，不修改原有路由规则、DNS、Crypto、图标或固定规则资源。
- 补充自建模板的一致性及敏感占位字段测试，发布说明见[RELEASE_NOTES_v0.1.15](./RELEASE_NOTES_v0.1.15.md)。


## v0.1.14 — 同步 LoonKit v7.0.12 Crypto 策略

- 新增 Crypto 代理策略组，39 → 40 个正式组；与 Paypal 共同移到基础平台策略后、流媒体前，保留 Proxy / Auto / Fallback 和同层动态订阅节点，不提供 DIRECT。
- 将 LoonKit 的 29 条加密货币域名后缀规则加入 Stash 原生配置，放在国内直连/广告远程资源之前，确保相关交易平台和钱包域名优先进入 Crypto。
- 原样自托管 Crypto BTC 专属图标，全部 40 张图标重新固定到不可变提交；同步九套正式、兼容和预览配置。
- 策略及本地规则校验锁定到 LoonKit v7.0.12；43 份未变远程规则继续使用原 v7.0.10 / StashKit v0.1.4 冻结资源，以免无必要地重置缓存。参见[发布说明](./RELEASE_NOTES_v0.1.14.md)。


## v0.1.13 — 正式 YAML 直接填写机场订阅

- `StashKit.yaml`、Privacy 与 Local 正式配置统一声明 `proxy-providers.Airport`，通过单个 YAML URL 填入私人 Clash/Stash 订阅，无需可视化编辑或 Python。
- 所有 37 个需节点的策略组均显式使用 `use: [Airport]`，保留原有 39 个策略组、Auto/Fallback、业务 DIRECT 顺序、DNS、规则与固定图标。
- `StashKit-Subscription.yaml` 保留为正式版的兼容别名；高级生成器自动剔除公开的无效示例 Provider，再绑定真实多来源节点。
- 公开仓库仅含无效的 `example.invalid` 占位 URL；实际订阅可能含 Token，应仅保存在本地，不要推送到 GitHub。Stash 真机加载与断线行为仍需设备检查。

## v0.1.12 — 默认无 ALL，保留订阅自动更新

- 三份正式模板恢复 Loon 对应的 39 个组，去除 ALL/Manual 中间入口；不再依赖固定 personal 名称或不存在的本地文件。
- API 与命令行默认 native，直接将真实 Provider/use-url 绑定到 Proxy、Auto、Fallback 及业务组。保留来源名称、刷新间隔、认证头、缓存和过滤条件，节点变化不需要重新生成静态列表。
- 公开模板以空 use 明确表示尚未绑定私人来源；首次必须生成完整配置。flat 改为显式静态快照选项，旧 ALL 改为显式兼容选项。
- 运行时审计增加逐业务组的当前节点集合检查，识别 Auto 正常但同层节点缺失、订阅更新后选项不同步和残留中间组。
- 回归覆盖默认 API/CLI、三种模板、任意名称多 Provider、use-url、刷新信息保留和运行时节点更新；规则、DNS、防护与图标资产未调整。


## v0.1.11 — 修复节点来源与 Loon 同层生成

- 公开版移除固定 `personal` 本地文件依赖，恢复当前配置中的任意节点/Provider 自动收集；Auto/Fallback/ALL 节点池不再包含 REJECT。
- 私有生成器默认 `flat`，读取本地节点、相对路径 Provider 或直接下载 HTTPS 订阅，展开为 39 个 Loon 对应策略组；保留服务 DIRECT 默认、节点顺序和自动策略参数。
- 空源、过滤后为空、无效节点、重名冲突和下载失败均停止；私有输出以 0600 权限原子替换，错误信息不回显凭据。
- 所有派生配置、兼容链接及参考预览由主配置生成；运行时审计检查所有策略组及三个节点池，识别缺少 Auto/Fallback 和 DIRECT 替代。
- Stash 对节点共享测速结果，不能直接照搬 Loon 的组级 `max-timeout`；保留来源的测速参数，缺省使用 Bing / 5 秒。订阅节点变化后需重新生成 flat 配置。


## v0.1.10 — 2026-10-29

- 删除此前擅自增加的 `Manual` 隐藏策略组，正式配置严格恢复 LoonKit 的 39 个策略组及原始顺序；不需要命名或重配订阅。
- `Proxy` 明确选择 `Auto` / `Fallback`，通过 Stash `include-all: true`、`filter: '.*'` 同时自动收集具体节点；34 个服务选择组也保留自身的明确策略选项并动态收集节点，按 LoonKit 的 `ALL_Filter` 思路直接实现。
- 不新增验证工具或试验配置；仅调整既有一致性检查。三套配置的 DNS、前置 STUN、规则与 v0.1.4 快照保持不变。参见[发布说明](./RELEASE_NOTES_v0.1.10.md)。
- **发布不等于 Stash iOS 界面验收**：此前 iOS 截图存在显示问题，本次以同层组合结构替换折中方案，效果仍须设备实际查看。

## v0.1.9 — 2026-10-29

- 修复 `Proxy` 无法直接选择 `Auto` / `Fallback` 的可用性问题：`Proxy` 使用明确的 `REJECT`、`Auto`、`Fallback`、`Manual` 选项，不再混用 `include-all`。
- 新增隐藏的 `Manual` 节点池自动收集现有订阅，避免强制设置具名 Provider；手动选节点需进入 `Manual` 一层。保留 39 个可见服务/策略组，隐藏辅助组不构成公开的重复 `ALL` 组。
- 重新验证组引用、图标复用、三套配置派生以及使用显式节点的 LoonKit 个人配置生成器。DNS、WebRTC、路由、规则快照不变。参见[发布说明](./RELEASE_NOTES_v0.1.9.md)。
- 这是兼容 Stash 当前 UI 的结构性折中，不等于 LoonKit 在同一选择列表中同时显示自动策略与全部节点的完全一致体验；真机仍需确认。

## v0.1.8 — 2026-10-29

- 修复 Stash 实际界面中服务策略组只显示订阅节点、无法选择 `Auto`/`Fallback` 的问题；`ChatGPT` 等服务组改为明确显示 `Proxy`、`Auto`、`Fallback` 候选。
- 只有 `Proxy`、`Auto`、`Fallback` 三个节点池启用 `include-all`。服务组不再重复列出节点，手动节点通过 `Proxy` 共享；保持 39 个策略组和原有服务分流顺序。
- 补充防止混用动态节点池和嵌套策略组的回归约束；旧节点选项升级后应重新确认。
- 未修改 DNS、WebRTC、图标、代理订阅、规则集及固定快照。详见[发布说明](./RELEASE_NOTES_v0.1.8.md)。

## v0.1.7 — 2026-10-29

- 按固定 LoonKit 的 `ALL_Filter` 语义，将 `Proxy` 与 34 个服务策略组的节点选择直接映射为 Stash `include-all: true`，而不是创建独立 `ALL` 策略组。
- 移除重复的 `ALL` 组、全部对其的配置引用与不再使用的图标，策略组回到 39 个；保留 `Proxy` 的默认 `REJECT`、`Auto` 和 `Fallback`。
- 新增逐组对照 LoonKit 正式配置的回归测试，检查名称、顺序、策略类型、候选项和节点池行为。图标清单及 CI 同步校验 39 个有效策略组。
- DNS、WebRTC、规则快照、服务分流规则和节点订阅保持不变。升级前若手动选择过 `ALL`，更新后应重新确认各策略组的当前选择。

## v0.1.6 — 2026-10-29

- 在 `Proxy` 策略组开启 `include-all: true`，允许直接选择本地和订阅节点，无需先进入 `ALL`。保留 `Auto`、`Fallback`、`ALL` 与默认的 `REJECT` 选项。
- 为直接选节点增加回归断言，所有三套配置同步生成。节点池为空时仍需检查实际出口，不能把 `REJECT` 占位视为内核级断网保护。
- 规则资源快照、DNS 配置、WebRTC 拦截、分流规则与策略组数量保持不变。详见[发布说明](./RELEASE_NOTES_v0.1.6.md)。

## v0.1.5 — 2026-10-29

- 统一配置版本元数据，将配置版本 `v0.1.5` 与不变的规则资源快照版本 `v0.1.4` 分开维护，不刷新原有规则下载地址和缓存目录。
- 主配置、Privacy/Local 派生配置、离线 ZIP、校验器、测试及 CI 使用同一份发布锁；发布前检查配置一致性和规则快照。
- 新增正式 Release 流程：主分支全部验证通过后，按锁定的配置版本创建版本标签和上传离线 ZIP；重复运行不会覆盖已有 Release。
- WebRTC 缓解、DNS 配置、节点选择、路由集合、策略顺序和图标未改动，见[发布说明](./RELEASE_NOTES_v0.1.5.md)。

## 配置派生与文档结构优化 — 2026-10-29

- 以 `StashKit.yaml` 为唯一手工维护的主配置，新增 `scripts/build_profiles.py` 统一派生 Privacy/Local，并在 CI 中强制校验字节一致性。
- 离线 ZIP 生成复用派生配置脚本，补充一致性、缺失字段和 YAML 英文注释测试。
- 按 LoonKit 的使用导向精简 README、架构文档及配置注释；不修改 DNS、WebRTC、规则列表、策略选项或锁定的远程资源。


## WebRTC IPv4/IPv6 泄露缓解补丁 — 2026-10-29

- 三套配置在 LAN/CN 直连之前阻止 STUN 协议及常用 STUN/TURN 目的端口，删除 STUN 的 Fake-IP Real-IP 例外；显式限制到受 Stash Tunnel 接管的流量。
- 扩展配置校验器对 `PROTOCOL,STUN` 与 `DST-PORT` 的校验，并添加三套配置的顺序和错误字段回归测试。
- 补充启用 Tunnel IPv6 路由、浏览器 WebRTC 限制、对照真实公网地址与 ICE 候选的真机验收说明；提醒实时音视频可能受影响，无法静态保证绝对无泄露。

## v0.1.4 — 2026-10-29

- 补齐 8 个 Google 广告与统计域名后缀（含 -cn 变体），文件匹配器增至 196,570 条；单独发布规则快照后切换不可变 pin 和缓存目录。
- 移除 Copilot 遥测域名的前置 AI 覆盖，让已有 AdBlock 规则生效；其他已验证的服务组与共享域名归属保留。
- 将固定 V2Fly private 名单的 133 条规则内嵌到三套配置，供路由、系统 DNS policy 和 Fake-IP 例外共用；无需首次下载 GeoSite，共 54 个文件 provider 加 1 个内嵌 provider。
- 真机审计校验 provider 名称及条目数、规则总量、递归策略选择和哨兵路由，拒绝空规则、意外直连、循环选择和错误命中；不输出个人节点名。
- 增强域名、ASN、正则、DNS 集合引用及 MATCH 位置校验，补充广告、私网和审计失败场景测试。

## 策略组图标更新 — 2026-10-29

- 为 ALL 新增独立的 512 × 512 PNG 字标图标，不再复用 Proxy。
- 修复 HBO 图标的清晰度；其余 38 张图标保持原样。
- 同步三份配置、不可变图标提交引用、图标锁及 40 张图标的 CI 校验。

## v0.1.3 图标恢复补丁 — 2026-10-29

- 原版 39 张 PNG 逐字节复制到 StashKit 自己的 `icons/`，不再使用旧 LoonKit 的外部图标链接。
- 普通、严格 DNS、本地规则版的 40 个策略组全部恢复自托管图标，ALL 复用 Proxy 图标。
- 增加校验图片 Git blob、PNG 文件头、策略组引用和 GitHub Raw 下载的回归测试；规则、DNS、节点配置不变。

## v0.1.3 — 2026-10-29

- 54 个规则订阅 URL 固定到不可变 Git commit；加入版本缓存 path，防止跨版本混用并复用本地规则。
- 提供完整路径本地版 `StashKit-Local.yaml`、确定性离线 ZIP 及 CI 工作流产物；首次离线安装仍需手动放入 Stash 受管资源目录，不宣称一键导入。
- 加入独立 `StashKit-Privacy.yaml` 及可选 DNS 隐私覆写，按 Stash 原生规则转发 AliDNS DoH，明确适用条件与残余直连。
- 移除对 LoonKit 固定 commit 图标的运行时依赖，回退到 Stash 默认图标。

## v0.1.2 — 2026-10-29

- Proxy 策略组默认改为 `REJECT`，避免空代理订阅被 Stash 替换为 `DIRECT` 后通过 Auto/Fallback 意外直连。必须在加入可用节点后手动选择 Proxy 出口；旧配置要核对已保存的策略。
- CI 增加默认 Proxy 安全出口回归测试，明确 Auto/Fallback 用户强制选择且空订阅时仍可能存在直连风险。

## v0.1.1 — 2026-10-29

- 私有域名使用限定的系统 DNS policy；内网域名和地址在公共分流之前直连。
- 测速参数改为 provider 级 benchmark-url / benchmark-timeout。
- GitHub 组控制 Raw 域名；SteamCN 优先接管已有的国内 CDN 精确域名。
- 動畫瘋的 HiNet 范围缩小到两个已知 CDN，移除通用 DigiCert 范围。
- 配置校验增加字段类型、策略引用环和覆写示例检查；DNS 探测校验完整成功应答。
- 源清单及输入摘要固定在本仓库，规则生成可逐字节复现；失败输入在写入前被拒绝。
- 补齐原始许可文本、历史来源材料和有效链接，注明最低 Stash 版本与真机验证边界。

上述更改不代表已经完成流媒体解锁、空订阅阻断或真机性能验收，验收方法见[验证步骤](./VALIDATION.md)。
