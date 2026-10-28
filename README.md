# StashKit

独立的 Stash 原生分流配置，基于 [LoonKit v7.0.10](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9) 正式规则。全部规则自本仓库托管，不依赖旧的 `loonkit/stashkit` 目录。

## 导入

**配置 URL：**

```text
https://raw.githubusercontent.com/YohakuSama/stashkit/main/StashKit.yaml
```

从 Stash 配置管理界面通过 URL 导入 [StashKit.yaml](./StashKit.yaml)。**需自行添加节点或兼容 Clash/Stash 的订阅**；项目不含个人节点或密钥。可参照 [订阅覆写示例](./overrides/provider.stoverride.example)，将 `example.invalid` 替换成合法的订阅 URL 后在 Stash 中应用。确认 Proxy、ALL、Auto、Fallback 节点池已加载并实际选路；Bing 测速不保证地区解锁。

## 规则与策略

- 从 LoonKit 43 份正式源文件生成 **54 个 Stash 原生规则集**：43 domain、7 ipcidr、4 classical ASN，共 **196,561** 条匹配器。
- 保留原有 39 个策略组，另新增 ALL 全量节点池（共 **40** 组）。保留策略首选项、规则优先级及 IP 子集 `no-resolve`。
- AdBlockBalanced **76,895** 条、ChinaDirect **114,705** 条按域名/IP 类型拆分；不把大型规则直接作为顺序匹配的 classical。
- Fake-IP + AliDNS DoH 与 LoonKit 使用习惯一致；DoH 不等于所有 DNS 必须经代理，也不保证绝对无 DNS 泄漏。
- 原 Loon 专用插件/脚本不冒充 Stash 兼容组件。

## 自动校验

[GitHub Actions](./.github/workflows/ci.yml) 校验：全量规则逐条一致、源 SHA256、重复项、类型语法、54 个引用地址、策略名称、匹配顺序及 YAML 结构。主分支还会通过 HTTP 实际下载全部 54 个规则集，比对字节完全一致，包括两个大型规则文件。

为保证可复现，源版本固定在 [LoonKit commit 5f272104](https://github.com/YohakuSama/loonkit/tree/5f272104fc1207612c1cbd18f3e19d861d459ed9)，防止上游改动自动变更生产策略。手动验证：

```sh
git clone https://github.com/YohakuSama/stashkit.git
cd stashkit
git clone https://github.com/YohakuSama/loonkit.git upstream/loonkit
git -C upstream/loonkit checkout 5f272104fc1207612c1cbd18f3e19d861d459ed9
python -m pip install 'PyYAML>=6,<7'
python scripts/verify.py
python scripts/check_remote.py
```

生成新规则：`python scripts/build_rules.py`，但更新 LoonKit 固定基准及主配置前必须审查变更，不能自动替换为 beta 候选。

**验证边界**：静态规则、配置语法和远程 HTTP 文件校验，不能替代 Stash iOS/macOS 真机导入、DNS、规则更新、性能、广告和流媒体解锁验收。

## 许可

遵循 [GPL-2.0-only](./LICENSE)，保留 [第三方声明](./docs/THIRD_PARTY_NOTICES.md) 及 LoonKit 规则来源。禁止提交私人订阅 URL 或节点凭据。
