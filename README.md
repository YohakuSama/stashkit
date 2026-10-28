# StashKit

独立的 Stash 原生分流配置，基于 [LoonKit v7.0.10](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9) 正式规则。全部规则自本仓库托管，不依赖旧的 `loonkit/stashkit` 目录。

## 导入

**配置 URL：**

```text
https://raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.yaml
```

从 Stash 配置管理界面通过 URL 导入 [StashKit.yaml](./StashKit.yaml)。**需自行添加节点或兼容 Clash/Stash 的订阅**；项目不含个人节点或密钥。可参照 [订阅覆写示例](./overrides/provider.stoverride.example)，将 `example.invalid` 替换成合法的订阅 URL 后在 Stash 中应用。确认 Proxy、ALL、Auto、Fallback 节点池已加载并实际选路；Bing 测速不保证地区解锁。

## 规则与策略

- 从 LoonKit 43 份正式源文件生成 **54 个 Stash 原生规则集**：43 domain、7 ipcidr、4 classical ASN，共 **196,561** 条匹配器。
- 保留原有 39 个策略组，另新增 ALL 全量节点池（共 **40** 组）。保留策略首选项、规则优先级及 IP 子集 `no-resolve`。
- AdBlockBalanced **76,895** 条、ChinaDirect **114,705** 条按域名/IP 类型拆分；不把大型规则直接作为顺序匹配的 classical。
- 使用 **Stash 自身的 Fake-IP + AliDNS DoH**。上游 DNS 与代理节点域名解析采用独立的 DNS 配置；不照搬 Loon 的 `real-ip` / `hijack-dns` 等指令，且 **DoH 加密不等于 DNS 一定经代理**。
- 原 Loon 专用插件/脚本不冒充 Stash 兼容组件。

## DNS 保护边界与 Stash 原生配置

- `dns.default-nameserver: https://223.5.5.5/dns-query`：使用 **IP 地址直连的加密 DoH** 解析 DoH 服务器的主机名，避免原先 `223.5.5.5` / `223.6.6.6` 普通 UDP DNS 的明文引导查询。CI 会测试该 IPv4 HTTPS 端点的证书和 RFC8484 应答。
- `dns.nameserver: https://dns.alidns.com/dns-query`：Stash 的主 DNS 上游，默认**直连 DoH**，不是自动走代理。外部 DoH 服务商可看到需要真实解析的查询；Fake-IP 只能减少部分代理域名的本地 DNS 查询。
- `dns.proxy-server-nameserver`：专门解析节点服务器域名，避免递归 DNS；同样采用加密 DoH，节点服务器名仍可能被 DNS 服务商看到。
- `dns.fake-ip-filter`：仅保留私有域名、局域网、网络探测、游戏及 STUN 的有限兼容例外。移除了此前沿用 LoonKit 的 `+.apple.com`、`+.icloud.com` **大范围 Real-IP 例外**，防止不必要的真实 DNS 查询。
- `dns.follow-rule: false`：显式保留 Stash 官方默认行为，不把所有 DNS 强行代理（可能导致代理节点域名递归解析、CDN 延迟）。如需海外 DNS 全程代理，须根据自己的节点 IP/域名及 `proxy-server-nameserver` 单独设计，不能简单打开开关。
- **不保证绝对无 DNS 泄漏**：其他 App 的内置 DoH、直连路径、VPN/Network Extension 的接管情况都需要设备上验证；建议在 Stash 连接后检查 DNS 测试和请求记录。

Stash 官方参考：[DNS 服务](https://stash.wiki/features/dns-server) · [策略组](https://stash.wiki/proxy-protocols/proxy-groups) · [高效配置](https://stash.wiki/faq/effective-stash)。

## 自动校验

[GitHub Actions](./.github/workflows/ci.yml) 校验：全量规则逐条一致、源 SHA256、重复项、类型语法、54 个引用地址、策略名称、匹配顺序及 YAML 结构。CI 另会真实探测 DoH bootstrap 证书与解析，主分支还会通过 HTTP 实际下载全部 54 个规则集，比对字节完全一致，包括两个大型规则文件。

为保证可复现，源版本固定在 [LoonKit commit 5f272104](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9)，防止上游改动自动变更生产策略。手动验证：

```sh
git clone https://github.com/YohakuSama/stashkit.git
cd stashkit
git clone https://github.com/YohakuSama/loonkit.git upstream/loonkit
git -C upstream/loonkit checkout 5f272104fc1207612c1cbd18f3e19d861d459ed9
python -m pip install 'PyYAML>=6,<7'
python scripts/verify.py
python scripts/check_remote.py
```

生成新规则：`python scripts/build_rules.py`，但更新 LoonKit 固定基准及主配置前必须审查变更，不能自动替换为 beta 候选。

**验证边界**：静态规则、配置语法和远程 HTTP 文件校验，不能替代 Stash iOS/macOS 真机导入、DNS、规则更新、性能、广告和流媒体解锁验收。

## 许可

遵循 [GPL-2.0-only](./LICENSE)，保留 [第三方声明](./docs/THIRD_PARTY_NOTICES.md) 及 LoonKit 规则来源。禁止提交私人订阅 URL 或节点凭据。
