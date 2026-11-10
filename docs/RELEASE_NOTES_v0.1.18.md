# StashKit v0.1.18

同步 [LoonKit v7.0.13](https://github.com/YohakuSama/loonkit/tree/66b01bffe8982d6a8153af7b03c897dc1bbab648) 的 Crypto 远程规则，同时保留 StashKit 原有 40 策略组、节点来源和 54 份冻结分类资源。

## 本次变更

- **Crypto 远程规则 29 → 219**：将 LoonKit 的 `DOMAIN` / `DOMAIN-SUFFIX` 精确转成 Stash `domain` 文本规则；使用固定 40 位提交的 GitHub Raw URL，`path` 为 `./rules/v0.1.18/Crypto.v7.0.13.domain.txt`；将其与主 YAML 解耦。
- **广告优先级**：AdBlock 在 Crypto 前匹配；但旧 AdBlock 仍含 `coincheck.com` 主页误拦，故在 AdBlock 前增加**仅该主机**的一条 `DOMAIN,coincheck.com,Crypto`，不向整域或公共 CDN 扩大例外。
- **可复现构建**：新增 [Crypto 源锁](../build/crypto-source-lock.json)、已审核源的独立 CI checkout、SHA256/条目数/原 29 根域保留回归；更新自建、订阅、隐私、离线及兼容配置。
- **文档改版**：README 对齐 LoonKit 的展示结构，突出导入方式、规则按需远程引用、使用风险和故障排查。

## 升级注意

公开模板不包含真实节点，仍需手动填写私有订阅或自建节点。首次运行需要加载 55 个远程规则文件；`Local` 离线版必须单独安装全部资源。版本缓存目录已更换，旧 `v0.1.17/Crypto.domain.txt` 不再作为当前 Crypto Provider 的目标；请更新并启用新配置，检查 Stash 实际下载结果和请求记录。

**验证边界**：CI 校验 YAML 结构、静态规则顺序、冻结来源与远程字节；无法证明某一版本 Stash App 的真机匹配、DNS/IPv6 漏洞防护、节点可用性或分流性能。推荐按 [验收指南](./VALIDATION.md) 测试。
