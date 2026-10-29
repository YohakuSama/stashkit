# StashKit

面向 [Stash](https://stash.wiki/) 的规则分流配置。国内常用服务直连，AI、开发平台、流媒体与社交服务可独立选路。规则基于 [LoonKit v7.0.10 固定版本](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9) 转换，产物由本仓库托管。

当前配置：**v0.1.10** · [发布说明](./docs/RELEASE_NOTES_v0.1.10.md) · [变更记录](./docs/CHANGELOG.md) · [CI](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) · [GPL-2.0-only](./LICENSE)

## 功能概览

**服务分流** — 39 个与 LoonKit 一致的业务与策略组，覆盖 AI、流媒体、社交、开发平台和国内常用服务。广告由 `AdBlock` 处理。

**服务直连** — Apple、Microsoft、Bilibili、Line、Speedtest 可以默认选 `DIRECT`，Steam 可手动选 `DIRECT`；国内核心、国内 AI、SteamCN CDN 仍由规则直连。国际 AI 服务不自动增加直连。

**原生节点选路（正式版）** — `StashKit.yaml` 现在采用 Stash 原生 `proxy-providers` + `use`，**没有 `ALL` 策略组**。`Proxy` 明确含 `Auto` / `Fallback` / `REJECT`，并直接引用名为 `personal` 的节点 Provider；业务组也直接引用相同 Provider。目标是同层显示节点及自动策略，仍须在 Stash iOS 验证。

**私人订阅设置（必须）** — 仓库不含订阅地址。默认配置使用 Stash 官方支持的本地 Provider：`proxy-providers.personal.path: ./providers/personal.yaml`；使用前须提供该文件，或将 `personal` 覆写为自己的真实 HTTPS 订阅，否则可能没有节点或落入 `DIRECT`。推荐通过[本地生成器](./docs/NATIVE_PROVIDER_TRIAL.md)创建包含真实订阅的完整私有配置，不要上传订阅密钥。

**回退方案** — 如 Stash iOS 无法同时显示 Auto/Fallback 和 Provider 节点，可以随时使用保留的 [StashKit-ALL.yaml](./StashKit-ALL.yaml) 兼容配置（Privacy / Local 也有对应备份）。见[策略组说明](./docs/LOON_POLICY_GROUPS.md)。

**网络保护** — 使用 Stash Fake-IP、AliDNS 加密 DNS 和前置 STUN/常见 TURN 端口拦截规则。WebRTC 防护仅适用于被 Stash Tunnel 接管的连接。

## 快速开始

1. **备份**现有 Stash 配置和节点订阅；切换到原生配置前准备好 `personal` 节点来源。
2. 在 Stash 中通过 URL 导入[主配置](https://raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.yaml)。
3. 先将 `personal` Provider 连接到自己的有效订阅：本地生成完整配置（推荐），或添加 `./providers/personal.yaml` 文件/修改[订阅覆写示例](./overrides/provider.stoverride.example)。
4. 更新配置后，检查 `Proxy` 是否同层显示 `Auto`、`Fallback` 和真实节点。若没有，使用 `StashKit-ALL.yaml` 回退。
5. 启动 Stash VPN/Tunnel，在请求记录中检查分流与实际出口。

> [!IMPORTANT]
> **重要：** 未配置 `personal` 时，此公开配置没有可用的代理节点；Stash 官方指出空 Provider 可能按 `DIRECT` 处理。`REJECT` 候选不能代替真机验证。请先通过[本地生成器](./docs/NATIVE_PROVIDER_TRIAL.md)输出完整个人配置或正确配置本地 Provider，再启用 VPN。

## 配置版本

| 配置 | 用途 |
| --- | --- |
| [StashKit.yaml](./StashKit.yaml) | 默认分流；公共 DNS 使用 AliDNS DoH，`follow-rule: false` |
| [StashKit-Privacy.yaml](./StashKit-Privacy.yaml) | 公共 DoH 请求跟随路由并优先走 `Proxy`；须先选择可用节点 |
| [StashKit-Local.yaml](./StashKit-Local.yaml) | 离线规则版；须先把 54 份文件规则放入 Stash 资源目录 |
| [StashKit-ALL.yaml](./StashKit-ALL.yaml) | 旧版兼容布局，Proxy → ALL → 具体节点；其他两个变体也有 -ALL 备份 |

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
