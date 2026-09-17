# 代码检查与维护

本仓库是组织检查试点。检查目标是 Python 生成器和发布工具的正确性、安全性及变更可追溯性；不验证赛事预测准确性、实时数据真实性或真实模型可用性。

## 日常开发

1. 从 main 创建工作分支；个人工具可使用 AGENTS.md / CLAUDE.md。
2. 安装 requirements-dev.txt 后运行 Ruff 和 unittest；全部例行测试离线执行。
3. 提交 PR，等待 Repository quality、CodeQL 及必要审查。
4. 修复失败项；新增可审查改动后重新获得批准。

初期 Ruff 只强制会影响运行的基础错误，不做全仓格式改写。Python 测试包括输出解析、mock 路由、HTML 转义、来源链接、历史报告归档、公开 artifact 白名单，以及 CI 汇总结果的失败／跳过处理。

## 组织必要检查

| 项目 | 行为 |
|---|---|
| lint | Python 语法、基础静态错误、Shell 语法 |
| tests | Python 3.11、3.12 上运行同一套离线测试 |
| dependency-review | PR 新增依赖若包含 high / critical 漏洞则失败 |
| ci-required | always 执行并核验依赖任务真实结果，异常 skipped、neutral、cancelled 或缺失均不放行 |
| CodeQL | 仓库安全设置覆盖 Python 与 Actions；告警严重度规则与扫描运行结果分别管理 |
| secret scanning / push protection | 使用仓库已启用的 GitHub 原生能力；不把没有告警当成所有类型密钥都能检测 |

PR 不设置路径过滤；纯文档 PR 也运行这套轻量检查。只有非 PR 的 push / 手动检查不适用依赖差异审查，ci-required 会明确说明。未运行或超时的 AI 审查必须标为未完成，不能伪装成通过。

## 合并与配置责任

目标规则为：main 通过 PR、至少一位非作者批准、撤销过期批准、Code Owner 审查、ci-required 成功、CodeQL 严重告警限制、禁止强推和删除。配置部署和实测结果以本次试点实施记录为准，不因文件存在就认定后台规则已生效。

仓库已有管理员团队 `@topsun-bot/topsun` 作为初始配置所有者。CODEOWNERS 覆盖工作流、检查入口、依赖与质量配置、审查指引及关键发布脚本。同一位符合条件的成员可同时完成普通审查和 Code Owner 审查，不能批准自己的 PR。

修改检查规则必须说明目的及是否减少覆盖；先在验收分支验证，再变更 main 的有效规则。不要为了通过当前 PR 删除测试、隐藏失败或扩大绕过权限。

## AI 审查

- Codex：仓库开启后使用 `@codex review`；规则在 AGENTS.md。
- Claude：需要相应服务授权。托管审查与 Actions 自建审查是两种不同方案；REVIEW.md 直接包含审查规则。
- Bugbot：需要服务授权，使用团队规则与 .cursor/BUGBOT.md；编辑器 .mdc 规则不会自动变成 PR 规则。

这些文件只是准备好的指引，并不证明服务已经接通。三家应分别完成真实 PR 验收，日常选择一家自动，其余按需。初期 AI 意见为辅助，不取代必要 CI 与人工批准。

## 自动日报发布

源代码在 main，自动生成的站点历史在 site-content；日报更新不直接提交 main。
Pages artifact 仅包含 index.html、.nojekyll 和符合命名要求的日报 HTML，排除源代码、凭据及符号链接。

- 定时／手动真实运行：需要有效 GEMINI_API_KEY；API 错误应保留失败记录，不能靠替换成 mock 来证明真实服务恢复。
- 手动 mock：只供离线预览，不更新 site-content，不部署 Pages。
- main 合并：重建归档站点，不触发真实模型调用。

切换步骤：合并已审查配置 → 将 Pages Source 改为 GitHub Actions → 运行并验证一次已有报告发布 → 查看站点 → 保留运行记录。切换前保存 Pages 原来源，若发布失败，先恢复已知可用的发布配置，不关闭代码合并保护。

2026-09-17 盘点发现，原定时任务的真实模型调用返回 HTTP 401。凭据需由有权限的维护者在 Secrets 中处理；离线测试通过不意味着此问题已解决。

## 验收与排错

最少核验：正常 PR、测试失败、必要任务被跳过、上游失败、取消／结果缺失、获批后追加代码、检查配置修改、个人工具停用、适用的 fork / Dependabot PR。
记录仓库、提交 SHA、PR、实际 job 结果、规则与批准状态。独立人员批准相关用例需要真实非作者参与，不能通过另一个机器人冒充人审。

依赖工具或账号能力受限时，单列限制和负责人员；不要把未开通、未运行、未测试写成已完成。当前运行、权限和验收事实保存在试点实施记录中。
