# StashKit

为 [Stash](https://stash.wiki/) 提供的规则分流配置。与 [LoonKit v7.0.12](https://github.com/YohakuSama/loonkit/tree/edbfedad1b568578edc1a6dcebf422867a36a3ed) 的 40 个策略组及 Crypto / Paypal 排序保持一致，支持 AI、开发平台、流媒体、社交、游戏和国内服务分流。43 份远程规则继续使用经过验证的冻结快照，不自动追踪上游主分支。

当前配置：**v0.1.17** · [发布说明](./docs/RELEASE_NOTES_v0.1.17.md) · [更新记录](./docs/CHANGELOG.md) · [CI](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) · [许可证](./LICENSE)

## 规则解耦与精简

**正式主配置约 280 行**（原来 983 行），没有删除 LoonKit 对应的 40 个策略组或业务分流。之所以能变短，是把 YAML 的重复展开改为简洁的 Stash 原生写法，并将 Crypto 的 29 条后缀规则提取成独立远程规则集。

- 原有 **54 份按业务划分的远程规则**继续使用 v0.1.4 固定快照，不追踪可变 main；新 **Crypto-domain** 规则集也固定到不可变提交。共有 55 份远程文件规则集，使用 `rule-providers` 声明及 `RULE-SET` 分流。
- 40 个策略组、Provider 声明使用**单行 YAML 映射**，缩短文件但仍是同一份 YAML 标准对象；并非将节点或规则数据混入主配置。
- 133 条 **Private-local** 私网匹配器仍内嵌为短列表，避免局域网 DNS 在冷启动时依赖 Github 下载，防止影响 `localhost`、`.lan`、私有反查等规则。其余路由和节点按需引用远程规则 / 代理来源。
- `Local` 离线版仍需把 54 份冻结资源和新 Crypto 文件（分别放入 `rules/v0.1.4/`、`rules/v0.1.17/`）安装到 Stash 受管目录。默认在线版从 GitHub Raw 按需下载并缓存。Stash 支持后台静默更新这些 Rule Set，缓存路径固定，详见 [官方规则集合文档](https://stash.wiki/rules/rule-set)。

## 选一个配置即可

| 使用场景 | 推荐下载 | 只需要修改 | 节点维护 |
| --- | --- | --- | --- |
| 机场 / 服务商提供订阅 URL | **[StashKit-Subscription.yaml](./StashKit-Subscription.yaml)** | proxy-providers → Airport → url | Stash 每 3600 秒刷新节点 |
| 自建 VPS / 一个或多个自有代理节点 | **[StashKit-SelfHosted.yaml](./StashKit-SelfHosted.yaml)** | **顶层 proxies: 下的节点列表** | 修改本地 YAML，重新导入 |

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

## B. 自建节点版：支持直接粘贴 1～N 个节点

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

把顶层 **proxies:** 换成自己的节点列表即可。**v0.1.16 起，节点名可以随意填写（不能重复），1 个或 3 个或更多个都能自动出现在代理策略组中**。无需把所有节点都命名成 SelfHosted，也不需要修改其他 38 个组。

下面是三个 Shadowsocks 节点的示例结构，所有服务器地址和密码都是无效占位，需替换为自己的实际参数：

~~~yaml
proxies:
  - name: 香港节点
    type: ss
    server: hk.example.invalid
    port: 443
    cipher: aes-128-gcm
    password: 'REPLACE-HK-PASSWORD'
  - name: 日本节点
    type: ss
    server: jp.example.invalid
    port: 443
    cipher: aes-128-gcm
    password: 'REPLACE-JP-PASSWORD'
  - name: 美国节点
    type: ss
    server: us.example.invalid
    port: 443
    cipher: aes-128-gcm
    password: 'REPLACE-US-PASSWORD'
~~~

**注意事项：**

- 整个 YAML 只能有**一个顶层 proxies:**，三个节点依次以 `  - name:` 开头、保持相同缩进，不能重复写三个顶层 proxies:。
- 每个节点需有**唯一的 name**、正确的 type / server / port 和对应协议认证参数。以上 type: ss 仅为 Shadowsocks 示例；Trojan、VLESS 等要使用自己的协议字段。
- **不需要修改 proxy-groups 下的 proxies:**。自建版的 Proxy、Auto、Fallback 和业务组使用 Stash 官方支持的 `include-all: true`，自动载入顶层所有本地节点；AdBlock 与 Final 仍保持原有策略选项。
- 如果 Stash 中仍只显示旧节点，请先确认导入并**启用了新版本的个人 YAML**，而不是仍在使用旧的 v0.1.15 配置或订阅版。修改完成后要从文件重新导入/切换到新配置，再查看 Proxy / Auto / ChatGPT 的节点列表。
- 若配置导入失败，优先检查 YAML 缩进、重复的顶层字段、重名、协议字段及端口是否有效。敏感信息只填在本地文件，勿上传公开仓库。

自建节点信息不会自动从服务器更新；修改时需要重新导入个人 YAML。不需要订阅 URL，也不需要额外本地 Provider 文件。[官方策略组说明](https://stash.wiki/proxy-protocols/proxy-groups)。

## 导入并检查

1. 把对应 YAML 保存到本地（例如「文件」App / iCloud Drive），替换真实订阅或节点信息；不要把带凭据的版本上传 GitHub。
2. 在 Stash 的配置文件管理中从**本地文件导入**，选中导入的配置并启动 Tunnel。
3. 检查策略组列表有 **40 组，无 ALL / Manual**。Proxy 应能选 Auto、Fallback 和真实节点；ChatGPT、Crypto 等业务组也应列出实际节点，自建版显示你所填写的全部节点名称。
4. 在 Stash 请求记录中核对出口、Crypto 等规则命中、国内服务直连；测试节点断开、订阅刷新和 DNS。**空订阅或不可用节点不等于安全断网**，务必确认没有意外直连。

## 规则与其他版本

默认采用 Stash Fake-IP、AliDNS DoH、前置 STUN / 常见 TURN 端口拦截和 40 个原生策略组。WebRTC 防护只覆盖 Stash Tunnel 实际接管的流量；真实 DNS 泄露与 IPv6 表现需要设备测试。

| 文件 | 用途 |
| --- | --- |
| [StashKit-Subscription.yaml](./StashKit-Subscription.yaml) | **订阅版**，提供 Airport 自动更新 |
| [StashKit-SelfHosted.yaml](./StashKit-SelfHosted.yaml) | **自建版**，直接填写多个静态节点 |
| [StashKit.yaml](./StashKit.yaml) | 订阅版兼容主入口 |
| [StashKit-Privacy.yaml](./StashKit-Privacy.yaml) | 订阅版：公共 DoH 跟随路由并优先走 Proxy |
| [StashKit-Local.yaml](./StashKit-Local.yaml) | 订阅版：55 份规则文件需要事先安装到 Stash 资源目录 |
| [StashKit-ALL.yaml](./StashKit-ALL.yaml) | 旧版 ALL 入口兼容方案，按兼容格式保留较长 YAML，非默认推荐 |

离线资源从 [CI](https://github.com/YohakuSama/stashkit/actions/workflows/ci.yml) 或 [Releases](https://github.com/YohakuSama/stashkit/releases) 获取；仅下载 ZIP 不会自动将规则放到 Stash 受管目录。

## 高级用法与维护

多机场、复杂的自建节点编排、已有完整 Stash/Clash 配置，可以使用 [配置生成器](./docs/NATIVE_PROVIDER_TRIAL.md) 从真实 Provider 或静态 proxies 生成独立的个人配置：

~~~sh
python -m pip install -r requirements-dev.txt
python scripts/build_loon_selection.py --nodes-from dist/source.yaml --output dist/StashKit-Personal.yaml
~~~

个人文件放在 Git 忽略的 dist/ 目录，不将 Token、节点密码上传至公开仓库。生成器可保留多个动态 Provider，或显式生成静态节点选择列表；自建版的单节点场景**不需要 Python**。

更多说明：[节点绑定](./docs/NATIVE_PROVIDER_TRIAL.md) · [路由与优先级](./docs/ROUTING.md) · [真机及离线资源验收](./docs/VALIDATION.md) · [策略组适配](./docs/LOON_POLICY_GROUPS.md) · [架构](./docs/ARCHITECTURE_AUDIT.md)。

开发校验：本仓库将 StashKit.yaml 作为派生配置的来源，编辑后运行 `python scripts/build_profiles.py --write`，再运行 `python scripts/build_profiles.py --check`、`python -m unittest discover -s tests -v` 和 `python scripts/verify.py`。需要先按照 [开发说明](./docs/VALIDATION.md) 准备固定版本的 LoonKit 源。策略组、规则和图标仍以冻结依赖为准。
