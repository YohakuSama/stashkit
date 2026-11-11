# StashKit v0.1.20 — 自建节点明确引用

这次修复针对用户在 VPN 启动后 `Proxy` 只显示真实节点、丢失 Auto/Fallback/REJECT 的实际反馈：用户确认 v0.1.13 工作正常，v0.1.19 仍失败。

**版本差异**：v0.1.13 使用具名 `Airport` Provider；v0.1.16–v0.1.19 的自建单文件方案改用 `include-all: true`。这次自建版不再让 Stash 运行时同时处理固定选项和 `include-all` 节点。

- [v0.1.20 历史自建模板](https://github.com/YohakuSama/stashkit/blob/a9621e83050a3707944a9a5682bbdf93047d0e85/StashKit-SelfHosted.yaml) 改为一份明确引用 `SelfHosted` 占位节点的**单节点**模板；默认节点参数无效，应替换。可直接修改该节点参数，但名称必须保持 `SelfHosted`。
- 使用自己的多个节点或希望重命名时，运行 `python scripts/build_loon_selection.py --layout flat --nodes-from dist/nodes-source.yaml --output dist/StashKit-Personal.yaml`，由工具从个人节点 YAML 自动填充所有需要节点的策略组，并保持 Auto、Fallback、REJECT 在上方；不用将私人节点名硬编码进仓库。
- v0.1.13 的 `use: [Airport]` 节点订阅模式继续在 [StashKit-Subscription.yaml](../StashKit-Subscription.yaml) 保留，适合不方便运行本地生成器、具有自己的 Clash/Stash YAML 订阅 URL 的用户。
- 远程规则仍为 55 份独立固定快照（包括 219 条 Crypto）；原有 DNS 与路由顺序保持不变，无需粘贴或本地化全部规则。

**验收边界**：静态校验和 CI 不能模拟 iOS Stash VPN。必须在受影响设备检查 VPN 关闭、开启和节点更新后是否始终显示完整策略；若仍失败，请以运行时 API 对照 UI 继续定位。

[README 配置步骤](../README.md) · [验收清单](./VALIDATION.md)
