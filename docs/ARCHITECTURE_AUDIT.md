# StashKit 架构复审与风险记录（2026-10-29）

> 基准：StashKit v0.1.2 候选、LoonKit v7.0.10 固定源。此文不是 Stash 官方核心的加载验收证书。

## 项目结构检查

| 层次 | 实现 | 核验 | 状态 |
| --- | --- | --- | --- |
| 配置入口 | `StashKit.yaml`，包含 DNS / 40 个策略组 / 54 个规则订阅 / 路由顺序 | Stash 官方配置字段对照 + 本仓库 schema | 静态检查通过，客户端加载待验 |
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

DNS 配置中 `follow-rule: false`：外部上游 DNS 查询默认由 Stash 直接送往 AliDNS 加密 DoH。证书测试证明测试环境里 HTTPS 端点可用，但**不能证明 iOS 全设备无 DNS 泄漏**。`nameserver-policy` 的私有域名使用 `system`，局域网查询可能是明文；代理节点域名经独立 DoH 解析，DoH 服务商仍能看到这些查询。应用自带 DoH、VPN 旁路、IPv6/UDP 实际行为需要设备验证。见[官方 DNS 文档](https://stash.wiki/features/dns-server)。

### A3 — 中：54 份远程资源的可达性、网络封锁与非原子更新

CI 检查 GitHub Raw 的 54 个 URL 均返回 200，并与本仓库文件逐字节一致，但这是 GitHub Actions 网络，不保证所有地区/运营商均能连接。Stash 规则集合有本地缓存和后台更新；**如果首次下载失败且没有缓存，规则可能未加载完整**。目前这些 URL 指向可变 `main`，54 份规则按各自周期更新，跨版本发布存在短暂的版本不一致窗口。后续适合引入版本化/不可变发布地址和分阶段上线，不应直接认定现有链路没有网络启动依赖。见[官方规则集文档](https://stash.wiki/rules/rule-set)。

### A4 — 中：交叉规则覆盖不等于可安全全局去重

每个源集合内、每个生成集合内均检查重复项。但跨集合存在有意的域名后缀覆盖。例如在对广告、国内、Google、Microsoft 等九个集合的抽样比较中，ChinaDirect 的某些广泛后缀会覆盖约 2,790 个广告集条目；**实际路由由规则顺序决定**，广告规则处于 ChinaDirect 之前，因此不能仅根据重复/包含关系删项。另有 Google 与 YouTube、Microsoft 与广告条目互相覆盖，参见[路由决策](./ROUTING.md)。上线前需针对重要服务做 Stash 真机匹配回归。

### A5 — 中：客户端版本和运行时资源预算

加密 DNS Bootstrap、独立节点解析和部分 DNS 集合功能要求 **Stash iOS/tvOS 3.6+ 或 macOS 4.3+**。约 19.7 万条匹配器虽使用优化后的 domain / ipcidr，但 iOS Network Extension 的实际峰值内存、缓存及重连表现不在静态 CI 覆盖范围。见[官方高效配置建议](https://stash.wiki/faq/effective-stash)。

### A6 — 低：图标仍依赖 LoonKit 固定 commit

主配置的 `icon:` 资源依然使用 LoonKit 不可变 commit 的图标 URLs。**规则和节点分流不依赖这些图标**，但如果原仓库资产被移除，图标可能无法加载。理想的独立发布应移入本仓库自托管，或显式保留这个只影响外观的可选依赖。

### A7 — 中：项目自建校验器不等于 Stash 内核

`scripts/validate_config.py` 是本项目使用字段的自建 schema；规则匹配离线测试只模拟部分规则类型。CI 没有运行 Stash 本机解析器、iOS Network Extension 或 macOS Stash 核心；**“CI 全绿”不能等价于“Stash 100% 可加载和所有分流正确”**。必须按照[设备验收矩阵](./VALIDATION.md)导入 App、检查 54 个 provider 状态并复核最终出口。

## 下一步设备验收重点

依次确认：首次导入 Proxy 选中 REJECT；导入节点后手动选用 Auto/ALL；空订阅和更新失败是否会直连；54 个规则集在 Stash 中真实加载；私有域名与公用域名 DNS 路径；重要广告/业务重叠域名的命中优先级；蜂窝网络/IPv6；高负载内存、重启及后台更新稳定性。

**结论**：代码结构和官方 YAML 语法整体合理，已发现的默认出口问题通过保守策略缓解，但目前不存在可支持“绝对没有任何问题”的真机证据。
