# StashKit v0.1.12 — 无 ALL 的默认动态策略组

三份正式模板恢复与 LoonKit 对应的 39 个策略组，无 ALL/Manual 中间入口。默认生成器直接把真实 Provider 或 use-url 绑定到 Proxy、Auto、Fallback 和业务组，保留原业务策略、DIRECT 顺序及自动策略参数。

首次绑定后，URL 型 Provider 由 Stash 后台更新，节点增删无需重新生成静态列表。名称、刷新间隔、认证头、过滤条件、缓存路径和测速参数保留；只有静态节点或 path-only 来源的输入仍为静态。flat 快照与旧 ALL 布局保留为显式兼容选项。

公开模板用空 use 表示尚未绑定私人来源，不含虚构的 personal 文件，须先按[绑定说明](./NATIVE_PROVIDER_TRIAL.md)生成完整个人配置。默认 native 不下载订阅，必须在 App 中确认真实节点已加载；空 Provider 的 DIRECT 替代不被视为验收成功。

运行时审计新增逐业务组的当前节点集合比较，识别 Auto 可用但同层节点缺失、订阅更新后组成员不同步，以及残留中间策略组。回归覆盖默认 API/CLI、多 Provider、use-url、三种模板与动态节点变更。

规则快照、DNS、防护及图标资产保持原值。CI 验证配置与生成行为，真实界面、出口及断线切换仍需 Stash 设备验收。
