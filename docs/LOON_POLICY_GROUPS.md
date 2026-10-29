# StashKit 策略组：LoonKit 兼容与直连服务

## 为什么采用 ALL 中转

LoonKit 的 `ALL_Filter` 是动态节点筛选器，可以和 `Auto` / `Fallback` 在同一层显示。Stash 官方支持 `include-all: true`、静态 `proxies` 和策略组嵌套，但没有明确保证 iOS 将“显式的 Auto/Fallback + 动态节点”在混合字段下同时显示。已有用户截图显示：实际 `Proxy` 列表只出现订阅节点，没有 Auto/Fallback。

因此公共 StashKit 采用明确且容易检查的二层选路：

```text
Proxy
├── Auto        # url-test，自动选节点
├── Fallback    # fallback，自动故障切换
└── ALL         # select，显示所有节点
    ├── 节点一
    └── 节点二
```

`Proxy` **不使用** `include-all`；`ALL` 使用 `include-all: true` 和 `filter: '.*'`，不会要求你的 Provider 名称或节点名称。Auto 和 Fallback 保留各自的动态节点池。35 个业务选择组也不再混合 `include-all` 和子策略，而是引用 `ALL`。这是跨版本的保守兼容方案：比 Loon 多一次点入 ALL，但不需要维护每次更新的节点名称。

```yaml
proxy-groups:
  - name: Proxy
    type: select
    proxies: [Auto, Fallback, ALL]
  - name: ALL
    type: select
    include-all: true
    filter: '.*'
    proxies: [REJECT]
  - name: Auto
    type: url-test
    include-all: true
    filter: '.*'
    proxies: [REJECT]
  - name: Fallback
    type: fallback
    include-all: true
    filter: '.*'
    proxies: [REJECT]
```

`REJECT` 是避免空组意外直连的显式兜底选项，但 `include-all` 与 `proxies` 混用时的具体运行时表现仍须在 Stash iOS 检查。Stash 官方提示空策略组可能视作 `DIRECT`，不要把空订阅的安全性建立在静态 YAML 推断上。若升级前 Stash 已记住旧的选中值，更新后手动重新选择 Auto。

## 与 LoonKit 保持一致的 DIRECT 服务

| 服务组 | 默认 | 可手动选择 |
| --- | --- | --- |
| Apple、Microsoft、Bilibili、Line、Speedtest | `DIRECT` | `Proxy` / `Auto` / `Fallback` / `ALL` |
| Steam | `Proxy` | `Auto` / `Fallback` / `DIRECT` / `ALL` |
| ChatGPT、Gemini、Claude 等国际服务 | `Proxy` | `Auto` / `Fallback` / `ALL` |

`DomesticCore`、`DomesticSupplement`、`DomesticAI` 和 `SteamCN` 由**规则直接路由** `DIRECT`，不依赖 `Proxy` 当前选项。`AdBlock` 与 `Final` 保持原有候选，所有域名遵循最先匹配的规则。不要在全局 `Proxy` 中增加 `DIRECT`，否则多个海外服务可能被一次操作同时放行。

## 私人订阅与生成器

公共仓库不保存个人节点或订阅密钥。若已有 Clash/Stash 格式的节点 YAML，可在本地运行：

```sh
mkdir -p dist
python scripts/build_loon_selection.py \
  --nodes-from dist/source.yaml \
  --output dist/StashKit-Loon-Personal.yaml
```

若有返回 Clash/Stash YAML 的 HTTPS 订阅 URL，将 URL 写入不提交 Git 的 `dist/subscriptions.txt`（每行一个），运行：

```sh
python scripts/build_loon_selection.py \
  --subscription-file dist/subscriptions.txt \
  --output dist/StashKit-Loon-Private.yaml
```

生成器把节点或 Provider 仅配置到 `Auto`、`Fallback`、`ALL`；服务策略组通过 `ALL` 间接选择节点。生成文件包含真实订阅凭据时不能上传 GitHub。若来源本身支持 `proxy-providers`，也可继续使用 `--provider-override` 模式。`StashKit-Loon-Preview.yaml` 仍是要求存在名为 `personal` 的 Provider 的示例，不能直接当成普通公共配置安装。

## 真机验收

在 Stash 的策略界面确认 `Proxy` 有 Auto / Fallback / ALL，进入 `ALL` 可选择真实节点。核实 Apple / Microsoft 等组的 `DIRECT`，检查国内服务是否直接命中 `DIRECT`，同时确认 ChatGPT 等走预期的代理。CI 静态校验不能代替 iOS 的真实 UI、空订阅行为和出站连接记录。

参考：[Stash 策略组](https://stash.wiki/proxy-protocols/proxy-groups) · [Stash 远程代理集](https://stash.wiki/proxy-protocols/proxy-providers)。
