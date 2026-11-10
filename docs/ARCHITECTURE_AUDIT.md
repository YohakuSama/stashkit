# StashKit 架构与验证边界

项目输出的是 Stash 原生配置和规则文件，不包含浏览器内核、代理节点或 Loon 插件。当前策略组与主要规则基准为固定的 [LoonKit v7.0.12](https://github.com/YohakuSama/loonkit/tree/edbfedad1b568578edc1a6dcebf422867a36a3ed)；43 份原有远程订阅资源继续按 v7.0.10 冻结。Crypto 规则独立按 [LoonKit v7.0.13](https://github.com/YohakuSama/loonkit/tree/66b01bffe8982d6a8153af7b03c897dc1bbab648) 更新，原快照不被覆盖。

自建版 StashKit-SelfHosted.yaml 是独立的静态多节点派生文件，顶层 proxies 可填写任意多个不同名称的本地节点；38 个需节点的策略组通过 include-all: true 自动引用所有本地节点，无需更新每个组的名称列表。其余规则、DNS、40 个策略组的默认固定选项保持一致，不依赖 Airport 订阅和额外本地 Provider 文件。该公开模板不含真实节点凭据，部署后需真机验收。

## 构建流程

| 层 | 输入与职责 | 输出 |
| --- | --- | --- |
| 固定来源 | `build/source-lock.json`、`build/release_manifest.json`、上游 SHA256 | 可审查的源版本 |
| 规则转换 | `scripts/rule_sources.py` 按类型转换，`build/adjustments.json` 记录额外改动 | `rules/*.txt` |
| 主配置 | `StashKit.yaml` 手工维护 DNS、策略组、规则顺序和 provider 引用 | 在线配置 |
| 派生配置 | `scripts/build_profiles.py` 从主配置分别生成 Privacy 和 Local | 两份派生 YAML |
| 离线包 | `scripts/build_offline_bundle.py` 复用 Local 生成器，连同固定规则打包 | ZIP 和 SHA256SUMS |
| 校验 | `scripts/validate_config.py`、`scripts/verify.py`、`tests/` | CI 静态断言 |
| 真机证据 | `scripts/stash_runtime_audit.py` 读取 Stash 控制器的规则、策略和 provider 状态 | 运行时诊断 |

主配置是**唯一手工维护的 YAML**；不要直接在 Privacy/Local 文件里修规则。运行 `python scripts/build_profiles.py --write` 后，`--check` 会要求两份生成文件与仓库内容逐字节一致。校验不会悄悄改写输出。

## 固定的行为与资源

- 54 个冻结文件规则 provider（43 domain、7 ipcidr、4 classical ASN），另有独立 Crypto-domain（domain，219 条，其中 1 条精确匹配）和 1 个内嵌 `Private-local`，合计 56 个 provider。
- 原上游 43 份输入经人工审查的 [adjustments.json](../build/adjustments.json) 转换。规则资源固定到 [release-lock.json](../build/release-lock.json) 指向的不可变提交，不跟随远程 `main`。
- 三份正式配置和默认 native 输出均保留 LoonKit 的 40 个策略组，无 ALL/Manual 中间组。正式 YAML 使用 `Airport` 具名 Provider 和无效占位 URL，可直接在本地改为私人订阅；高级生成器仍可将其替换为多 Provider/use-url 来源，保留 Stash 的后台节点更新，不下载成静态快照。旧 ALL 仅为显式兼容选项，flat 仅为静态快照选项。运行时审计逐组核对当前订阅节点，CI 不启动 Stash iOS，详见[订阅绑定说明](./NATIVE_PROVIDER_TRIAL.md)。
- STUN 和常用 TURN 端口拦截位于 LAN/CN 直连之前，所有三套配置保持一致。此次架构调整**不修改**这些网络规则。

## 测试与已知边界

| 检查范围 | 自动化能够验证 | 自动化不能证明 |
| --- | --- | --- |
| 配置 | 字段类型、引用、顺序、三套配置一致性 | 任意版本 Stash 的原生解析行为 |
| 规则 | 上游固定 SHA、生成字节、远程资源内容和缓存路径 | 首次下载失败后的每种设备状态 |
| DNS | 配置与上游 DoH 测试环境的响应 | 每台设备上所有 App 的 DNS 出口 |
| WebRTC | 拦截规则及其先后顺序 | 未接管的流量、设备 ICE 候选和真实公网泄露 |
| 节点 | 策略引用与运行时控制器返回的选择 | 空订阅、掉线时一定不会回退直连 |

普通配置的公共 DNS 是 AliDNS DoH，默认不强制走代理；Privacy 版启用 `follow-rule` 并前置 DoH 路由规则。节点 DNS 和局域网 `system` DNS 使用各自的解析路径。WebRTC 限制可能影响原生 App、网页的通话及游戏连接。IPv6 Tunnel 选项应按实际网络验证；`Auto` 已通过真实出口测试时不需要强制改为 Always。

CI 成功表示仓库生成与静态约束通过，不等于对所有设备、网络和服务的无故障保证。设备验收步骤和只读 HTTP API 审计见 [VALIDATION.md](./VALIDATION.md)，变更历史见 [CHANGELOG.md](./CHANGELOG.md)。

## v0.1.18 配置格式精简与新版 Crypto

正式主配置约 600 行，仍声明全部 40 个策略组和 55 个远程文件规则 Provider。传统多行 YAML 组 / Provider 映射改为 YAML Flow Mapping；Stash 解析后的策略名、顺序、图标、节点来源、规则先后关系没有改变。Private-local 本地规则保持原始 133 条，仅压缩到 YAML Flow Sequence，保留首次启动的私网与 DNS 保护。Crypto 219 条域名匹配在独立冻结文件中，以一个 `RULE-SET,Crypto-domain,Crypto` 路由，无需将每个域名写到主配置。旧 ALL 和 Preview 文件维持展开布局供兼容使用。

新版 Crypto 从 LoonKit v7.0.13 的固定 `.lsr` 转换为 Stash `behavior: domain` 文本资源，转换结果保存在 `rules/extra/Crypto.v7.0.13.domain.txt`，上游路径、提交、SHA256 和条目数登记在 [crypto-source-lock.json](../build/crypto-source-lock.json)。在线配置只含远程 Provider 引用，离线包单独收录文件。广告快照仍为原冻结版本；通过 `DOMAIN,coincheck.com,Crypto` 的单一精确例外避免旧广告规则误拦主页，再让广告规则优先于 Crypto 集合，不能将此例外扩大为整个 `coincheck.com` 后缀。

## v0.1.19 策略组显示回归与顺序

策略组从紧凑单行 YAML 映射恢复为多行字段，固定选项 `proxies` 写在动态节点 `use` / `include-all` 前。40 个策略组与规则内容不变，仍有 55 份远程文件规则和 133 条冷启动私网匹配器。高级原生生成器也将 `Proxy` 的 REJECT 选项排在节点列表之前。Stash 默认按配置顺序显示，用户可以在网络设置修改排序方式。

这次改动**不等同于证明 iOS Stash 的 VPN 启动状态下自动合并两类成员**。旧版本和新版本配置经 YAML 解析后的组数据相同，真正的回归判定需要对受影响设备分别在启动前、启动后查看 `Proxy` 的完整候选顺序，并运行 `scripts/stash_runtime_audit.py` 对照控制器的 `/proxies` 成员列表。如果仍只剩节点，记录 Stash 版本和运行时信息，不能只凭 CI 通过合并结论。
