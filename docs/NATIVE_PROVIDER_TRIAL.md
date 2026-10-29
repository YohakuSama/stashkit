# 生成 Loon 同层选路的 Stash 私有配置

正式生成器默认使用 `flat`：在本机读取或下载真实节点，把它们明确写入 Proxy、Auto、Fallback 和业务组，输出 39 个组，无 ALL、无固定 Provider 名称。下载只发生在自己的电脑与订阅源之间，不使用第三方订阅转换服务。

## 准备

在自己的电脑上克隆仓库并安装依赖：

```sh
git clone https://github.com/YohakuSama/stashkit.git
cd stashkit
python -m pip install -r requirements-dev.txt
mkdir -p dist
```

`dist/` 已被 Git 忽略。输入和生成结果都可能含节点密码、订阅 token 或认证头，不要上传到 GitHub。

## A. 已有 Clash/Stash YAML

将机场或 Stash 导出的 YAML 保存为 `dist/source.yaml`，其中应含 `proxies` 或 `proxy-providers`：

```sh
python scripts/build_loon_selection.py \
  --nodes-from dist/source.yaml \
  --output dist/StashKit-Personal.yaml
```

生成器读取实际节点名称与 Provider 名称，忽略来源里的业务组、DNS 和规则，使用 StashKit 的分流设置。Provider 有 URL 时获取最新节点；仅含 `path` 时相对输入 YAML 所在目录读取本地节点文件。常见 Provider 名称过滤及测速参数会应用到展开后的节点。多个来源按声明顺序合并，内容相同的同名节点去重，内容不同的同名节点需先在本地重命名。

## B. 只有订阅 URL

将一个或多个 HTTPS 订阅写入 `dist/subscriptions.txt`，每行一个；返回内容必须是带顶层 `proxies` 列表的 Clash/Stash YAML，URI 列表和 Base64 订阅需先由订阅服务提供对应 YAML 格式。

```sh
python scripts/build_loon_selection.py \
  --subscription-file dist/subscriptions.txt \
  --output dist/StashKit-Personal.yaml
```

也可把真实 Provider 写入本地 `dist/provider.stoverride`，按[示例](../overrides/provider.stoverride.example)添加 headers、filter 等配置，然后使用 `--provider-override dist/provider.stoverride`。无需固定叫 personal。

## 导入与更新

1. 在 Stash 中从文件导入生成的 `dist/StashKit-Personal.yaml`。
2. 检查 Proxy 是否明确列出 Auto、Fallback 和真实节点，再核对 ChatGPT 与 Apple 的选项。
3. 打开 Tunnel，在请求记录确认命中与出口，测试首选节点断开后的 Fallback 切换。
4. 订阅新增、删除或更名节点后，重新执行相同命令并重新导入；flat 文件不自动刷新订阅。现有节点的自动测速和故障切换仍可用。

生成器拒绝空订阅、过滤后无节点、无效节点、下载失败和策略名称冲突，不会覆盖旧结果；私有输出以仅本人可读写的权限原子保存。失败信息不打印私人 URL、节点名或凭据。

使用 `--profile privacy` 或 `--profile local` 可生成对应变体；Local 仍需按[离线安装说明](./VALIDATION.md)准备规则资源。

## 需要动态订阅自动更新时

公开[主配置](../StashKit.yaml)使用兼容布局：Proxy 明确列出 Auto/Fallback/ALL，只有三个节点池动态收集当前配置的节点。将自己的 Provider 加入同一份配置即可，不要求特定名称；通过 ALL 手动选节点。空 Provider 仍可能按 DIRECT 处理，启用前应确认已加载真实节点。

生成器的 `--layout nested` 会保留这个布局并绑定输入里的真实 Provider；`--layout native` 则把动态 Provider / use-url 直接附到 Proxy 和业务组，作为高级兼容试验。native 的动态节点与自动策略是否同层显示仍需真机检查；如遇选项缺失，使用默认 flat 或公开兼容布局。

`StashKit-Loon-Preview.yaml` 和 `StashKit-Native-Preview.yaml` 仅是需要自行声明 personal Provider 的参考片段，不是可直接使用的个人订阅。

官方语法与测速边界见[策略组适配说明](./LOON_POLICY_GROUPS.md)。
