# 全球智库AI赛事预测日报 · GitHub Pages 站点

本仓库是《全球智库AI赛事预测日报》的公开静态站点，通过 GitHub Pages 托管。

## 部署配置

| 项 | 值 |
|---|---|
| 平台 | GitHub Pages（纯静态，无 Jekyll，根目录有 `.nojekyll`） |
| 生产地址 | https://topsun-bot.github.io/ai-match-forecast/ |
| 仓库地址 | https://github.com/topsun-bot/ai-match-forecast |
| 部署触发 | push 到 `main` 分支自动生效（GitHub Pages 原生，无需 Action） |
| 健康检查 | 访问生产地址，首页列出日报即为正常 |
| 合并方式 | 本地直接 commit 到 main（单人维护，不走 PR） |
| 项目类型 | 纯静态 HTML 报告站（非应用） |

## 目录结构

```
ai-match-forecast-site/
├── index.html              # 首页（自动列出所有日报，深蓝金色风格）
├── .nojekyll               # 跳过 Jekyll，直接 serve 原始 HTML
├── README.md               # 本文件
└── 日报-YYYY-MM-DD.html     # 每日报告（自包含，CSS 内联）
```

## 更新流程（每天出报告后）

源码与生成脚本在**主仓库**（不公开）：`huazhijian/subprojects/ai_match_predictor/`。

```bash
cd ~/Documents/huazhijian/subprojects/ai_match_predictor
bash publish_to_github.sh
```

该脚本会：① 复制最新报告 + 刷新首页到本部署目录 ② commit ③ push ④ 确认 Pages 开启。

## 本地预览

不部署也能看：双击 `AI赛事预测日报.command` 选 `4)`，本机 `localhost:8000` 预览所有日报。

## 免责声明

报告由 AI 基于公开比赛数据与模拟专家观点自动生成，仅作技术演示，不构成投注/投资建议。
