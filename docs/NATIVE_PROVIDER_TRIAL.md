# Stash 原生 Provider 同层选路实验

> **实验配置，不是默认正式版。** Stash 文档支持 `proxy-groups.proxies`、`proxy-groups.use` 和 `proxy-providers`，但它没有保证每个 iOS 版本都将策略组和远程节点同时显示在同一层。此前 `include-all` 混用方案已经在用户截图中出现显示缺失。这份实验通过明确的具名 Provider 来排查差异。

## 目标结构（不使用 ALL）

```text
Proxy
├── Auto
├── Fallback
├── 订阅节点 A
└── 订阅节点 B
```

`StashKit-Native-Preview.yaml` 是用于覆写 Provider 的完整配置预览，**不是不需配置订阅的直装版**。所有业务规则、DNS、广告拦截、图标与默认版一致，且不包含个人节点或订阅密钥。预览里要求你在 Stash 中提供一个确实存在的 `personal` Provider；没有该 Provider 时可能直接提示无效或无法加载节点。不要把试验版当成公开的即用订阅链接。

## 本地生成可导入的完整配置（推荐）

在你自己的电脑上克隆仓库，并把下面路径都放在 Git 忽略的 `dist/` 下。**不要把订阅 URL、用户名、密码上传到 GitHub。**

### A. 原生具名 Provider（`use`）

从 Stash/机场导出一个包含 `proxy-providers` 的 Clash/Stash YAML，保存为 `dist/source.yaml`：

```sh
mkdir -p dist
python scripts/build_loon_selection.py \
  --layout native \
  --nodes-from dist/source.yaml \
  --output dist/StashKit-Native-Personal.yaml
```

生成器会自动读取真实 Provider 名称，并将它们作为 `use` 加入 `Proxy`、`Auto`、`Fallback` 和各业务选择组。输出是完整配置，可直接在 Stash **从文件导入**。

若手头只有远程 Provider URL，可参考 [覆写示例](../overrides/provider.stoverride.example) 在本地写入 `dist/provider.stoverride`，把 `personal.url` 换成真实的 Clash/Stash YAML 节点集，再运行：

```sh
python scripts/build_loon_selection.py \
  --layout native \
  --provider-override dist/provider.stoverride \
  --output dist/StashKit-Native-Personal.yaml
```

### B. 无需填写 Provider 名称（`use-url`）

把一个或多个 **HTTPS** 节点订阅 URL 写入 `dist/subscriptions.txt`，每行一个，且返回的 YAML 顶层必须包含 `proxies`。本地执行：

```sh
python scripts/build_loon_selection.py \
  --layout native \
  --subscription-file dist/subscriptions.txt \
  --output dist/StashKit-Native-Personal.yaml
```

这也能测试同层动态节点选择，但相较具名 Provider，Stash 的 `use-url` 不能为 Provider 单独设置名称或刷新频率。

### C. 本地节点列表

如果手头只有包含具体节点的 `proxies` YAML，也可用 `--nodes-from` 生成；节点会被明确写进各组而非由 `use` 更新。这能绕过 Stash 动态合并 UI 的问题，**但订阅节点变化后需要重新生成文件**。

## 两种布局的区别

| 项目 | 正式默认布局 | 原生实验布局 |
| --- | --- | --- |
| 手动节点 | `Proxy → ALL → 节点` | 尝试 `Proxy → 节点` |
| `Auto` / `Fallback` | 引用策略组 | 引用策略组 |
| Provider | 只附加给 `Auto` / `Fallback` / `ALL` | 附加给 `Proxy`、`Auto`、`Fallback` 与业务组 |
| 国内直连和服务 DIRECT | 保留 | 保留 |
| 自动更新订阅 | Provider / use-url 模式可用 | Provider / use-url 模式可用 |
| Stash iOS 同层显示 | 不依赖混合动态选项 | **尚待真机验收** |

## 验收与风险

1. 在 Stash 中导入生成的 `dist/StashKit-Native-Personal.yaml` 并确认启用的是此配置；先**备份原配置**。
2. 检查 `Proxy` 是否同时列出 `Auto`、`Fallback` 和真实订阅节点；再检查 ChatGPT 与 Apple 服务组。
3. 确认 Apple、Microsoft、Bilibili、Line、Speedtest 首选 `DIRECT`，Steam 保留 `DIRECT` 选项，ChatGPT/Gemini/Claude 没有被自动设置为 DIRECT。
4. 测试订阅更新、断开首选节点、所有节点不可用、DNS、实际连接出口，而不只是检查 YAML 能加载。
5. **Stash 官方说明空远程代理集会被当作 `DIRECT`**：即使配置里另有 `REJECT` 选项，也不能假定空订阅一定不会走直连。运行验证前必须确认 Provider 已成功加载真实节点。

如果 Stash iOS 仍然隐藏 `Auto` / `Fallback`，不要将这个实验布局切到正式配置；继续使用 `ALL` 或基于具名节点的静态扁平生成方案。

参考：[Stash 远程代理集](https://stash.wiki/proxy-protocols/proxy-providers) · [Stash 策略组](https://stash.wiki/proxy-protocols/proxy-groups)。
