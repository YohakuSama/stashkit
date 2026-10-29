# 无 ALL 的动态订阅绑定

默认 `native` 输出 39 个与 LoonKit 对应的策略组。Proxy 和业务组直接引用节点 Provider，保留 Auto/Fallback 和原有 DIRECT 选项。真实节点由 Stash 的 `use` 或 `use-url` 加载，订阅更新后不需要重新生成节点列表。

## 无需生成器：直接编辑 YAML

正式主配置现在直接填写订阅链接：下载 [StashKit.yaml](../StashKit.yaml) 到本地，把 `proxy-providers.Airport.url` 的 `example.invalid` URL 改成 HTTPS Clash/Stash YAML 节点订阅，再在 Stash 从文件导入。无需可视化编辑或 Python。

所有 37 个需要节点的组显式使用 `use: [Airport]`，保留 `Proxy` 内的 `Auto`、`Fallback` 和 `REJECT`，每 3600 秒自动更新 Provider。若添加多个机场，请增加 `proxy-providers` 条目，并将名称加入需要节点的策略组 `use`。私人订阅可能含 Token，**切勿推送到公开 GitHub**。导入后要确认节点非空并检查实际策略选择。

下文的生成器方法继续适合复杂、多机场和高级绑定需求；StashKit-Subscription.yaml 仅为兼容别名。

## 首次准备

公开 `StashKit.yaml`、Privacy、Local 已声明 `Airport` Provider，但其 URL 是无效占位地址。简单使用无需生成器，在本地填真实 URL 即可。以下仅说明复杂多来源使用时如何通过生成器替换示例 Provider：

```sh
git clone https://github.com/YohakuSama/stashkit.git
cd stashkit
python -m pip install -r requirements-dev.txt
mkdir -p dist
```

输入和输出可能含订阅 token、节点密码或认证头；`dist/` 已被 Git 忽略，生成文件仅本人可读写。无需将订阅上传到公开仓库。

## A. 只有订阅 URL

将一个或多个 HTTPS 订阅写入 `dist/subscriptions.txt`，每行一个。返回内容应为带顶层 `proxies` 的 Clash/Stash YAML；URI 或 Base64 列表应先向订阅服务选择对应 YAML 格式。

```sh
python scripts/build_loon_selection.py \
  --subscription-file dist/subscriptions.txt \
  --output dist/StashKit-Personal.yaml
```

默认生成 `use-url` 动态引用，命令不会下载后固化成静态节点。Stash 负责获取与更新节点；use-url 不能自定义 Provider 名称或刷新间隔，需要这些参数时使用下面的具名 Provider 方式。

## B. 已有 Provider

将包含 `proxy-providers` 的 Stash YAML 保存为 `dist/source.yaml`。名称可以任意，生成器读取实际名称并绑定到所有需要节点的组：

```sh
python scripts/build_loon_selection.py \
  --nodes-from dist/source.yaml \
  --output dist/StashKit-Personal.yaml
```

Provider 的 URL、interval、headers、filter、path 和测速参数原样保留。URL 型 Provider 可自动更新；仅有 path 的来源仍是 Stash 受管资源目录中的本地静态 Provider，需自行提供资源文件。来源中的 DNS、业务组和规则不会覆盖 StashKit 的分流逻辑。

也可基于[示例](../overrides/provider.stoverride.example)创建本地 `dist/provider.stoverride`，然后使用 `--provider-override dist/provider.stoverride`。不能把未替换的示例 URL 当成有效订阅。

如果输入只有 `proxies` 而没有远程来源，输出只能保留静态节点；需要后台更新时请使用 URL 或 URL 型 Provider。

## 导入与验证

1. 在 Stash 中从文件导入完整的 `dist/StashKit-Personal.yaml`。
2. 检查总计 39 个策略组，无 ALL/Manual。Proxy 同时显示 Auto、Fallback 与真实节点；ChatGPT 等业务组同时显示策略和节点；Apple 等直连组的 DIRECT 顺序保持不变。
3. 更新订阅，检查节点新增、移除或更名是否同步到 Auto/Fallback、Proxy 和业务组，无需重新生成。修改订阅 URL、认证或 Provider 名称时才需要重新绑定。
4. 启用 Tunnel，查看请求记录并测试 Fallback 断线切换；通过[运行时审计](./VALIDATION.md)逐组核对实际成员，不能只看 Auto 能用。

```sh
python scripts/stash_runtime_audit.py \
  --base-url http://127.0.0.1:9090 \
  --profile dist/StashKit-Personal.yaml
```

控制器密钥通过 STASH_API_TOKEN 环境变量传入。公开配置只包含无效订阅占位符，不能用于证明真实订阅已通过验收。

默认 native 不下载订阅内容，因此生成成功仅证明引用与结构有效；必须在 Stash 中确认 Provider 已加载非空真实节点。官方说明空 Provider 可能用 DIRECT 替代，Proxy 中的 REJECT 手动选项不能保证空订阅阻断。运行时审计会拒绝这种替代。

`--profile privacy` / `--profile local` 选择相应模板。Local 仍需按[安装说明](./VALIDATION.md)准备 54 份规则文件。

## 显式兼容选项

- `--layout flat`：下载或读取真实节点并展开为 39 组静态列表。空源、过滤后为空或下载失败时保留旧输出；节点变化后需重新生成。
- `--layout nested`：保留旧的 ALL 中间入口。`StashKit-ALL.yaml` 等文件只为主动选择旧布局的用户保留，正式默认不用它们。

两份 Preview 仅是需要自行声明 personal Provider 的旧参考配置。正式使用直接运行默认生成器即可，不需要先经过 Preview。

Stash 实际的同层显示、节点连通与断线行为仍需在你的 App 版本验收。源码回归与 CI 不能代替真机，见[策略组适配说明](./LOON_POLICY_GROUPS.md)。
