# LoonKit 策略组在 Stash 中的对应方式

LoonKit 的 `ALL_Filter`、`Auto_Filter`、`Fallback_Filter` 是正则节点筛选器，不是独立策略组。目标行为：`Proxy` 和各服务策略组都可以选择 **Auto / Fallback / 订阅节点**；内置的 `DIRECT` 选项按原组保留。

## 为什么不直接用 include-all

Stash 官方提供两种不同的节点引用方式：

- `include-all: true`：从配置与订阅中收集全部节点，不需要知道 provider 名称。
- `use: [provider-name]`：从已命名的 `proxy-providers` 引用节点，可与 `proxies` 中的 `Auto` / `Fallback` 等明确选项配合。

用户提供的 iOS 截图已证明，在当前 Stash 环境中，`include-all` 和 `proxies` 混用时，服务组界面只出现实际节点，`Auto` / `Fallback` 没有出现在候选项中。所以不能把这样的组合当作已经通过真机验证。

完整保留 LoonKit 的动态节点和嵌套策略候选，必须知道**具名 provider**。仓库不能推断个人订阅在设备里的 provider 名称，也不应提交订阅 URL。

## 个人专属配置

[provider 覆写示例](../overrides/provider.stoverride.example) 使用 `personal` 作为 provider 名称。请在本地复制并填入真实订阅 URL，不要把带有凭据的文件上传到 GitHub。

```sh
cp overrides/provider.stoverride.example overrides/provider.stoverride
# Edit the URL locally, then generate:
python scripts/build_loon_selection.py \
  --provider-override overrides/provider.stoverride \
  --output dist/StashKit-Loon-Personal.yaml
```

如果使用 Privacy 或离线配置，加上 `--profile privacy` 或 `--profile local`。多个 provider 可以放在同一个本地覆写文件里，生成器会把它们统一引用到 `Proxy`、`Auto`、`Fallback` 及 34 个服务策略组。

生成文件是包含 provider 定义的**完整个人配置**，导入 Stash 时不需要再叠加相同的 provider 覆写。请保护它，因为可能包含订阅链接或鉴权信息。生成器只允许在项目的 `dist/`（已在 .gitignore 中忽略）或项目外保存。

## iOS 验收预览

分支上的 [StashKit-Loon-Preview.yaml](../StashKit-Loon-Preview.yaml) 使用 `use: [personal]`，**故意不包含个人订阅 URL**。只有当 Stash 对它应用了名为 `personal` 的 provider 覆写后，才是有效配置；没有覆写时不要直接启用预览文件。

预期 `ChatGPT`、`Gemini`、`Netflix` 等服务组会显示 `Proxy`、`Auto`、`Fallback` 和具名 provider 中的实际节点；`Proxy` 也应能直接选择自动策略和节点。必须在 Stash 真机界面与连接记录中验证，自动化只能证明配置结构和引用有效，不能代替 App 的界面测试。

参考：[Stash 策略组](https://stash.wiki/proxy-protocols/proxy-groups) · [远程代理集](https://stash.wiki/proxy-protocols/proxy-providers) · [配置覆写](https://stash.wiki/configuration/override)。

**现有正式版 v0.1.8 不受此试验影响。** 正式发布前需要在实际 iOS Stash 验证节点与 `Auto` / `Fallback` 确实同时显示、可切换，并检查断网及空订阅出口。
