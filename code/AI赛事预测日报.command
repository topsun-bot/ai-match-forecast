#!/bin/bash
# 《全球智库AI赛事预测日报》一键启动器（mac 双击运行）。
# 双击此文件 → 选模式 → 自动生成 HTML + PDF 报告并打开浏览器。
# 文本编辑器打开此文件即可改默认行为。
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

clear
echo "══════════════════════════════════════════"
echo "          全球智库AI赛事预测日报"
echo "══════════════════════════════════════════"
echo ""
echo "  1) 样刊模式      —— 内置样例数据 + 占位分析（秒出，不耗 token）"
echo "  2) 真实 AI 分析  —— 样例数据 + Gemini 真实决策（需 .env 填 GEMINI_API_KEY）"
echo "  3) 真实数据      —— API-Football 实时数据 + 真实分析（需 .env 填 API_FOOTBALL_KEY）"
echo "  4) 启动网页版    —— 本机浏览器打开报告列表页（可分享给局域网/公网）"
echo ""
read -p "请输入 1 / 2 / 3 / 4（直接回车=1）： " choice

echo ""
case "$choice" in
  2) python3 generate_report.py --pdf ;;
  3) python3 generate_report.py --pdf --data-tier paid --no-mock-data ;;
  4) python3 web_server.py; exit 0 ;;
  *) python3 generate_report.py --pdf --mock-llm ;;
esac

echo ""
echo "──────────────────────────────────────────"
echo "完成。报告在 reports/ 目录（.html 和 .pdf），浏览器应已自动打开。"
echo "按任意键关闭此窗口..."
read -n 1
