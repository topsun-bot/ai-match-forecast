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
| 部署触发 | push 到 `main` 分支自动生效（GitHub Pages 原生，无需 Action） |
| 健康检查 | 访问生产地址，首页列出日报即为正常 |
| 合并方式 | 本地直接 commit 到 main（单人维护，不走 PR） |
| 项目类型 | 纯静态 HTML 报告站 + Python 生成器源码 |

## 目录结构

```
ai-match-forecast-site/  (仓库根，GitHub Pages 从这里 serve)
├── index.html              # 报告站首页（深蓝金色，自动列出日报）
├── 日报-YYYY-MM-DD.html     # 每日报告（自包含，CSS 内联）
├── .nojekyll               # 跳过 Jekyll，直接 serve 原始 HTML
├── README.md               # 本文件
└── code/                   # 生成器源代码（Pages 不 serve .py，仅作存档）
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

**安全**：`.env`（含 API key）已被 `.gitignore` 排除，不会推送到本仓库。key 模板见 `code/.env.example`。

## 更新流程

### 每天出报告后（更新公网站点）

```bash
cd ~/Documents/huazhijian/subprojects/ai_match_predictor
bash publish_to_github.sh
```

该脚本会：① 复制最新报告 + 刷新首页到根目录 ② 同步代码到 `code/` ③ commit ④ push ⑤ 确认 Pages 开启。

### 改了代码后

同一条命令 `bash publish_to_github.sh`，代码也会一起同步推送。

## 本地预览

不部署也能看：双击 `code/AI赛事预测日报.command` 选 `4)`，本机 `localhost:8000` 预览所有日报。

## 免责声明

报告由 AI 基于公开比赛数据与模拟专家观点自动生成，仅作技术演示，不构成投注/投资建议。
