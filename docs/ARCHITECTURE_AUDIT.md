# StashKit 架构复审与风险记录（2026-10-29）

> 基准：StashKit v0.1.5、LoonKit v7.0.10 固定源。此文不是 Stash 官方核心的加载验收证书。

## 项目结构检查

| 层次 | 实现 | 核验 | 状态 |
| --- | --- | --- | --- |
| 配置入口 | `StashKit.yaml`，包含 DNS / 40 个策略组 / 54 个文件规则订阅 / 1 个内嵌私网集合 / 路由顺序 | Stash 官方配置字段对照 + 本仓库 schema | 静态检查通过，客户端加载待验 |
| 输入 | `build/source-lock.json`、冻结的 `release_manifest.json`、`upstream/loonkit` 固定 commit | SHA256、路径保护、源数量 | 自动测试 |
| 转换 | `scripts/rule_sources.py`、`scripts/build_rules.py` | 全量规则比较、调整清单、确定性生成 | 自动测试 |
| 资源 | `rules/*.txt`（43 domain / 7 ipcidr / 4 classical ASN） | 无集合内重复、内容和类型、54 个真实 URL 字节校验 | 自动测试 |
| 分流 | `rules:` 的显式覆盖 + 顺序匹配，`docs/ROUTING.md` | 独立路由示例和图引用环检测 | 离线回归通过，真机待验 |
| 策略 | Proxy / Auto / Fallback / ALL、服务策略组 | `include-all`、引用关系、默认策略 | **本次将 Proxy 默认改为 REJECT** |
| DNS | AliDNS DoH、加密 Bootstrap、独立节点 DNS、内网系统 DNS | RFC8484 HTTPS 探测 + DNS 配置字段 | 仅验证测试运行环境，设备待验 |
| 文档与许可 | README、许可证与第三方来源锁 | 链接和文件 SHA 校验 | 自动测试 |

## 重要风险与处置

### A1 — 高：空订阅下的意外直连（已缓解，仍需真机复核）

Stash 官方[远程代理集文档](https://stash.wiki/proxy-protocols/proxy-providers)明确说明空远程代理集可能被 `DIRECT` 代替；[策略组文档](https://stash.wiki/proxy-protocols/proxy-groups)说明 `include-all: true` 会接纳远程代理集。旧版默认 `Proxy → Auto` 存在无节点时意外直连的潜在路径。

v0.1.2 将 `Proxy` **第一个选项设为 `REJECT`**，并在 CI 固定这一安全默认值。用户成功载入个人节点后，需要手动把 Proxy 切换到 Auto / Fallback / ALL。**边界**：旧设备可能保留原有策略组选择；用户手动选择空的 Auto/Fallback 时依然不能保证阻断。这是保守默认，不是内核级 Kill Switch。

### A2 — 高：DNS 不等于全程经代理（已明确告知，真机待验）

普通配置 `follow-rule: false`：外部上游 DNS 查询默认由 Stash 直接送往 AliDNS 加密 DoH。证书测试证明测试环境里 HTTPS 端点可用，但**不能证明 iOS 全设备无 DNS 泄漏**。`nameserver-policy` 的私有域名使用 `system`，局域网查询可能是明文；代理节点域名经独立 DoH 解析，DoH 服务商仍能看到这些查询。新增可选 `overrides/dns-privacy.stoverride.example` 开启 `follow-rule: true`，并优先将 AliDNS DoH 主机路由到 Proxy。仅适合节点可用且接受 CDN/解析递归风险的用户；该模式仍无法代理节点域名解析、私有 LAN 系统 DNS 和 VPN 之外的请求。应用自带 DoH、VPN 旁路、IPv6/UDP 实际行为需要设备验证。见[官方 DNS 文档](https://stash.wiki/features/dns-server)。

### A3 — 中：54 份远程资源的可达性、网络封锁与非原子更新

CI 检查 GitHub Raw 的 54 个 URL 均返回 200，并与本仓库文件逐字节一致，但这是 GitHub Actions 网络，不保证所有地区/运营商均能连接。Stash 规则集合有本地缓存和后台更新；**如果首次下载失败且没有缓存，规则可能未加载完整**。v0.1.3 引入同一固定提交，v0.1.4 发布新规则快照并切换 pin，版本缓存目录改为 `./rules/v0.1.4/`，避免后续 main 规则更新引起同一配置内的跨版本不一致，并为已有缓存提供重启保护。首次无缓存仍依赖 GitHub 可达；另提供完整 ZIP 与 path-only 离线配置，**但需手工安装至 Stash 受管资源目录**。每次发新规则要先发布规则快照、再切换配置 pin。见[官方规则集文档](https://stash.wiki/rules/rule-set)。

### A4 — 中：交叉规则覆盖不等于可安全全局去重

每个源集合内、每个生成集合内均检查重复项。但跨集合存在有意的域名后缀覆盖。例如在对广告、国内、Google、Microsoft 等九个集合的抽样比较中，ChinaDirect 的某些广泛后缀会覆盖约 2,790 个广告集条目；**实际路由由规则顺序决定**，广告规则处于 ChinaDirect 之前，因此不能仅根据重复/包含关系删项。另有 Google 与 YouTube、Microsoft 与广告条目互相覆盖，参见[路由决策](./ROUTING.md)。上线前需针对重要服务做 Stash 真机匹配回归。

### A5 — 中：客户端版本和运行时资源预算

加密 DNS Bootstrap、独立节点解析和部分 DNS 集合功能要求 **Stash iOS/tvOS 3.6+ 或 macOS 4.3+**。约 19.7 万条匹配器虽使用优化后的 domain / ipcidr，但 iOS Network Extension 的实际峰值内存、缓存及重连表现不在静态 CI 覆盖范围。见[官方高效配置建议](https://stash.wiki/faq/effective-stash)。

### A6 — 低：图标网络可达性

**已修复：** 39 张原始图标 PNG 已逐字节迁移至 StashKit 自有仓库，全部 40 个策略组均使用本仓库固定提交的图标地址。ALL 和 HBO 使用独立更新图标。网络不可达时图标可能不显示，但分流不受影响；CI 校验字节完整性和 HTTPS 可达性。

### A7 — 中：项目自建校验器不等于 Stash 内核

`scripts/validate_config.py` 是本项目使用字段的自建 schema；规则匹配离线测试只模拟部分规则类型。CI 没有运行 Stash 本机解析器、iOS Network Extension 或 macOS Stash 核心；**“CI 全绿”不能等价于“Stash 100% 可加载和所有分流正确”**。必须按照[设备验收矩阵](./VALIDATION.md)导入 App、检查 54 个文件 provider 与内嵌私网 provider 状态并复核最终出口。

## 下一步设备验收重点

依次确认：首次导入 Proxy 选中 REJECT；导入节点后手动选用 Auto/ALL；空订阅和更新失败是否会直连；54 个文件规则集和内嵌私网集合在 Stash 中真实加载；私有域名与公用域名 DNS 路径；重要广告/业务重叠域名的命中优先级；蜂窝网络/IPv6；高负载内存、重启及后台更新稳定性。

**结论**：代码结构和官方 YAML 语法整体合理，已发现的默认出口问题通过保守策略缓解，但目前不存在可支持“绝对没有任何问题”的真机证据。

## v0.1.4 复审修正

Google 广告与统计域名已补入广告集；Copilot 遥测的前置 AI 例外已移除。私网名单固定源并内嵌三套配置，不再依赖首次下载 GeoSite。运行时审计会断言 provider 名称和条目数、规则总量、嵌套策略最终选择和路由哨兵；空规则、意外 DIRECT、循环选择及错误路由均有失败测试。共享服务域名仍按原有已验证策略处理，具体范围见路由文档。

## v0.1.5 STUN 防护与设备边界

三套配置首先拒绝被识别的 STUN，避免后续直连规则优先放行探测。校验器按 Stash 的 PROTOCOL 语法检查，离线回归覆盖 IPv4/IPv6 及普通业务不被此协议规则命中的情况。运行时审计验证 guard 已加载；它不产生真实 STUN 数据包。iPhone 的 Tunnel IPv6 路由仍需在 App 开启，浏览器候选暴露、系统旁路和通话兼容性仍需设备验收。
