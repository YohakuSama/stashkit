# StashKit v0.1.11 — Loon 策略组适配修复

正式版解决固定 personal 本地文件未提供时无法导入真实节点的问题。公开配置通过独立的 Auto/Fallback/ALL 节点池收集当前配置中的任意节点与 Provider，明确保留自动策略、业务默认和 DIRECT 选项。REJECT 保留为 Proxy/AdBlock 的手动策略，不再混入节点池。

私有生成器默认使用 flat：从本地 YAML、相对路径 Provider 或 HTTPS 订阅获取真实节点，生成 39 个与 Loon 对应的同层策略组，无 ALL 或动态混合引用。空源、过滤后为空、无效节点、重名冲突及下载失败均停止生成并保留旧文件；私有输出以 0600 权限原子替换。

运行时审计现在检查所有策略组的类型、成员、当前选择和 Auto/Fallback/ALL 节点池，识别选项缺失和空 Provider 的 DIRECT 替代。派生配置、兼容链接和参考预览统一生成，避免正式版与示例漂移。

54 份文件规则及 v0.1.4 不可变规则快照、DNS、STUN/TURN 防护与图标资产保持原值。Loon 原始业务策略与直连顺序由固定源的独立回归比较校验。

使用方式见[生成说明](./NATIVE_PROVIDER_TRIAL.md)。flat 节点变化后需要重新生成；动态自动更新可用公开兼容布局。Stash 共享节点测速，无法直接表达 Loon 的 Fallback 独立 2200ms 超时。CI 和本地回归不能替代 Stash iOS 的真实界面、出口与断线验收。
