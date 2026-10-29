# LoonKit 策略组到 Stash 的节点选择

LoonKit 的 `ALL_Filter` 是节点筛选器，不是一个名为 `ALL` 的策略组。目标是让 `Proxy` 与 `ChatGPT` 等服务组都能直接选择订阅节点、`Auto` 和 `Fallback`。

## 公共配置（v0.1.10）：完整的 LoonKit 同层候选结构

默认 StashKit v0.1.10 在 `Proxy` 及 34 个服务选择组中同时设置 `proxies`（明确的 `Proxy` / `Auto` / `Fallback` 等策略候选）以及 `include-all: true`、`filter: '.*'`（订阅自动更新的实际节点）。不使用 `Manual` 或 `ALL`，也不要求订阅名称。该组合在公开 Stash 配置中已有使用，但其 iOS 版本的选择器显示需要在实际设备上确认。

以下本地生成器仅作为其他用户希望按特定节点表生成完整个人配置的可选工具，**公共正式版不需要它**。

## 已确认的行为与限制

Stash 支持 `proxies`（具体节点名或策略组名）、`use`（具名远程节点 Provider）以及 `include-all`（收集全部节点）。官方文档分别描述了这些字段，但并未保证 iOS 在混用 `include-all` 和显式 `proxies` 时总能同时展示两类选项。用户提供的 iOS 截图中，动态节点显示正常，但 `Auto` 和 `Fallback` 不在同一个策略组的可选列表中。

因此，不能再把 `include-all: true` 与 `proxies: [Proxy, Auto, Fallback]` 的静态组合当作完成验收。另一个方案 `use: [personal]` 则要求预先声明了相应 Provider，不能自动引用用户设备上的未知订阅。

## 原生 use-url：不指定订阅名称、无需每次更新节点后重新生成

Stash 官方文档的 `use-url` 可让策略组直接引用远程节点订阅 URL，不必声明或维护 `proxy-providers` 名称。与以前需要手动同步节点的 `--nodes-from` 不同，这种方式是**由 Stash 从 URL 获取节点**：当节点列表在订阅端变化时，不需要再次枚举节点名。

**必要条件：** 你必须拥有一个返回 Clash/Stash YAML（顶层包含 `proxies`）的 **HTTPS 节点订阅 URL**；仅在手机上手动添加了节点、没有订阅地址的用户无法使用这种模式。它不具备读取 iPhone 上另一个配置内部节点数据库的权限。你仍需要在自己的电脑上输入一次原有订阅 URL；**不需要设置 Provider 名称，更不需要额外的 Manual / ALL 策略组**。

把一个或多个订阅 URL 写到本地文件（每行一个），不要把私密 URL 作为终端命令参数或发送到公开仓库：

```sh
mkdir -p dist
# 在电脑上用文本编辑器新建 dist/subscriptions.txt，
# 填入原有 HTTPS 节点订阅 URL，每行一个。不要提交此文件。
python scripts/build_loon_selection.py \
  --subscription-file dist/subscriptions.txt \
  --output dist/StashKit-Loon-Private.yaml
```

生成的个人配置使用如下结构（仅示意；URL 请使用你自己本地保存的真实订阅）：

```yaml
proxy-groups:
  - name: Proxy
    type: select
    proxies:
      - REJECT
      - Auto
      - Fallback
    use-url:
      - https://example.org/private-node-subscription
  - name: ChatGPT
    type: select
    proxies:
      - Proxy
      - Auto
      - Fallback
    use-url:
      - https://example.org/private-node-subscription
```

`Auto`、`Fallback` 也引用同样的 `use-url`，以便它们测速、故障切换的候选池与手动选择的节点一致；`AdBlock`、`Final` 沿用原始策略候选，不重复导入节点。

这是 Stash **文档明确提供**的引用机制，而不是 `include-all` 与 `proxies` 混用时的未确认推断。CI 可以验证输出 YAML 结构、策略引用与保留的规则；依然必须在 iPhone 上检查订阅实际返回的格式、是否成功更新，以及节点和自动策略能否同时选择。

**安全：** `dist/subscriptions.txt` 和 `dist/StashKit-Loon-Private.yaml` 都会包含订阅访问凭证；项目的 `dist/` 已被 Git 忽略。不要将生成文件上传 GitHub 或共享给他人，也不要在 Stash 中重复叠加同一订阅，以免出现重名节点。Stash 内订阅刷新行为及间隔由 Stash 自身控制，`use-url` 不能自定义其名称或刷新周期。

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

本地生成方案已经纳入回归测试，但**仍需在 Stash iOS 上确认实际节点、Auto、Fallback 三种选项同时出现且可以切换**。CI 成功只代表 YAML 结构正确，不代表 iOS 控件已通过真机验收。公共版 v0.1.10 不再包含隐藏策略组；个人生成器仍是可选方式。

参考：[Stash 策略组](https://stash.wiki/proxy-protocols/proxy-groups) · [Stash 远程代理集](https://stash.wiki/proxy-protocols/proxy-providers)。
