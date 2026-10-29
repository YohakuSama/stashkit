# 直接使用机场远程订阅（不编辑 YAML）

StashKit 的移动端推荐用法是 **机场/服务商的完整 Clash/Stash YAML 作为当前配置**，再安装 **StashKit 远程覆写**。与把 StashKit.yaml 当作主配置不同，这种方式不会要求个人订阅地址预先写在公开文件里，也不需要运行 Python 生成器。

## Stash 操作（无需代码编辑器）

1. 打开 Stash → 设置 → 配置文件 → **从 URL 下载**，粘贴机场提供的 Clash/Stash YAML 订阅 URL。选中这个机场配置作为当前配置。
2. 用 Safari 点击 [一键安装 StashKit 远程覆写](https://link.stash.ws/install-override/raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.stoverride)，确认安装并启用。也可使用原始地址：`https://raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.stoverride`。
3. 返回 Stash，重新载入当前配置或重启 Tunnel。策略页面应有 39 组：Proxy 的 Auto/Fallback/REJECT 和订阅的真实节点、Auto/Fallback 的节点列表，以及 ChatGPT、YouTube 等业务组的 Proxy/Auto/Fallback 与具体节点。
4. 通过 Stash 的订阅更新刷新机场配置后，再检查新增、删除的节点是否同步进入相关策略组。可同时从 Stash 更新远程覆写，无需修改订阅 URL，也无需重新生成本地文件。

*机场订阅地址可能含 token，请仅输入 Stash 自己的配置 URL 框，不要粘贴到公共 Issue、日志、仓库或覆写地址中。*

## 与 LoonKit 的对应关系

LoonKit 用 `[Remote Filter]` 定义 `ALL_Filter / Auto_Filter / Fallback_Filter = .*`，并将其作为 Proxy、Auto/Fallback 和业务组的动态候选。

StashKit 的远程覆写使用 Stash 的 `include-all: true` 收集**当前配置内**的 `proxies` 和 `proxy-providers`：
- Proxy：保留 Auto / Fallback / REJECT 手动选项，并直接列出节点。
- Auto / Fallback：动态使用当前节点进行延迟或故障切换。
- 34 个业务组：保留原来的 Proxy / Auto / Fallback / DIRECT 次序，并动态列出节点。
- AdBlock / Final：保留固定的原始策略，不重复插入节点。

完整覆写通过 `#!replace` 替换 `proxy-groups`、`rules`、`rule-providers` 和 `dns`，使上游机场策略不覆盖 StashKit 的分流顺序；**不设置** `proxies` 和 `proxy-providers`，因此由原机场配置负责节点和订阅更新。官方语法参考：<https://stash.wiki/proxy-protocols/proxy-groups>、<https://stash.wiki/configuration/override>。

## 限制和排查

- **机场必须提供有效的 Clash/Stash YAML**，至少含真实 `proxies` 或可用的 `proxy-providers`。仅有 SS/V2Ray URI 或 Base64 节点列表需要在机场订阅端切换格式。StashKit 不读取另一个**未激活**配置的节点。
- Stash 的 **远程配置订阅**负责更新普通 `proxies`；含 `proxy-providers` 的完整配置还会使用 Provider 自己的更新机制。
- `include-all` 的实际效果以本机 Stash 版本为准；仓库自动测试验证结构和 LoonKit 策略顺序，不代表已经在 iOS/macOS 的策略页面验收。若策略列表出现只有节点没有 Auto/Fallback、某个服务组缺少节点等情况，请注明 Stash 版本并提供**隐藏订阅地址/凭据**的截图。
- 机场当前节点集为空时，Stash 可能把空策略组/Provider 当作 DIRECT，请先确认节点列表确实非空，切勿把 `REJECT` 候选当作断网保护。
- 因为 `#!replace` 是完全替换，不要同时启用其他重写这四个字段的覆写；原机场的自定义规则、策略组及 DNS 会被 StashKit 替换。
- 如果想使用 StashKit 作为**主配置 URL**并在另一配置里单独添加机场订阅，两份独立配置的节点不会自动合并。此时应采用本页的「机场配置 + 远程覆写」模式，而非导入空模板。
- 已有配置用 `scripts/build_loon_selection.py` 绑定节点的原工作流仍然保留，适用于希望维护独立个人配置文件的用户。

覆写从 `StashKit.yaml` 自动派生，`python scripts/build_profiles.py --check` 会检查它与主配置是否同步。
