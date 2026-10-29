# StashKit v0.1.8

修复 Stash 策略组 UI 中无法从服务组选择 `Auto` 或 `Fallback` 的问题。此前 `include-all: true` 使 `ChatGPT` 等组在实际 Stash 界面中只显示两个具体节点，即使配置文本声明了自动策略。

## 策略组操作

- **Proxy**：直接选定某个订阅节点，例如 Snell 或 HY2。这是共享的手动节点出口。
- **Auto**：在全部订阅节点中自动测速选择，延迟容差为 60 ms，检测间隔为 600 秒。
- **Fallback**：按节点顺序优先使用健康节点，检测间隔为 900 秒。
- **ChatGPT、Gemini、Netflix 等服务组**：直接显示 `Proxy`、`Auto`、`Fallback` 三个可选策略；部分服务保留 `DIRECT`。
- **Final**：继续提供 `Proxy`、`Auto`、`Fallback`、`DIRECT`。

例如希望 ChatGPT 使用自动测速：打开「策略群组」→「ChatGPT」→ 选择 `Auto`。选择 `Proxy` 则会跟随 `Proxy` 当前手动节点。

## 兼容性

此次修改保持 39 个策略组、全部原有规则、DNS 和 WebRTC 防护不变，仍使用固定的 v0.1.4 规则资源快照。

为了让 `Auto` 和 `Fallback` 在 Stash 界面中真正可见，服务组不再同时开启 `include-all`。因此服务组通过 `Proxy` 共享手动选定的节点，不会在每个服务组内部重复列出全部订阅节点。首次更新后，请核对服务组的当前选择，避免继续使用已失效的旧节点选择。

## 下载

普通版：[StashKit.yaml](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.8/StashKit.yaml)

隐私 DNS 版：[StashKit-Privacy.yaml](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.8/StashKit-Privacy.yaml)

离线版随 Release 附带，ZIP 不是 Stash 一键导入格式。详见[验收与安装](https://github.com/YohakuSama/stashkit/blob/v0.1.8/docs/VALIDATION.md)。

运行时提示：当节点订阅为空或失效时，不能仅凭配置中的 `REJECT` 判定不会直连；请在 Stash 连接记录中检查真实出口。
