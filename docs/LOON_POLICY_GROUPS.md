# LoonKit 策略组到 Stash 的节点选择

LoonKit 的 `ALL_Filter` 是节点筛选器，不是一个名为 `ALL` 的策略组。目标是让 `Proxy` 与 `ChatGPT` 等服务组都能直接选择订阅节点、`Auto` 和 `Fallback`。

## 公共配置（v0.1.9）：无需指定订阅名称

默认配置使用 `Proxy` 的显式 `Auto` / `Fallback` / `Manual` 选项；`Manual` 是 `hidden: true` 的 `include-all` 动态节点池。这样 Stash 可以把自动策略和直接选节点的入口分别展示，不需要用户配置 `use: [personal]`。

选择 `Proxy → Auto` 后，所有跟随 `Proxy` 的服务组共同使用自动测速策略；选择 `Proxy → Manual` 后可进入 `Manual` 手动选实际节点。**此公共配置不具备 LoonKit 同层列出自动策略和全部节点的体验**，但保留了动态订阅自动更新。

以下本地生成器用于需要所有选项直接出现在同一列表的个人配置。

## 已确认的行为与限制

Stash 支持 `proxies`（具体节点名或策略组名）、`use`（具名远程节点 Provider）以及 `include-all`（收集全部节点）。官方文档分别描述了这些字段，但并未保证 iOS 在混用 `include-all` 和显式 `proxies` 时总能同时展示两类选项。用户提供的 iOS 截图中，动态节点显示正常，但 `Auto` 和 `Fallback` 不在同一个策略组的可选列表中。

因此，不能再把 `include-all: true` 与 `proxies: [Proxy, Auto, Fallback]` 的静态组合当作完成验收。另一个方案 `use: [personal]` 则要求预先声明了相应 Provider，不能自动引用用户设备上的未知订阅。

## 无需手动指定 Provider 名称的生成方式

`scripts/build_loon_selection.py` 现在可以**读取已有的 Clash/Stash 节点 YAML**，自动提取其中的 `proxies` 节点名称和 `proxy-providers` Provider 名称。生成的完整配置中：

- `Proxy` 有 `REJECT`、`Auto`、`Fallback` 及具体节点名；有 Provider 时自动附加 `use`。
- `ChatGPT`、`Gemini`、`Netflix` 等服务组有 `Proxy`、`Auto`、`Fallback` 及具体节点名；有 Provider 时自动附加 `use`。
- `Auto` 和 `Fallback` 从相同的节点和 Provider 中选择，保留现有测速频率与策略优先级。
- `AdBlock`、`Final` 不会被注入无关节点，原来的服务路由规则、DNS、WebRTC 和规则快照不变。

在个人电脑本地使用：

```sh
mkdir -p dist
# 把现有的 Clash/Stash 节点 YAML 导出为 dist/source.yaml
python scripts/build_loon_selection.py \
  --nodes-from dist/source.yaml \
  --output dist/StashKit-Loon-Personal.yaml
```

`--profile privacy` 或 `--profile local` 可选用其他配置变体。**不需要填写 Provider 名称，也不需要向 GitHub 提交订阅 URL 或私钥。** 生成的 YAML 是可直接导入 Stash 的完整个人配置，不要再次叠加同一份节点订阅，以免出现重复名称。

`dist/` 在 `.gitignore` 中忽略。输入和输出可能包含节点密码、UUID、订阅凭据，**只保存在本地**，不要上传 Issues、PR、公共网盘或聊天记录。

### 更新订阅后的维护

节点名称或 Provider 列表变化后，需要重新运行生成命令并在 Stash 中更新个人配置。生成器不会在 iPhone 后台读取当前 Stash 的节点数据库。这是“完全不指定 Provider 名称”和“在同一组显示具体节点与自动策略”的代价；仅靠仓库中的一份公共静态 YAML 无法推断未来的私有节点名称。

如果现有来源本身含 `proxy-providers`，生成器会自动读取所有键名，无需指定 `personal`。原先的 `--provider-override` 仍可用于已有的具名 Provider 工作流。

## 当前的预览状态

[StashKit-Loon-Preview.yaml](../StashKit-Loon-Preview.yaml) 仍是**具名 Provider 的示例**，引用 `personal`，不是免配置的通用订阅 URL。不要在没有相应 Provider 覆写时直接启用它。

本地生成方案已经纳入回归测试，但**仍需在 Stash iOS 上确认实际节点、Auto、Fallback 三种选项同时出现且可以切换**。CI 成功只代表 YAML 结构正确，不代表 iOS 控件已通过真机验收。公共版 v0.1.9 采用上面的隐藏 `Manual` 兼容方案；个人生成器仍是可选方式。

参考：[Stash 策略组](https://stash.wiki/proxy-protocols/proxy-groups) · [Stash 远程代理集](https://stash.wiki/proxy-protocols/proxy-providers)。
