# 第三方许可与来源

StashKit 的原创配置、脚本和本地修正采用 [GPL-2.0-only](../LICENSE)。第三方规则、图标和品牌标识保留各自适用的声明；不能将项目整体许可当成对全部第三方素材的独立授权证明。

## 当前规则来源

生成基准为 [YohakuSama/loonkit 固定提交 5f272104](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9)。本仓库保留：

- [冻结的上游发布清单](../build/release_manifest.json)：43 个源文件的路径、固定资源地址、策略、SHA256 和 196,561 条原始匹配器。
- [源锁](../build/source-lock.json)：基准提交、清单与原配置的摘要。
- [StashKit 本地修正](../build/adjustments.json)：收窄動畫瘋范围、前移 Steam 国内 CDN 和补齐 Google 广告/统计端点；生成后为 196,570 条文件匹配器。
- [历史来源目录](../build/historical_license_sources.json)：原样保留上游的 87 条历史输入记录；其中的旧数量、路径和未恢复的逐条溯源状态均是历史记录，不能当成当前分发数量或完整的逐条来源认证。
- [材料摘要锁](../build/third-party-lock.json)：许可文本及历史目录的上游路径和 SHA256。

内嵌 `Private-local` 的 133 条私网规则直接来自 [V2Fly 固定提交 fc0a0693 的 data/private](https://github.com/v2fly/domain-list-community/blob/fc0a0693ec4e5c09938957c98aa11e530764492f/data/private)。保留 [原始文件](../build/private-domains.source.txt)、[源与许可摘要锁](../build/private-domains-lock.json)和[对应 MIT 许可](../rules/LICENSE.MIT-PRIVATE)。精确、后缀与单标签 DNS 名称语义用于三套配置；单标签正则以适用于有效 DNS 标签的无逗号形式内嵌。

## 许可文本与来源项目

| 来源项目 | 上游记录的许可 | 随仓库保留的材料 |
| --- | --- | --- |
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) | GPL-2.0-only | [GPL 文本](../rules/LICENSE.GPL-2.0)及历史来源目录 |
| [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) | MIT | [MIT 版权及许可声明](../rules/LICENSE.MIT-V2FLY) |
| [felixonmars/dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) | WTFPL-2.0 | [许可及版权文本](../rules/LICENSE.WTFPL-FELIXONMARS) |
| [o-ocn/loon-rules 固定参考提交](https://github.com/o-ocn/loon-rules/tree/47fa36ef0fcbfb9b664bac6fa2f4e574b6107b0f) | 上游声明为 GPL-2.0 | 上游在 v7.0.3 服务补充中登记的必要域名参考，见[固定来源说明](https://github.com/YohakuSama/loonkit/blob/5f272104fc1207612c1cbd18f3e19d861d459ed9/docs/THIRD_PARTY_NOTICES.md) |
| LoonKit 自有规则及 StashKit 修改 | 自有贡献采用 GPL-2.0-only | 项目 LICENSE、固定源清单和本地修正记录 |

三份规则许可文本和历史来源目录均按源锁所指向的 LoonKit 提交原样复制，并由测试检查摘要。[上游来源登记](https://github.com/YohakuSama/loonkit/blob/5f272104fc1207612c1cbd18f3e19d861d459ed9/rules/sources.json)与[历史决策记录](https://github.com/YohakuSama/loonkit/blob/5f272104fc1207612c1cbd18f3e19d861d459ed9/rules/reviewed/v6.5.8/decisions.json)保留在固定上游地址，不声称它们全部存在于本仓库。

上游说明 [luestr/ProxyResource](https://github.com/luestr/ProxyResource) 与 [luestr/ShuntRules](https://github.com/luestr/ShuntRules) 仅用于组织与分类参考，未复制其模板或托管规则正文。历史合并快照不能恢复所有规则的逐条来源；保留现有材料不等于独立完成权利认定。

## 图标与品牌

运行时 PNG 图标来自 LoonKit 固定资源提交 d82214d057b27a68d6b9c07c61fb126a69adc903。[图标说明](https://github.com/YohakuSama/loonkit/blob/5f272104fc1207612c1cbd18f3e19d861d459ed9/icons/README.md)与[App Store 来源清单](https://github.com/YohakuSama/loonkit/blob/5f272104fc1207612c1cbd18f3e19d861d459ed9/icons/appstore_sources.json)提供原有素材登记。本仓库在 icons/ 保留 39 张 PNG 供 40 个策略组（含隐藏的 Manual）复用，配置引用固定图标提交；摘要由 icon-lock.json 验证。

品牌名称、商标和应用图标用于识别相应服务，权利归各自权利人；这不代表相关平台认可或赞助。

来源、署名或材料问题请在 [StashKit Issues](https://github.com/YohakuSama/stashkit/issues) 中提供资源路径及参考依据。

[返回首页](../README.md) · [规则说明](../rules/README.md)
