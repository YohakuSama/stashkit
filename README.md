# StashKit

面向 [Stash](https://stash.wiki/) 的规则分流配置。国内常用服务直连，AI、开发平台、流媒体与社交服务可独立选路。规则基于 [LoonKit v7.0.10 固定版本](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9) 转换，产物由本仓库托管。

当前配置：**v0.1.10** · [发布说明](./docs/RELEASE_NOTES_v0.1.10.md) · [变更记录](./docs/CHANGELOG.md) · [CI](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) · [GPL-2.0-only](./LICENSE)

## 功能概览

**服务分流** — 提供与 LoonKit 一致的 39 个策略组，覆盖 AI、开发平台、流媒体、社交及国内常用服务；广告请求由 `AdBlock` 处理。

**服务直连** — Apple、Microsoft、Bilibili、Line、Speedtest 默认可选直连（首选为 `DIRECT`），Steam 可手动直连但默认走代理；国内核心服务、国内 AI 和 SteamCN CDN 在规则层直连。海外 AI / 流媒体保留独立代理选择，不把 `DIRECT` 泛加到所有服务或 `Proxy`。详见[路由策略](./docs/ROUTING.md)。

**节点选路** — `Proxy` 明确包含 `Auto` / `Fallback`，并通过 `include-all` 和 `filter: '.*'` 收集订阅节点。ChatGPT 等服务组同时明确列出 `Proxy` / `Auto` / `Fallback` 和动态节点；没有 `ALL`、`Manual` 或具名 Provider 要求。项目不包含节点或个人订阅。

**LoonKit 选路兼容性** — 除公共配置的 `include-all` 外，还支持基于 Stash 原生 `use-url` 的[私有订阅生成方案](./docs/LOON_POLICY_GROUPS.md)：只需在本地提供已有 HTTPS 节点订阅 URL，不必指定 Provider 名称或列举节点，`Proxy` 与服务组明确列出 `Auto` / `Fallback`，并引用相同的动态订阅。无需 `ALL` / `Manual` 中转组；私有生成版 `Proxy` 以 `Auto` 为首选，`REJECT` 放在最后作为明确的拒绝兜底，保留上述服务的 `DIRECT` 选择。生成的私有文件含订阅凭据，不能提交到公开仓库。iOS 实际显示仍需验收。

**网络保护** — 使用 Stash Fake-IP、AliDNS 加密 DNS 和前置 STUN/常见 TURN 端口拦截规则。WebRTC 防护仅适用于被 Stash Tunnel 接管的连接。

## 快速开始

1. **备份**现有 Stash 配置和节点订阅。
2. 在 Stash 中通过 URL 导入[主配置](https://raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.yaml)。
3. 添加自己的节点或使用[订阅覆写示例](./overrides/provider.stoverride.example)，将示例地址替换为有效订阅。
4. 更新配置后，在 `Proxy` 或服务策略组中选择 `Auto`、`Fallback` 或具体节点；确认 Stash iOS 是否同时展示这两类选项，并查看连接记录。
5. 启动 Stash VPN/Tunnel，在请求记录中检查分流与实际出口。

> [!IMPORTANT]
> `Auto` / `Fallback` 在无节点时仍保留 `REJECT` 兜底，但不代表空订阅时一定不会直连；必须在 Stash iOS 真实测试。更新配置可能保留设备上已有的策略选择；空订阅和故障回退需检查实际出口。

## 配置版本

| 配置 | 用途 |
| --- | --- |
| [StashKit.yaml](./StashKit.yaml) | 默认分流；公共 DNS 使用 AliDNS DoH，`follow-rule: false` |
| [StashKit-Privacy.yaml](./StashKit-Privacy.yaml) | 公共 DoH 请求跟随路由并优先走 `Proxy`；须先选择可用节点 |
| [StashKit-Local.yaml](./StashKit-Local.yaml) | 离线规则版；须先把 54 份文件规则放入 Stash 资源目录 |

离线文件包可从 [CI 产物](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) 获取。ZIP 不会自动安装到 Stash 的规则目录；详见[安装及验收说明](./docs/VALIDATION.md)。

## 使用与排查

- **WebRTC / IPv4 / IPv6**：三套配置前置拦截 `STUN` 和常见 STUN/TURN 目的端口。保持 Stash VPN/Tunnel 接管；IPv6 隧道路由使用 `Auto` 还是明确开启，以当前网络的实际接管和泄露测试为准，不必在 `Auto` 已通过时强制改动。此规则可能影响部分实时语音、视频通话或游戏联机。
- **DNS**：默认公共查询通过 AliDNS DoH 加密，但不等于一定通过代理。需让公共 DoH 跟随代理时选用 Privacy 配置；节点 DNS 和私有局域网 DNS 有独立路径。
- **分流**：国内和私有地址会依规则 `DIRECT`；`AdBlock`、服务组和 `Final` 的具体出口取决于设备上的策略选择。若有问题，先查看 Stash 请求记录，再核对规则命中。

## 项目结构

| 目录 | 内容 |
| --- | --- |
| `StashKit.yaml` | 唯一手工维护的主配置 |
| `StashKit-Privacy.yaml`、`StashKit-Local.yaml` | 由主配置确定性生成 |
| `rules/` | 54 份固定版本的 Stash 原生规则文件 |
| `build/` | 上游 SHA、来源锁、人工审查的规则调整记录 |
| `scripts/` | 规则生成、配置派生、校验与运行时审计 |
| `tests/` | 规则优先级、配置一致性和构建回归测试 |

规则文件的来源、格式及许可证见 [rules/README.md](./rules/README.md)。运行时不依赖 LoonKit 的插件、脚本或远程主分支。

## 开发与校验

```sh
git clone https://github.com/YohakuSama/stashkit.git
cd stashkit
git clone https://github.com/YohakuSama/loonkit.git upstream/loonkit
git -C upstream/loonkit checkout 5f272104fc1207612c1cbd18f3e19d861d459ed9
python -m pip install -r requirements-dev.txt
python scripts/build_profiles.py --check
python scripts/build_rules.py --check
python -m unittest discover -s tests -v
python scripts/verify.py
```

修改主 YAML 后用 `python scripts/build_profiles.py --write` 同步两份派生配置，再运行 `--check`。规则源修改通过 [build/adjustments.json](./build/adjustments.json) 审查，并需按固定源快照流程发布；不要直接修改生成文件。

## 文档导航

**使用与验收** · [路由策略](./docs/ROUTING.md) · [真机测试与离线安装](./docs/VALIDATION.md)

**维护与来源** · [架构及已知边界](./docs/ARCHITECTURE_AUDIT.md) · [变更记录](./docs/CHANGELOG.md) · [第三方版权声明](./docs/THIRD_PARTY_NOTICES.md)

[Issues](https://github.com/YohakuSama/stashkit/issues) · [License](./LICENSE)
