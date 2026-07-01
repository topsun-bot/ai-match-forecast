#!/bin/bash
# 本地定时任务：生成《全球智库AI赛事预测日报》+ 推送到公网。
# 替代被 billing 锁的 GitHub Actions。由 crontab 定时调用。
# 依赖：gh 已登录、本地 .env 有 GEMINI_API_KEY、网络能访 Gemini API。
# 日志：由 crontab 条目重定向到日志文件，本脚本只负责串流程。
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
cd /Users/zhang/Documents/huazhijian/subprojects/ai_match_predictor || { echo "✗ 找不到项目目录"; exit 1; }

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 开始生成当日日报（Gemini grounding）==="
if ! python3 generate_report.py --model gemini-2.5-pro --no-mock-data --no-open; then
  echo "⚠ 生成失败（可能休赛无比赛 / 网络问题），跳过本次推送。"
  exit 1
fi

echo "=== 推送到公网（topsun-bot/ai-match-forecast）==="
bash /Users/zhang/Documents/huazhijian/subprojects/ai_match_predictor/publish_to_github.sh

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 完成 ==="
