# StashKit v0.1.10 — LoonKit 同层策略组

本次取消上版的 `Manual` 辅助组，按照 LoonKit 的原始节点筛选与嵌套策略逻辑，恢复 **39 个策略组**。

## 策略选择

`Proxy` 同时包含明确指定的 `Auto`、`Fallback` 策略，以及 `include-all: true` + `filter: '.*'` 动态节点池。不需要设置节点订阅名称。

`ChatGPT`、`Gemini`、`Netflix` 等 34 个服务组也同时包含：

- `Proxy`、`Auto`、`Fallback`；
- 根据 LoonKit 原版保留的 `DIRECT` 选项；
- 自动收集、随订阅更新的所有节点。

`AdBlock` 和 `Final` 维持原有明确的策略列表。`Auto` 和 `Fallback` 仍分别使用节点测速和故障切换。没有 `ALL`、`Manual` 或固定 `personal` 订阅名称。

## 其他配置

三套 YAML 配置同步更新；原有 54 份规则、固定 v0.1.4 规则快照、DNS、前置 STUN 及常见 TURN 端口防护、图标均未更改。继续通过原有 CI 进行静态校验和资源验证。

- [主配置](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.10/StashKit.yaml)
- [Privacy 版](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.10/StashKit-Privacy.yaml)
- [版本发布页](https://github.com/YohakuSama/stashkit/releases/tag/v0.1.10)

**验收边界：** 这是正式版配置变更，但静态配置校验不能证明 Stash iOS 实际同时展示动态节点和嵌套的自动策略。请在 iOS 更新后打开 `Proxy` 与 `ChatGPT` 查看选项，并在连接记录中确认出口；未经过真实 App 测试，不能声称已经完成 UI 验收。
