# StashKit v0.1.6

将节点直接显示在 `Proxy` 策略组中，减少手动选节点的操作步骤。

## 更新内容

- `Proxy` 新增 `include-all: true`，收集主配置节点和远程订阅的节点，可以直接点击具体节点。
- 保留 `REJECT`、`Auto`、`Fallback` 和 `ALL`。新配置初始候选仍以 `REJECT` 开头，旧设备可能保留已选择的出口。
- 三套 YAML 由主配置派生并经过一致性检查。规则集、DNS 配置、WebRTC 防护、图标和策略组数量均未改动。

## 导入

普通版：[StashKit.yaml](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.6/StashKit.yaml)

隐私 DNS 版：[StashKit-Privacy.yaml](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.6/StashKit-Privacy.yaml)

将自己的节点订阅导入 Stash 后，在 `Proxy` 组选择实际节点、`Auto` 或 `Fallback`。仍可使用原有 `ALL` 组手动选择节点。

离线 ZIP 需按 [安装指南](https://github.com/YohakuSama/stashkit/blob/v0.1.6/docs/VALIDATION.md) 将 54 份规则文件放入 Stash 受管规则目录，不能直接把 ZIP 当作一键配置导入。

## 兼容性说明

本版本继续引用 v0.1.4 的固定规则快照，不需要刷新缓存路径。节点故障和空订阅时的实际出口需在 Stash 中验证；不保证全部网络环境下绝对不直连。
