# StashKit

为 [Stash](https://stash.wiki/) 提供的规则分流配置。与 [LoonKit v7.0.12](https://github.com/YohakuSama/loonkit/tree/edbfedad1b568578edc1a6dcebf422867a36a3ed) 的 40 个策略组及 Crypto / Paypal 排序保持一致，支持 AI、开发平台、流媒体、社交、游戏和国内服务分流。43 份远程规则继续使用经过验证的冻结快照，不自动追踪上游主分支。

当前配置：**v0.1.15** · [发布说明](./docs/RELEASE_NOTES_v0.1.15.md) · [更新记录](./docs/CHANGELOG.md) · [CI](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) · [许可证](./LICENSE)

## 选一个配置即可

| 使用场景 | 推荐下载 | 只需要修改 | 节点维护 |
| --- | --- | --- | --- |
| 机场 / 服务商提供订阅 URL | **[StashKit-Subscription.yaml](./StashKit-Subscription.yaml)** | proxy-providers → Airport → url | Stash 每 3600 秒刷新节点 |
| 自建 VPS / 单个自有代理节点 | **[StashKit-SelfHosted.yaml](./StashKit-SelfHosted.yaml)** | **顶层 proxies: 下的 SelfHosted 节点** | 修改本地 YAML，重新导入 |

[StashKit.yaml](./StashKit.yaml) 继续作为**订阅版的兼容主入口**，内容与 StashKit-Subscription.yaml 完全相同。两份推荐文件都包含完整分流规则和策略组，不必手动合并。下载到**本地**填写个人信息后，再从文件导入 Stash；不要直接启用尚未修改的公开示例。

## A. 机场订阅版：只改一行

打开 **StashKit-Subscription.yaml**，找到顶层的 proxy-providers：

~~~yaml
proxy-providers:
  Airport:
    url: 'https://example.invalid/REPLACE-WITH-YOUR-CLASH-SUBSCRIPTION'
    path: ./providers/stashkit-airport.yaml
    interval: 3600
~~~

**只把 url 改为你自己的 HTTPS Clash/Stash YAML 节点订阅链接**，保留英文单引号、Airport 名称和其余字段。订阅返回内容须包含顶层 proxies 节点列表；普通 URI / Base64 节点文本不能直接作为该 Provider 的 YAML 来源。

更新节点由 Stash 负责；40 个策略组中有 38 个使用 Airport，Auto、Fallback、Proxy 和业务组都能引用同一批节点。不要将包含 Token 的真实订阅地址提交到公开仓库。

## B. 自建节点版：只替换一个区块

打开 **[StashKit-SelfHosted.yaml](./StashKit-SelfHosted.yaml)**，在文件开头找到**顶层 proxies:**。这里的默认 Shadowsocks 仅为**无效占位示例**：

~~~yaml
proxies:
  - name: SelfHosted
    type: ss
    server: replace-me.invalid
    port: 443
    cipher: aes-128-gcm
    password: 'REPLACE-WITH-YOUR-PASSWORD'
~~~

把这一整个节点定义替换为你的真实 Stash / Clash 节点参数：

- **name**：保持 **SelfHosted**，否则必须同时修改各策略组中的节点名称引用。
- **type / server / port**：填你实际部署的协议、服务器地址和端口。
- **认证及协议字段**：根据你使用的 Shadowsocks、Trojan、VLESS 等协议填写对应参数；示例中的 cipher / password **只适用于 Shadowsocks**，不能直接用于其他协议。

**特别注意：修改的是顶层的 proxies:，不是 proxy-groups 里面的 proxies:**。后者仅表示策略组的候选节点名称，无需逐项改动。自建版已移除 Airport 订阅 Provider，Proxy、Auto、Fallback 及各业务组都直接引用 SelfHosted。默认只配置**一个**自建节点；需要多个自建节点时，建议使用下方的高级生成器为各组同步扩展节点，不要只在顶层增加名称而遗漏组引用。

不需要添加订阅 URL，也不需要额外放置本地 Provider 文件。服务器地址、UUID、密码、私钥等敏感信息只能填在自己的**本地副本**里。静态自建节点不会自动从服务器同步配置变动。

## 导入并检查

1. 把对应 YAML 保存到本地（例如「文件」App / iCloud Drive），替换真实订阅或节点信息；不要把带凭据的版本上传 GitHub。
2. 在 Stash 的配置文件管理中从**本地文件导入**，选中导入的配置并启动 Tunnel。
3. 检查策略组列表有 **40 组，无 ALL / Manual**。Proxy 应能选 Auto、Fallback 和真实节点；ChatGPT、Crypto 等业务组也应列出实际节点，自建版节点名称为 SelfHosted。
4. 在 Stash 请求记录中核对出口、Crypto 等规则命中、国内服务直连；测试节点断开、订阅刷新和 DNS。**空订阅或不可用节点不等于安全断网**，务必确认没有意外直连。

## 规则与其他版本

默认采用 Stash Fake-IP、AliDNS DoH、前置 STUN / 常见 TURN 端口拦截和 40 个原生策略组。WebRTC 防护只覆盖 Stash Tunnel 实际接管的流量；真实 DNS 泄露与 IPv6 表现需要设备测试。

| 文件 | 用途 |
| --- | --- |
| [StashKit-Subscription.yaml](./StashKit-Subscription.yaml) | **订阅版**，提供 Airport 自动更新 |
| [StashKit-SelfHosted.yaml](./StashKit-SelfHosted.yaml) | **自建版**，直接填写单个静态节点 |
| [StashKit.yaml](./StashKit.yaml) | 订阅版兼容主入口 |
| [StashKit-Privacy.yaml](./StashKit-Privacy.yaml) | 订阅版：公共 DoH 跟随路由并优先走 Proxy |
| [StashKit-Local.yaml](./StashKit-Local.yaml) | 订阅版：54 份规则文件需要事先安装到 Stash 资源目录 |
| [StashKit-ALL.yaml](./StashKit-ALL.yaml) | 旧版 ALL 入口兼容方案，非默认推荐 |

离线资源从 [CI](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) 或 [Releases](https://github.com/YohakuSama/stashkit/releases) 获取；仅下载 ZIP 不会自动将规则放到 Stash 受管目录。

## 高级用法与维护

多机场、多自建节点、已有完整 Stash/Clash 配置，可以使用 [配置生成器](./docs/NATIVE_PROVIDER_TRIAL.md) 从真实 Provider 或静态 proxies 生成独立的个人配置：

~~~sh
python -m pip install -r requirements-dev.txt
python scripts/build_loon_selection.py --nodes-from dist/source.yaml --output dist/StashKit-Personal.yaml
~~~

个人文件放在 Git 忽略的 dist/ 目录，不将 Token、节点密码上传至公开仓库。生成器可保留多个动态 Provider，或显式生成静态节点选择列表；自建版的单节点场景**不需要 Python**。

更多说明：[节点绑定](./docs/NATIVE_PROVIDER_TRIAL.md) · [路由与优先级](./docs/ROUTING.md) · [真机及离线资源验收](./docs/VALIDATION.md) · [策略组适配](./docs/LOON_POLICY_GROUPS.md) · [架构](./docs/ARCHITECTURE_AUDIT.md)。

开发校验：本仓库将 StashKit.yaml 作为派生配置的来源，编辑后运行 `python scripts/build_profiles.py --write`，再运行 `python scripts/build_profiles.py --check`、`python -m unittest discover -s tests -v` 和 `python scripts/verify.py`。需要先按照 [开发说明](./docs/VALIDATION.md) 准备固定版本的 LoonKit 源。策略组、规则和图标仍以冻结依赖为准。
