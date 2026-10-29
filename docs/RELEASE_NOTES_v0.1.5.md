# StashKit v0.1.5

基于已验证的 v0.1.4 固定规则快照发布配置更新。此次发布不修改 54 份规则文件、远程规则 SHA、DNS 字段、分流策略或 WebRTC 拦截规则。

## 更新内容

- 在三套配置中前置 `PROTOCOL,STUN,REJECT` 和常用 STUN/TURN 端口阻断规则，减少经 Stash Tunnel 的公网 IPv4/IPv6 WebRTC STUN 暴露。
- 移除 STUN 域名 Fake-IP 例外；默认 DNS 仍使用 AliDNS DoH，Privacy 版可让公共 DoH 请求跟随策略。
- 从单一主配置确定性生成 Privacy 和 Local 版，并在 CI 中验证字节一致性。
- 精简 YAML 英文注释、README 和架构说明；区分配置版本 v0.1.5 与仍被使用的 v0.1.4 不可变规则快照。
- 固定版本的离线 ZIP 随 GitHub Release 提供，包含 `StashKit-Local.yaml`、54 份本地规则和 `SHA256SUMS.txt`。

## 使用

普通版：[StashKit.yaml](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.5/StashKit.yaml)

DNS Privacy 版：[StashKit-Privacy.yaml](https://raw.githubusercontent.com/YohakuSama/stashkit/v0.1.5/StashKit-Privacy.yaml)

需要自己添加代理节点或订阅。在 Stash 中选择实际可用的 `Proxy` 出口后再使用。

离线 ZIP 并非一键导入包。应按照 [验证说明](https://github.com/YohakuSama/stashkit/blob/v0.1.5/docs/VALIDATION.md) 将规则文件安装到 Stash 受管规则目录。

## 边界

- WebRTC 和 DNS 测试应在自己的 Wi-Fi、蜂窝网络和具体设备上完成，配置规则不能保证拦截未经过 Stash Tunnel 的流量。
- STUN/TURN 阻断可能影响原生 App、游戏、实时语音和视频通话。
- 首次未配置节点时 `Proxy` 默认为 `REJECT`；空节点列表、缓存失效及所有服务的运行表现仍需要设备验收。
