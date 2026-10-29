# StashKit

面向 [Stash](https://stash.wiki/) 的规则分流配置。国内常用服务直连，AI、开发平台、流媒体与社交服务可独立选路。规则基于 [LoonKit v7.0.10 固定版本](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9) 转换，产物由本仓库托管。

当前配置：**v0.1.11** · [发布说明](./docs/RELEASE_NOTES_v0.1.11.md) · [变更记录](./docs/CHANGELOG.md) · [CI](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) · [GPL-2.0-only](./LICENSE)

## 功能概览

**服务分流** — 39 个与 LoonKit 对应的业务与策略组；公开配置额外提供 1 个 `ALL` 节点入口，覆盖 AI、流媒体、社交、开发平台和国内常用服务。广告由 `AdBlock` 处理。

**服务直连** — Apple、Microsoft、Bilibili、Line、Speedtest 可以默认选 `DIRECT`，Steam 可手动选 `DIRECT`；国内核心、国内 AI、SteamCN CDN 仍由规则直连。国际 AI 服务不自动增加直连。

**公开配置选路** — `Proxy` 保留 `Auto / Fallback / ALL / REJECT`，业务组保留 LoonKit 的默认策略和 DIRECT 选项；只有 `Auto / Fallback / ALL` 使用 `include-all` 收集当前配置中的节点和 Provider。无需固定的 Provider 名称或 `personal.yaml` 文件。节点池不再混入 `REJECT`。

**Loon 同层选节点（推荐）** — [本地生成器](./docs/NATIVE_PROVIDER_TRIAL.md)现在默认使用 `flat`：从本地节点文件或 HTTPS 订阅读取真实节点，生成 **39 个组**，让 `Proxy` 和业务组同时明确列出自动策略与具体节点，无 `ALL`，也不依赖动态混合显示。空订阅、过滤后无节点、重名冲突或下载失败时停止生成，保留旧输出。订阅节点变化后须重新运行生成器。

**节点来源** — 仓库不含私人节点。公开 YAML 须在**同一份生效配置**中加入自己的 `proxies` 或 `proxy-providers`，可使用任意 Provider 名称；另一个独立配置里的订阅不会因此自动合入。最直接的方式是本地生成包含真实节点的完整配置。订阅 URL 和节点密码只在自己的电脑上处理，不上传 GitHub。

**网络保护** — 使用 Stash Fake-IP、AliDNS 加密 DNS 和前置 STUN/常见 TURN 端口拦截规则。WebRTC 防护仅适用于被 Stash Tunnel 接管的连接。

## 快速开始

1. 备份现有配置，将自己的 Clash/Stash 节点 YAML 保存为 Git 忽略的 `dist/source.yaml`。
2. 按[生成说明](./docs/NATIVE_PROVIDER_TRIAL.md)执行 `python scripts/build_loon_selection.py --nodes-from dist/source.yaml --output dist/StashKit-Personal.yaml`；只有订阅 URL 时使用 `--subscription-file`。
3. 在 Stash 中从文件导入生成结果，确认 `Proxy` 同时显示 `Auto`、`Fallback` 和真实节点，Apple 等直连组保留 DIRECT。
4. 启用 Tunnel，在请求记录核对业务分流和真实出口；旧配置升级时已保存的策略选择可能保留。

如果需要 Provider 自动更新，可导入[公开主配置](https://raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.yaml)，并在当前配置中加入自己的 Provider。此布局通过 `Proxy → ALL → 节点` 手动选路。`StashKit-ALL.yaml` 等旧链接与当前兼容布局同步生成。

> [!IMPORTANT]
> Stash 官方说明空节点组或空 Provider 可能按 DIRECT 处理。公开 YAML 本身不提供节点；启用前确认真实节点已加载。`REJECT` 手动选项不能保证空订阅自动阻断。[运行时审计](./docs/VALIDATION.md)会检查各组成员、节点池及真实选择。

## 配置版本

| 配置 | 用途 |
| --- | --- |
| [StashKit.yaml](./StashKit.yaml) | 默认分流；公共 DNS 使用 AliDNS DoH，`follow-rule: false` |
| [StashKit-Privacy.yaml](./StashKit-Privacy.yaml) | 公共 DoH 请求跟随路由并优先走 `Proxy`；须先选择可用节点 |
| [StashKit-Local.yaml](./StashKit-Local.yaml) | 离线规则版；须先把 54 份文件规则放入 Stash 资源目录 |
| [StashKit-ALL.yaml](./StashKit-ALL.yaml) | 主配置的兼容链接；Privacy / Local 也有同步的 -ALL 链接 |

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

修改主 YAML 后用 `python scripts/build_profiles.py --write` 同步派生配置、兼容链接和参考预览，再运行 `--check`。规则源修改通过 [build/adjustments.json](./build/adjustments.json) 审查，并需按固定源快照流程发布；不要直接修改生成文件。

## 文档导航

**使用与验收** · [路由策略](./docs/ROUTING.md) · [真机测试与离线安装](./docs/VALIDATION.md)

**维护与来源** · [架构及已知边界](./docs/ARCHITECTURE_AUDIT.md) · [变更记录](./docs/CHANGELOG.md) · [第三方版权声明](./docs/THIRD_PARTY_NOTICES.md)

[Issues](https://github.com/YohakuSama/stashkit/issues) · [License](./LICENSE)
