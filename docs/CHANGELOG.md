# 变更记录

## v0.1.3 图标恢复补丁 — 2026-10-29

- 原版 39 张 PNG 逐字节复制到 StashKit 自己的 `icons/`，不再使用旧 LoonKit 的外部图标链接。
- 普通、严格 DNS、本地规则版的 40 个策略组全部恢复自托管图标，ALL 复用 Proxy 图标。
- 增加校验图片 Git blob、PNG 文件头、策略组引用和 GitHub Raw 下载的回归测试；规则、DNS、节点配置不变。

## v0.1.3 — 2026-10-29

- 54 个规则订阅 URL 固定到不可变 Git commit；加入版本缓存 path，防止跨版本混用并复用本地规则。
- 提供完整路径本地版 `StashKit-Local.yaml`、确定性离线 ZIP 及 CI 工作流产物；首次离线安装仍需手动放入 Stash 受管资源目录，不宣称一键导入。
- 加入独立 `StashKit-Privacy.yaml` 及可选 DNS 隐私覆写，按 Stash 原生规则转发 AliDNS DoH，明确适用条件与残余直连。
- 移除对 LoonKit 固定 commit 图标的运行时依赖，回退到 Stash 默认图标。

## v0.1.2 — 2026-10-29

- Proxy 策略组默认改为 `REJECT`，避免空代理订阅被 Stash 替换为 `DIRECT` 后通过 Auto/Fallback 意外直连。必须在加入可用节点后手动选择 Proxy 出口；旧配置要核对已保存的策略。
- CI 增加默认 Proxy 安全出口回归测试，明确 Auto/Fallback 用户强制选择且空订阅时仍可能存在直连风险。

## v0.1.1 — 2026-10-29

- 私有域名使用限定的系统 DNS policy；内网域名和地址在公共分流之前直连。
- 测速参数改为 provider 级 benchmark-url / benchmark-timeout。
- GitHub 组控制 Raw 域名；SteamCN 优先接管已有的国内 CDN 精确域名。
- 動畫瘋的 HiNet 范围缩小到两个已知 CDN，移除通用 DigiCert 范围。
- 配置校验增加字段类型、策略引用环和覆写示例检查；DNS 探测校验完整成功应答。
- 源清单及输入摘要固定在本仓库，规则生成可逐字节复现；失败输入在写入前被拒绝。
- 补齐原始许可文本、历史来源材料和有效链接，注明最低 Stash 版本与真机验证边界。

上述更改不代表已经完成流媒体解锁、空订阅阻断或真机性能验收，验收方法见[验证步骤](./VALIDATION.md)。
