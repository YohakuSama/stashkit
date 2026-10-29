# LoonKit 策略组在 Stash 中的适配

正式默认保留 LoonKit 的 39 个对应策略组，无 ALL、Manual 或改名后的中间节点选择组。Provider 直接绑定到 Proxy、Auto、Fallback 和业务组。

## 默认 native 布局

以任意名称的 Provider `my-provider` 为例：

| 组 | 明确的策略选项 | 动态节点来源 |
| --- | --- | --- |
| Proxy | Auto、Fallback、REJECT | use: [my-provider] |
| Auto | 无内置策略；url-test，600 秒，tolerance 60ms | use: [my-provider] |
| Fallback | 无内置策略；fallback，900 秒 | use: [my-provider] |
| ChatGPT 等海外服务 | Proxy、Auto、Fallback | use: [my-provider] |
| Apple、Microsoft、Bilibili、Line、Speedtest | DIRECT、Proxy、Auto、Fallback | use: [my-provider] |
| Steam | Proxy、Auto、Fallback、DIRECT | use: [my-provider] |
| AdBlock | REJECT、DIRECT、Proxy | 无额外节点源 |
| Final | Proxy、Auto、Fallback、DIRECT | 无额外节点源 |

多个 Provider 按输入顺序引用；URL、刷新间隔、认证头、过滤条件、缓存和测速参数保留。只有订阅 URL 时，生成器可直接写入各组的 use-url，保持 Stash 后台更新。Auto/Fallback 只引用真实节点来源，不混入 REJECT。

具体节点从动态来源导入，策略选项按 Loon 原来的顺序保留；订阅节点增删后无需重新生成配置。运行时审计会比较 Auto/Fallback 的实际节点，以及每个业务组是否同时包含策略和当前节点，避免只验证 Auto 有出口。

## 公开模板与首次绑定

三份公开 YAML 的 `use: []` 有意留空，仓库没有私人节点、订阅地址或虚构的本地 Provider 文件。第一次使用必须按[绑定说明](./NATIVE_PROVIDER_TRIAL.md)生成包含真实来源的完整配置；只导入公开模板不能获得节点，另一个独立配置中的订阅也不会自动合入。

默认 native 不会提前下载私人订阅。生成成功说明引用与结构有效，Provider 是否非空、实际节点是否连通需要在 Stash 中检查。空组或空 Provider 可能按 DIRECT 处理，手动 REJECT 选项不能保证自动阻断。

## 可选布局

| 选择 | 组数 | 节点更新 |
| --- | --- | --- |
| native（默认） | 39，无 ALL | Provider / use-url 由 Stash 更新 |
| flat（显式选择） | 39，无 ALL | 静态节点快照，节点变化后重新生成 |
| nested / -ALL 文件（旧版兼容） | 40，额外 ALL 入口 | 可保留 Provider 更新；需要多进一层手动选节点 |

旧兼容文件不再是默认模板的别名，不会因运行默认生成器而重新插入 ALL。

## 适配边界

Stash 为同一个节点共享测速结果，Loon 的组级 url 和 max-timeout 不能直接搬成 Stash 组字段；不宣称复现 Fallback 独立的 2200ms 超时。原来的业务默认、DIRECT 顺序和 Auto/Fallback 周期由固定 Loon 源的独立回归比较。

Stash 官方文档支持策略与 Provider 引用；当前 App 是否正确显示同层选项，仍需运行时及真机验收。此前出现过的动态混合显示问题不能仅凭 YAML 校验排除；如你的版本缺少选项，运行时审计会失败，明确节点的 flat 模式可用于兼容。

官方文档：[策略组](https://stash.wiki/proxy-protocols/proxy-groups) · [远程代理集](https://stash.wiki/proxy-protocols/proxy-providers) · [延迟测试](https://stash.wiki/proxy-protocols/proxy-benchmark)。
