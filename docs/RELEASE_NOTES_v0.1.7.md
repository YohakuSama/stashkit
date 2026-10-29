# StashKit v0.1.7

修复 v0.1.6 的策略组设计：LoonKit 的 `ALL_Filter` 是节点筛选器，不是应当单独显示的 `ALL` 策略组。

## 修复

- **39 个策略组**，与固定 LoonKit 源配置在名称、顺序及选路候选方面保持一致。
- `Proxy` 直接列出可用订阅节点，同时保留 `REJECT`、`Auto` 和 `Fallback`。
- 原先通过 `ALL` 间接选择节点的 34 个服务策略组，现在可以直接选择订阅节点。
- 删除重复的 `ALL` 策略组和闲置图标；按固定 LoonKit 的节点筛选器语义检查全部三套配置。
- `Proxy` 初始候选仍为 `REJECT`。已在设备上选择过 `ALL` 的用户升级后，应检查并重新选择实际节点或 `Auto`/`Fallback`。

## 导入

普通版：[StashKit.yaml](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.7/StashKit.yaml)

隐私 DNS 版：[StashKit-Privacy.yaml](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.7/StashKit-Privacy.yaml)

离线规则包随此 Release 提供。ZIP 不会自动安装规则文件，参见[验收与离线安装](https://github.com/YohakuSama/stashkit/blob/v0.1.7/docs/VALIDATION.md)。

## 不变的功能

原有 DNS、IPv4/IPv6 WebRTC STUN 防护、分流规则、测速间隔、代理节点订阅及固定的 v0.1.4 规则快照均未修改。空订阅和节点故障时仍需要检查 Stash 的实际出口；CI 不代替所有网络环境的真机测试。
