# StashKit v0.1.17 — 远程规则解耦与精简 YAML

## 为什么改

主配置 v0.1.16 长达 983 行：40 个策略组全部展开、54 个远程规则 Provider 每个占多行、内嵌 133 条私网匹配器，Crypto 29 条规则还直接写在 rules 中。规则实际上已经部分远程化，但声明重复占据绝大多数文件行数。

## 本次

- **主配置减少到约 280 行**。40 个策略组的名称、类型、优先顺序、默认选项、图标以及 Provider 引用保持不变；54 个原有远程规则的 URL、缓存、interval、类型全部保留，只将重复的 YAML 声明改成紧凑的 Flow Mapping。
- **Crypto 独立远程规则集**：29 个 LoonKit v7.0.12 Crypto 后缀匹配变为 `Crypto-domain` + `RULE-SET,Crypto-domain,Crypto`。以 `behavior: domain` 和 `format: text` 使用不可变远程地址，离线版本包含相同规则字节，优先级保持在通用业务和 CN 直连之前。
- **安全的 Private-local 保持内嵌**：133 个私网 DNS / LAN 条目仅压缩排列，不改匹配器，不把首次启动时的私网识别变成远程依赖。
- **双节点模式不受影响**：订阅版和自建多节点版均压缩到约 280 行，自建版仍用 Stash 官方 `include-all: true` 自动载入全部本地节点。
- **自动化验证**：检查 54 份原有冻结规则 SHA 和 Provider 精确一致、Crypto 29 条与上游完全对应、所有公开变体的策略与路由顺序保持一致、在线 Crypto 文件 HTTP 字节一致、离线 ZIP 55 份规则文件齐全。

## 注意事项

主文件中的规则声明比 Loon 配置略长是 Stash 的 `rule-providers` 模式要求：要在 `rules:` 中按策略引用，须先声明具名远程规则集。这并不意味着规则数据被塞回主 YAML。

v0.1.17 离线资源包除旧的 `rules/v0.1.4/` 54 个文件外，还包括 `rules/v0.1.17/Crypto.domain.txt`；单纯导入 ZIP 不会自动复制缓存资源。设备端连接、DNS 及首次远程规则下载仍需使用 Stash 检查。
