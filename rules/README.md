# 规则资源与来源

StashKit 的**在线配置只声明远程引用**，不将大批域名、CIDR 或 ASN 清单复制进 YAML。`StashKit.yaml` 当前有 **55 份远程文件 Provider**，另有 **133 条 Private-local 本地匹配器**用于冷启动的内网 DNS / 私网保护。

## 当前资源分层

| 类别 | 数量与来源 | 加载方式 |
| --- | --- | --- |
| 基础分类规则 | 54 份 Stash text（43 domain、7 ipcidr、4 classical ASN），合计 196,588 条处理后的匹配器 | GitHub Raw 固定提交，54 份统一使用 `rules/v0.1.23/` 缓存，Crypto 独立固定 |
| Crypto | 1 份 domain 文本规则集，219 条（1 精确域名 + 218 后缀） | [Crypto.v7.0.13.domain.txt](./extra/Crypto.v7.0.13.domain.txt) 固定提交，`rules/v0.1.18/` 缓存 |
| Private-local | 133 条私网匹配器 | 配置内嵌，不依赖首次远程加载 |

基础分类来源为 [LoonKit v7.0.10 固定清单](../build/release_manifest.json) 中的 43 个远程源文件（196,561 条原始匹配器），转换时使用 [adjustments.json](../build/adjustments.json) 做显式的增删和范围调整；原有国内补充、维基百科及多邻国规则保持不变；Apple、SharedInfrastructure 两个现有分类的域名集合按 LoonKit v7.0.16 审查后同步。全部 54 份文件固定在同一 StashKit Git 提交，且不追随 LoonKit main。规则总量以锁文件和各资产为准，不与 Python 生成器的原始匹配器数混为一谈。

Crypto 独立使用 [LoonKit v7.0.13 固定提交](https://github.com/YohakuSama/loonkit/tree/66b01bffe8982d6a8153af7b03c897dc1bbab648) 的 [Crypto.lsr](https://github.com/YohakuSama/loonkit/blob/66b01bffe8982d6a8153af7b03c897dc1bbab648/rules/releases/v7.0.13/Crypto.lsr)。构建时将原生 `DOMAIN` 转为 Stash text 精确域名，将 `DOMAIN-SUFFIX` 转为 `+.` 前缀的后缀域名，保持**原始类型语义**，不混用 Loon / Stash 配置语法。固定资源的路径、上游提交、摘要和 219 条数量记录在 [crypto-source-lock.json](../build/crypto-source-lock.json)。

夸克网盘 `quark.cn`、`myquark.cn` 已加入原有 `DomesticSupplement-domain` 直连分类。维基百科、Wikimedia 及多邻国国际站加入原有 `SharedInfrastructure-domain` 代理分类。Apple 的 Private Cloud Compute 增加 `apple-relay.cloudflare.com`、`apple-relay.fastly-edge.com`、`cp4.cloudflare.com` 三个精确域名，减少四条已被上级 EdgeKey 后缀覆盖的重复项。Stripe 的 `stripe.com`、`stripe.network` 后缀归入现有 SharedInfrastructure / Proxy。没有新增 Provider、策略组或本地域名规则。

## 优先级与例外

正式 YAML 先处理局域网与 WebRTC 防护，再处理**精确服务例外 → AdBlock → Crypto → 国内/其他业务 → Final**。由于基础 AdBlock 保留旧的冻结版本，其中原有 `coincheck.com` 主页误拦，StashKit 使用一条 `DOMAIN,coincheck.com,Crypto` *精确域名* 例外。该例外不适用于所有子域，不影响其他广告遥测在 Crypto 前被拦截。升级 AdBlock 时应先核对该例外是否可以移除，不能叠加跨域放行。

重要：`rules/extra/Crypto.domain.txt` 是历史 29 条的保留快照，**不是 v0.1.18 正式订阅的目标**。正式入口为 [StashKit.yaml](../StashKit.yaml) 中的 `Crypto-domain`，实际远程 URL 固定到已存在的新资源提交，不直接指向可变 `main`。

## 构建与验收

在仓库根目录安装 `requirements-dev.txt` 后运行：

```sh
python scripts/build_rules.py --check
python scripts/build_profiles.py --check
python -m unittest discover -s tests -v
python scripts/verify.py
python scripts/check_remote.py
```

CI 使用三个分离的固定来源：v7.0.10 规则快照、v7.0.12 策略组基线、v7.0.13 Crypto 来源；切换其中一层不会自动更改其他层。在线版按需缓存并刷新固定快照，离线版须事先将全部 55 个文件安装到 Stash 受管资源目录；`StashKit-Local.yaml` 本身不会从网络下载规则。

[路由优先级](../docs/ROUTING.md) · [离线验收](../docs/VALIDATION.md) · [第三方来源及许可](../docs/THIRD_PARTY_NOTICES.md) · [返回首页](../README.md)
