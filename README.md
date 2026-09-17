# 全球智库AI赛事预测日报 · GitHub Pages 站点 + 源代码

本仓库托管两样东西：
1. **《全球智库AI赛事预测日报》公开站点**（GitHub Pages，根目录）
2. **生成器源代码**（`code/` 子目录）

## 部署配置

| 项 | 值 |
|---|---|
| 平台 | GitHub Pages（纯静态，无 Jekyll，根目录有 `.nojekyll`） |
| 生产地址 | https://topsun-bot.github.io/ai-match-forecast/ |
| 仓库地址 | https://github.com/topsun-bot/ai-match-forecast |
| 部署触发 | 迁移后使用 Pages Actions：main 合并后重建站点；定时任务生成并自动发布日报 |
| 健康检查 | 访问生产地址，首页列出日报即为正常 |
| 合并方式 | 工作分支提交 PR；必要检查和非作者审查通过后合并 |
| 项目类型 | 纯静态 HTML 报告站 + Python 生成器源码 |

## 目录结构

```
ai-match-forecast-site/  (仓库根，GitHub Pages 从这里 serve)
├── index.html              # 报告站首页（深蓝金色，自动列出日报）
├── 日报-YYYY-MM-DD.html     # 每日报告（自包含，CSS 内联）
├── .nojekyll               # 跳过 Jekyll，直接 serve 原始 HTML
├── README.md               # 本文件
└── code/                   # 生成器源代码；新 Pages artifact 只包含 HTML 报告
    ├── generate_report.py      # CLI 入口
    ├── data_provider.py        # 数据采集（API-Football）
    ├── llm_router.py           # 多模型抽象（Gemini/GLM/GPT）
    ├── analyst.py              # 球评模拟 + 决策
    ├── render.py + report_template.html  # 渲染
    ├── export_pdf.py           # Chrome 无头 PDF
    ├── web_server.py           # 本地网页服务器
    ├── publish_site.py         # 报告同步脚本
    ├── sync_code.py            # 代码同步脚本
    ├── publish_to_github.sh    # 一键发布脚本
    ├── AI赛事预测日报.command    # Mac 双击启动器
    ├── config_data.py / config_models.py  # 配置
    ├── requirements.txt / .env.example    # 依赖与 key 模板
    └── 数据源技术尽调-2026-06.md  # 数据源技术尽调报告
```

本地凭据由 `.gitignore` 排除，key 模板见 `code/.env.example`。PR 检查使用离线样例，不读取生产凭据。

## 更新流程

### 修改代码

从最新 main 创建工作分支，修改后提交 PR。运行本地检查：

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m ruff check code scripts tests
python3 -m unittest discover -s tests -v
```

GitHub 上的 `ci-required` 验证静态检查、Python 3.11/3.12 测试及适用的依赖审查。
CodeQL 和密钥检查另行提供安全证据。个人 AI 自检不能替代组织检查。

### 自动日报与 Pages

迁移后，定时任务继续在北京时间 08:00 / 20:00 运行；报告历史保存到
`site-content` 分支，Pages 从仅含 HTML 的 artifact 发布，任务不再写入 source main。
main 合并时只重建历史站点，不调用付费模型。手动 `mock=true` 只生成预览 artifact，
不会归档或公开发布样例。

部署迁移需要在本 PR 合并后，将仓库 Settings → Pages 的 Source 设为
GitHub Actions，并验证首次发布。具体合并保护、工具接入状态和维护步骤见
[工程检查与维护说明](docs/engineering-checks.md)。

旧的 `code/publish_to_github.sh` 仅可用于已有工作分支，不再允许直接提交 main。

## 本地预览

不部署也能看：双击 `code/AI赛事预测日报.command` 选 `4)`，本机 `localhost:8000` 预览所有日报。

## 免责声明

报告由 AI 基于公开比赛数据与模拟专家观点自动生成，仅作技术演示，不构成投注/投资建议。
