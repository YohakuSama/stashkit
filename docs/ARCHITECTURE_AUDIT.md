# StashKit 架构与验证边界

项目输出的是 Stash 原生配置和规则文件，不包含浏览器内核、代理节点或 Loon 插件。当前规则基准为固定的 [LoonKit v7.0.10](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9)。

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

- 54 个文件规则 provider（43 domain、7 ipcidr、4 classical ASN），另有 1 个内嵌 `Private-local` provider。
- 原上游 43 份输入经人工审查的 [adjustments.json](../build/adjustments.json) 转换。规则资源固定到 [release-lock.json](../build/release-lock.json) 指向的不可变提交，不跟随远程 `main`。
- 三份正式模板和默认 native 输出均保留 LoonKit 的 39 个策略组，无 ALL/Manual 中间组。公开模板的空 use 由本地生成器绑定真实 Provider/use-url；完整私有配置直接引用来源，保留 Stash 的后台节点更新，不下载成静态快照。旧 ALL 仅为显式兼容选项，flat 仅为静态快照选项。运行时审计逐组核对当前订阅节点，CI 不启动 Stash iOS，详见[订阅绑定说明](./NATIVE_PROVIDER_TRIAL.md)。
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
