# StashKit v0.1.9

修复公共 StashKit 配置中的 `Proxy` 策略组只显示节点、无法直接切换 `Auto` 或 `Fallback` 的问题。

## 策略组选择

`Proxy` 为普通 `select` 策略组，明确列出：

- `Auto`：自动测速选择节点。
- `Fallback`：优先使用按顺序排列的健康节点，并在故障时切换。
- `Manual`：进入隐藏的节点池，自行选择现有订阅中的实际节点（不要求指定任何 Provider 名称）。
- `REJECT`：配置里的初始兜底候选，空订阅时是否严格阻断仍须真机检查。

`Manual` 设置了 `hidden: true` 和 `include-all: true`，不在顶层策略群组页面单独显示，但可作为 `Proxy` 的选项使用。

`ChatGPT`、`Gemini`、`Netflix` 等服务组仍提供 `Proxy`、`Auto`、`Fallback` 选项。其中 `Proxy` 会跟随上面选择的 `Auto` / `Fallback` / `Manual`，实现全局统一的选路方式。

**限制：** 这与 LoonKit 完全同层列出动态节点的方式不同。在不预先获知订阅节点名称的公共 YAML 中，当前可验证的设计将节点手选放在 `Manual` 下，额外多一步。需要在同层直接选择节点和自动策略时，可使用仓库提供的[本地配置生成器](https://github.com/YohakuSama/stashkit/blob/main/docs/LOON_POLICY_GROUPS.md)。

## 不变的部分

- 原有 39 个服务及策略组名称与顺序保留；额外增加 1 个隐藏的节点池，共 40 个 YAML 策略组。
- 原有订阅地址、DNS、前置 STUN WebRTC 拦截、54 份规则资源与不可变 v0.1.4 快照均不变。
- 三套配置由单一主文件生成并在 CI 校验。39 张固定 PNG 图标复用，不额外下载图标。

## 配置

- [StashKit.yaml](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.9/StashKit.yaml)
- [StashKit-Privacy.yaml](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.9/StashKit-Privacy.yaml)
- [离线包与安装说明](https://github.com/YohakuSama/stashkit/blob/v0.1.9/docs/VALIDATION.md)

升级后，请在 Stash 策略群组页面确认 `Proxy` 能展开并选择 `Auto`、`Fallback`、`Manual`，并通过连接记录确认具体出口。CI 不等于 iOS 真机 UI 验收。
