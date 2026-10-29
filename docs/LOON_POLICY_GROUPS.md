# StashKit 策略组：原生 Provider 与兼容回退

## 正式版：原生同层选路

默认 `StashKit.yaml` 的 `Proxy` 不再包含 `ALL`，改用 Stash 官方 `proxy-providers` + `use`：

```yaml
proxy-providers:
  personal:
    path: ./providers/personal.yaml # 需要你自己提供有效节点文件

proxy-groups:
  - name: Proxy
    type: select
    use: [personal]
    proxies: [Auto, Fallback, REJECT]
  - name: Auto
    type: url-test
    use: [personal]
    proxies: [REJECT]
  - name: Fallback
    type: fallback
    use: [personal]
    proxies: [REJECT]
```

**目标界面**是 `Proxy` 下同层列出 Auto、Fallback 和订阅的具体节点，但能否在当前 Stash iOS 上同时显示，仍须真机验证；GitHub CI 只能验证合法引用和配置结构。

公开仓库无法读取你的个人订阅。默认 `personal` 是无 URL 的本地路径型 Provider；官方支持只含 `path` 的静态 Provider。必须先提供真实 `./providers/personal.yaml` 或覆盖 `personal.url` 为真实 HTTPS 节点集，才能正常使用。**空 Provider 官方可能转为 DIRECT，不能将其视为安全的拒绝回退。**

若不想手动创建路径型 Provider，请按[原生订阅生成说明](./NATIVE_PROVIDER_TRIAL.md)本地生成一个含私人订阅的完整 YAML。任何个人订阅 URL、认证信息、节点密码均不应上传到公开 GitHub。

## 直连服务不变

| 服务组 | 默认选路 | 手动可选 |
| --- | --- | --- |
| Apple、Microsoft、Bilibili、Line、Speedtest | DIRECT | Proxy、Auto、Fallback、Provider 节点 |
| Steam | Proxy | DIRECT、Auto、Fallback、Provider 节点 |
| ChatGPT、Gemini、Claude 等海外服务 | Proxy | Auto、Fallback、Provider 节点 |

`DomesticCore`、`DomesticSupplement`、`DomesticAI`、`SteamCN` 等规则集继续高优先级直连，与服务组是否含 DIRECT 无关。保持广告拦截优先级与其他路由规则不变。

## 一键回退旧版 ALL

用户在 Stash iOS 上观察到 `include-all` + 明确策略组混用时不能保证同层显示。之前因此使用二层 `ALL` 兼容方案，现完整备份为：

- [默认兼容版](../StashKit-ALL.yaml)
- [隐私兼容版](../StashKit-Privacy-ALL.yaml)
- [本地规则兼容版](../StashKit-Local-ALL.yaml)

这些备份的 `Proxy` 为 `Auto → Fallback → ALL`，进入 `ALL` 再选具体节点。备份不需要指定 `personal` Provider，继续沿用 `include-all` 收集 Stash 已加载的节点。

官方文档：[Stash 策略组](https://stash.wiki/proxy-protocols/proxy-groups) · [远程代理集](https://stash.wiki/proxy-protocols/proxy-providers)。
