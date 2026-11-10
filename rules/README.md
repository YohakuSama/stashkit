# 生成规则与来源

本目录包含 54 份原有冻结的 Stash text 规则集：43 domain、7 ipcidr、4 classical ASN；当前原有文件共 196,570 条匹配器，另有 Crypto 29 条独立远程匹配器。另外新增 1 份固定到独立提交的 [Crypto-domain](./extra/Crypto.domain.txt) 远程规则集（29 条），配置内嵌 133 条 `Private-local` 私网匹配器，共 56 个 provider；私网源文件、摘要和许可证见 [私网源锁](../build/private-domains-lock.json)。

输入为 [LoonKit v7.0.10 固定源清单](../build/release_manifest.json)，共有 43 个源文件、196,561 条匹配器；[本地调整](../build/adjustments.json)显式登记了增删与原因。清单中的 URI 指向原始 Loon 资产，不能作为 Stash 规则 URL 直接导入。Stash 实际入口为 [StashKit.yaml](../StashKit.yaml) 中本仓库的 rule-providers。

运行 `python scripts/build_rules.py --check` 可核对全部输出字节；运行 `python scripts/build_rules.py` 会先校验固定输入再生成，不会自动跟随上游新版本。两条命令均从仓库根目录执行，按 [README](../README.md) 准备固定上游和依赖。

原始匹配器的类型语义保持不变：DOMAIN 保持精确匹配；DOMAIN-SUFFIX 转为 `+.` 前缀；CIDR 保持地址族和 `no-resolve`；ASN 使用小型 classical 集合。大型域名和 IP 集合不采用顺序匹配的 classical。

许可文本：[GPL-2.0](./LICENSE.GPL-2.0)、[MIT 与 V2Fly 版权声明](./LICENSE.MIT-V2FLY)、[WTFPL 与原版权声明](./LICENSE.WTFPL-FELIXONMARS)。完整背景见[第三方声明](../docs/THIRD_PARTY_NOTICES.md)与[历史来源目录](../build/historical_license_sources.json)。

新增 Crypto 资源使用 Stash `behavior: domain`、`format: text` 和固定提交 URL；`rules/extra/` 不属于 54 份 v0.1.4 源规则的再生成集合，避免破坏其冻结快照。正式配置在 `rules/v0.1.17/Crypto.domain.txt` 缓存它，离线包也会包含该文件。主 YAML 的 Remote Provider 一行化只是 YAML 排版精简，解析结构不变。
