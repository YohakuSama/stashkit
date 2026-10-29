# LoonKit 策略组在 Stash 中的适配

Loon 的 `ALL_Filter / Auto_Filter / Fallback_Filter` 在组内展开节点；Stash 的 `include-all / use / use-url` 是另一套节点来源语法。仓库此前记录过混用明确策略和动态节点时 UI 选项缺失，不能仅由 YAML 通过校验认定已经复现 Loon 的界面。

## 同层明确节点：flat 私有配置

生成器默认读取真实节点并展开 Loon 的三个筛选器，输出 39 个对应策略组。例如节点有 A、B 时：

| 策略组 | 选项顺序 |
| --- | --- |
| Proxy | Auto、Fallback、A、B、REJECT |
| Auto | A、B；url-test，600 秒，tolerance 60ms |
| Fallback | A、B；fallback，900 秒 |
| ChatGPT 等海外服务 | Proxy、Auto、Fallback、A、B |
| Apple、Microsoft、Bilibili、Line、Speedtest | DIRECT、Proxy、Auto、Fallback、A、B |
| Steam | Proxy、Auto、Fallback、DIRECT、A、B |
| AdBlock | REJECT、DIRECT、Proxy |
| Final | Proxy、Auto、Fallback、DIRECT |

所有节点以明确名称出现在 `proxies` 列表中，无 ALL 中间组、固定 Provider 名称或动态混合来源。Auto/Fallback 只含真实节点，不把 REJECT 当作节点参与选路。生成前必须获取有效且非空的节点集；任何源加载失败、过滤后为空或同名节点内容不同都会停止，不会输出半份配置。

具体命令见[私有配置生成说明](./NATIVE_PROVIDER_TRIAL.md)。节点发生变化后重新生成；现有节点的 Auto 测速和 Fallback 故障切换仍由 Stash 执行。

## 自动更新：公开兼容布局

公开 `StashKit.yaml` 没有私人节点，采用 39 个对应组加 1 个 ALL 节点入口：

| 位置 | 配置 |
| --- | --- |
| Proxy | 明确引用 Auto、Fallback、ALL、REJECT |
| 业务组 | 保留 Loon 的默认策略及 DIRECT 顺序，通过 ALL 手动选节点 |
| Auto / Fallback / ALL | 仅使用 include-all 和 filter 收集当前配置的节点与 Provider |

把自己的节点或任意名称的 Provider 加入**当前生效配置**，三个节点池就能引用它们。另一个独立配置中的订阅不会自动合并。无需 `personal` 名称，也无需不存在的 `./providers/personal.yaml`。`StashKit-ALL.yaml`、Privacy-ALL、Local-ALL 为同步生成的兼容链接。

Stash 官方说明空组和空 Provider 可能按 DIRECT 处理。公开模板必须配好节点再启用；Proxy 中的 REJECT 只是手动选项，不能保证空订阅自动阻断。运行时审计会拒绝把 DIRECT/REJECT 或嵌套策略当作真实节点池。

## 适配边界

Stash 为同一个节点共享测速结果，Loon 的组级 `url` 和 `max-timeout` 不能直接搬成 Stash 组字段。flat 输出保留节点或 Provider 自己的 `benchmark-url / benchmark-timeout`，未设置时使用 `http://www.bing.com` / 5 秒；不宣称复现 Fallback 独立的 2200ms 超时。

`--layout native` 保留具名 Provider / use-url 动态混合模式，须自行检查 Stash 实际界面。CI 验证源策略顺序、引用、规则可复现性和生成器行为；真实 App 显示、节点连通和故障切换仍需设备验收。

官方文档：[策略组](https://stash.wiki/proxy-protocols/proxy-groups) · [远程代理集](https://stash.wiki/proxy-protocols/proxy-providers) · [延迟测试](https://stash.wiki/proxy-protocols/proxy-benchmark)。
