# StashKit

面向 [Stash](https://stash.wiki/) 的规则分流配置。国内常用服务直连，AI、开发平台、流媒体与社交服务可独立选路。规则基于 [LoonKit v7.0.10 固定版本](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9) 转换，产物由本仓库托管。

当前配置：**v0.1.12** · [发布说明](./docs/RELEASE_NOTES_v0.1.12.md) · [变更记录](./docs/CHANGELOG.md) · [CI](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) · [GPL-2.0-only](./LICENSE)

## 功能概览

**服务分流** — 39 个与 LoonKit 对应的业务与策略组，无 `ALL`、`Manual` 或其他中间选择组，覆盖 AI、流媒体、社交、开发平台和国内常用服务。广告由 `AdBlock` 处理。

**服务直连** — Apple、Microsoft、Bilibili、Line、Speedtest 可以默认选 `DIRECT`，Steam 可手动选 `DIRECT`；国内核心、国内 AI、SteamCN CDN 仍由规则直连。国际 AI 服务不自动增加直连。

**无 ALL 的同层选路（默认）** — [生成器](./docs/NATIVE_PROVIDER_TRIAL.md)默认使用 `native`，将真实 Provider 的 `use` 或订阅的 `use-url` 直接绑定到 `Proxy`、`Auto`、`Fallback` 与业务组。`Proxy` 保留 Auto/Fallback，业务组保留 Loon 的默认策略及 DIRECT 选项，具体节点从同一动态来源导入。没有二层 ALL 入口，也不使用 include-all 混合选择。

**订阅更新** — 输入 Provider 时保留名称、URL、刷新间隔、认证头、过滤条件与缓存路径；节点增删由 Stash 更新，不需要重新运行生成器。只有 URL 时可用 `--subscription-file`，通过 Stash 的 use-url 自动管理；需要自定义刷新间隔时使用具名 Provider。只有静态 proxies 的输入仍为静态节点。

**手机端远程订阅（推荐）** — 不需要 Python、编辑器或将私人订阅地址写入仓库。在 Stash 中从 URL 导入机场 Clash/Stash 配置，再[一键安装 StashKit 远程覆写](https://link.stash.ws/install-override/raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.stoverride)。39 个策略组中的节点相关组使用 `include-all` 动态读取当前订阅的节点；机场配置负责远程更新。[安装与限制](./docs/REMOTE_SUBSCRIPTION.md)。

**独立配置模板（进阶）** — 三份公开 YAML 仍是不含私人节点的 **39 组模板**，`use: []` 表示尚未绑定，不能单独当作完整个人配置直接启用。若需要 StashKit 作为独立主配置文件，可使用生成器绑定自己的订阅或 Provider。不同配置的节点不会跨文件自动合并。

**网络保护** — 使用 Stash Fake-IP、AliDNS 加密 DNS 和前置 STUN/常见 TURN 端口拦截规则。WebRTC 防护仅适用于被 Stash Tunnel 接管的连接。

## 快速开始

**手机端无需编辑器（推荐）：** 在 Stash 的「设置 → 配置文件」中从 URL 导入并启用自己的 Clash/Stash 机场订阅，然后点击[安装 StashKit 远程覆写](https://link.stash.ws/install-override/raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.stoverride)。安装并启用覆写后，刷新订阅即可动态同步 Proxy、Auto、Fallback 和业务组的节点。详见[远程订阅指南](./docs/REMOTE_SUBSCRIPTION.md)。

**需要输出独立个人 YAML 的进阶方式：**

1. 备份现有配置，将包含 `proxy-providers` 的 Clash/Stash YAML 保存为 Git 忽略的 `dist/source.yaml`；或者将 HTTPS 订阅逐行保存为 `dist/subscriptions.txt`。
2. 执行 `python scripts/build_loon_selection.py --nodes-from dist/source.yaml --output dist/StashKit-Personal.yaml`；只有 URL 时将 `--nodes-from dist/source.yaml` 替换为 `--subscription-file dist/subscriptions.txt`。默认 native 保留动态更新。
3. 在 Stash 中从文件导入生成结果，检查 Proxy 和业务组是否同时列出 Auto/Fallback 与真实节点；确认总计 39 组且无 ALL。
4. 更新订阅并检查节点增删；启用 Tunnel 后在请求记录核对实际出口。使用[运行时审计](./docs/VALIDATION.md)检查每个组是否包含当前订阅的节点。

`--layout flat` 是明确选择的静态快照模式，节点变化后才需要重新生成。`StashKit-ALL.yaml` 等旧版兼容配置保留供主动选择，正式默认不再使用它们。完整步骤见[订阅绑定说明](./docs/NATIVE_PROVIDER_TRIAL.md)。

> [!IMPORTANT]
> Stash 官方说明空节点组或空 Provider 可能按 DIRECT 处理。公开模板尚未绑定节点，须先生成完整个人配置；动态订阅是否非空需在 Stash 中确认。`REJECT` 手动选项不能保证空订阅自动阻断。[运行时审计](./docs/VALIDATION.md)会检查各组成员、节点池及真实选择。

## 配置版本

| 配置 | 用途 |
| --- | --- |
| [StashKit.yaml](./StashKit.yaml) | 默认分流；公共 DNS 使用 AliDNS DoH，`follow-rule: false` |
| [StashKit-Privacy.yaml](./StashKit-Privacy.yaml) | 公共 DoH 请求跟随路由并优先走 `Proxy`；须先选择可用节点 |
| [StashKit-Local.yaml](./StashKit-Local.yaml) | 离线规则版；须先把 54 份文件规则放入 Stash 资源目录 |
| [StashKit-ALL.yaml](./StashKit-ALL.yaml) | 可选的旧版 ALL 兼容布局；不属于默认 39 组方案 |

离线文件包可从 [CI 产物](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) 获取。ZIP 不会自动安装到 Stash 的规则目录；详见[安装及验收说明](./docs/VALIDATION.md)。

## 使用与排查

- **WebRTC / IPv4 / IPv6**：三套配置前置拦截 `STUN` 和常见 STUN/TURN 目的端口。保持 Stash VPN/Tunnel 接管；IPv6 隧道路由使用 `Auto` 还是明确开启，以当前网络的实际接管和泄露测试为准，不必在 `Auto` 已通过时强制改动。此规则可能影响部分实时语音、视频通话或游戏联机。
- **DNS**：默认公共查询通过 AliDNS DoH 加密，但不等于一定通过代理。需让公共 DoH 跟随代理时选用 Privacy 配置；节点 DNS 和私有局域网 DNS 有独立路径。
- **分流**：国内和私有地址会依规则 `DIRECT`；`AdBlock`、服务组和 `Final` 的具体出口取决于设备上的策略选择。若有问题，先查看 Stash 请求记录，再核对规则命中。

## 项目结构

| 目录 | 内容 |
| --- | --- |
| `StashKit.yaml` | 39 组独立主模板，使用它时需绑定私有节点来源 |
| `StashKit-Privacy.yaml`、`StashKit-Local.yaml` | 由主配置确定性生成 |
| [`StashKit.stoverride`](./StashKit.stoverride) | **推荐手机端**：为机场远程订阅套用 39 组策略和 StashKit 规则，不覆盖节点来源 |
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
