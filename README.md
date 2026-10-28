# StashKit

独立的 Stash 原生分流配置，基于 [LoonKit v7.0.10](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9) 正式规则。全部规则自本仓库托管，不依赖旧的 `loonkit/stashkit` 目录。

当前配置版本 **v0.1.1**。最低文档支持范围为 **Stash iOS/tvOS 3.6+、macOS 4.3+**，用于加密 DNS bootstrap 和独立的节点域名解析；不适用于把同名字段直接套到旧版 Clash 或 Loon。[变更记录](./docs/CHANGELOG.md) · [真机验收步骤](./docs/VALIDATION.md)。

## 导入

**配置 URL：**

```text
https://raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.yaml
```

从 Stash 配置管理界面通过 URL 导入 [StashKit.yaml](./StashKit.yaml)。**需自行添加节点或兼容 Clash/Stash 的订阅**；项目不含个人节点或密钥。可参照 [订阅覆写示例](./overrides/provider.stoverride.example)，将 `example.invalid` 替换成合法的订阅 URL 后在 Stash 中应用。确认 Proxy、ALL、Auto、Fallback 节点池已加载并实际选路；Bing 测速不保证地区解锁。

测速参数按 Stash 官方机制配置在节点或 `proxy-providers` 的 `benchmark-url` / `benchmark-timeout` 上；同一节点在多个组中共享测速结果。示例统一使用 Bing HTTP 测速，组内仅设置测试间隔，不使用 Clash 风格的组级 `url`。

Auto、Fallback、ALL 中的 `REJECT` 仅为尚未配置节点池时的占位。Stash 官方说明空远程代理集可能以 DIRECT 替代，因此这里**不宣称空订阅时一定阻断**；必须按真机验收步骤分别测试空列表、下载失败和旧缓存场景。正常使用前应确认 provider 实际包含节点，并在 ALL 中明确选择可用节点。

## 规则与策略

- 以 LoonKit 43 份正式源文件的 **196,561** 条匹配器为基准，经[明确列出的本地修正](./build/adjustments.json)生成 **54 个 Stash 原生规则集**：43 domain、7 ipcidr、4 classical ASN，共 **196,562** 条匹配器。
- 保留原有 39 个策略组，另新增 ALL 全量节点池（共 **40** 组）。保留策略首选项及 IP 子集 `no-resolve`；内网、GitHub Raw 和 Steam 国内 CDN 的优先级修正见[路由说明](./docs/ROUTING.md)。
- AdBlockBalanced **76,895** 条、ChinaDirect **114,705** 条按域名/IP 类型拆分；不把大型规则直接作为顺序匹配的 classical。
- 使用 **Stash 自身的 Fake-IP + AliDNS DoH**。上游 DNS 与代理节点域名解析采用独立的 DNS 配置；不照搬 Loon 的 `real-ip` / `hijack-dns` 等指令，且 **DoH 加密不等于 DNS 一定经代理**。
- 原 Loon 专用插件/脚本不冒充 Stash 兼容组件。

## DNS 保护边界与 Stash 原生配置

- `dns.default-nameserver: https://223.5.5.5/dns-query`：使用 **IP 地址直连的加密 DoH** 解析 DoH 服务器的主机名，避免原先 `223.5.5.5` / `223.6.6.6` 普通 UDP DNS 的明文引导查询。CI 会测试该 IPv4 HTTPS 端点的证书和 RFC8484 应答。
- `dns.nameserver: https://dns.alidns.com/dns-query`：Stash 的主 DNS 上游，默认**直连 DoH**，不是自动走代理。外部 DoH 服务商可看到需要真实解析的查询；Fake-IP 只能减少部分代理域名的本地 DNS 查询。
- `dns.proxy-server-nameserver`：专门解析节点服务器域名，避免递归 DNS；同样采用加密 DoH，节点服务器名仍可能被 DNS 服务商看到。
- 私有域名通过限定范围的 `nameserver-policy` 使用 `system`，便于访问路由器、NAS 和内网服务；这部分查询可能使用局域网明文 DNS，公共域名仍交给 DoH。私有域名和 LAN 地址另有前置 `DIRECT` 规则；`fake-ip-filter` 本身不负责直连。企业自定义域名需自行补充对应内网 DNS policy。
- `dns.fake-ip-filter`：仅保留私有域名、局域网、网络探测、游戏及 STUN 的有限兼容例外。移除了此前沿用 LoonKit 的 `+.apple.com`、`+.icloud.com` **大范围 Real-IP 例外**，防止不必要的真实 DNS 查询。
- `dns.follow-rule: false`：显式保留 Stash 官方默认行为，不把所有 DNS 强行代理（可能导致代理节点域名递归解析、CDN 延迟）。如需海外 DNS 全程代理，须根据自己的节点 IP/域名及 `proxy-server-nameserver` 单独设计，不能简单打开开关。
- **不保证绝对无 DNS 泄漏**：其他 App 的内置 DoH、直连路径、VPN/Network Extension 的接管情况都需要设备上验证；建议在 Stash 连接后检查 DNS 测试和请求记录。

Stash 官方参考：[DNS 服务](https://stash.wiki/features/dns-server) · [策略组](https://stash.wiki/proxy-protocols/proxy-groups) · [高效配置](https://stash.wiki/faq/effective-stash)。

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
```

生成新规则：`python scripts/build_rules.py`；仅检查可复现性：`python scripts/build_rules.py --check`。生成器先核对[源锁](./build/source-lock.json)、[冻结清单](./build/release_manifest.json)、全部源 SHA256、规则数量和遗留文件，再暂存输出并逐文件原子替换。输入校验失败不会部分改写规则。更新固定基准、调整清单及主配置前必须审查变更，不能自动替换为 beta 候选。

**验证边界**：静态规则、配置语法和远程 HTTP 文件校验，不能替代 Stash iOS/macOS 真机导入、DNS、规则更新、性能、广告和流媒体解锁验收。

## 许可

遵循 [GPL-2.0-only](./LICENSE)，保留 [第三方声明](./docs/THIRD_PARTY_NOTICES.md) 及 LoonKit 规则来源。禁止提交私人订阅 URL 或节点凭据。
