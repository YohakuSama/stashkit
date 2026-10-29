# StashKit v0.1.13 — 正式主配置内直接添加订阅

正式的 [StashKit.yaml](../StashKit.yaml) 现在直接包含 `proxy-providers.Airport` 和自动更新引用。将文件下载到本地，仅替换 `url: 'https://example.invalid/REPLACE-WITH-YOUR-CLASH-SUBSCRIPTION'` 为自己的 HTTPS Clash/Stash YAML 节点订阅地址，保存后导入 Stash；无需可视化编辑或 Python 生成器。

StashKit-Privacy.yaml 和 StashKit-Local.yaml 同步采用该结构；StashKit-Subscription.yaml 作为兼容别名继续存在。主配置保持 39 个分流策略组，Proxy 包含 Auto、Fallback、REJECT，节点由具名 Airport Provider 直接供各组使用，每小时自动刷新。原有服务默认顺序、DNS、STUN 保护、规则、固定资源快照和图标保持不变。

高级 Python 生成器继续支持多个具名 Provider、use-url 和静态节点；它会自动移除公开配置中的无效演示 Provider，避免私人输出同时混入占位来源。

**安全提示：** `example.invalid` 地址故意不可用。请仅在设备本地填写真实订阅 URL（常包含 Token），不要将其提交到公开 GitHub。CI 只检查结构、规则与生成一致性，不能代替 Stash 真机检查实际节点加载、Proxy 中 Auto/Fallback 是否可选、订阅更新和断线时出口。
