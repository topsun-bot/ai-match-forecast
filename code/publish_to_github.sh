#!/bin/bash
# 推送赛事预测日报到 GitHub Pages（topsun-bot 组织公开仓库）。
# ⚠ 此脚本会：① 在 topsun-bot 组织下创建公开仓库 ② push 报告内容 ③ 开启 Pages。
# ⚠ 首次运行前请确认：仓库公开化 OK、报告内容无敏感信息。
set -e

cd "$(dirname "$0")"
SITE_DIR="$HOME/Documents/ai-match-forecast-site"
REPO_FULL="topsun-bot/ai-match-forecast"   # 组织/仓库名（在 topsun-bot 组织下新建）
ORG="topsun-bot"
REPO="ai-match-forecast"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

gh api user >/dev/null 2>&1 || { echo "✗ gh 未登录，先跑 gh auth login"; exit 1; }

echo "=== 1/4 同步最新报告 + 代码到部署目录 ==="
python3 publish_site.py --site-dir "$SITE_DIR"
python3 sync_code.py --site-dir "$SITE_DIR"

cd "$SITE_DIR"

echo ""
echo "=== 2/4 Git 提交 ==="
if [ ! -d ".git" ]; then
  git init -b main >/dev/null
  git add -A && git commit -m "首次部署：全球智库AI赛事预测日报" >/dev/null
  echo "  首次提交完成"
else
  git add -A
  git commit -m "更新日报 $(date +%Y-%m-%d)" >/dev/null && echo "  新提交完成" || echo "  无新改动"
fi

echo ""
echo "=== 3/4 创建远程仓库并推送（首次）/ 直接推送（之后）==="
if git remote get-url origin >/dev/null 2>&1; then
  git push
else
  echo "  → 在 $ORG 组织下创建公开仓库 $REPO_FULL ..."
  gh repo create "$REPO_FULL" --public --source=. --push
fi

echo ""
echo "=== 4/4 开启 GitHub Pages ==="
if gh api "repos/$REPO_FULL/pages" >/dev/null 2>&1; then
  echo "  Pages 已开启"
else
  gh api -X POST "repos/$REPO_FULL/pages" -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 \
    && echo "  Pages 已开启" \
    || echo "  ⚠ 自动开 Pages 失败，请网页开：https://github.com/$REPO_FULL/settings/pages"
fi

echo ""
echo "══════════════════════════════════════════════════════"
echo "✓ 部署完成。Pages 生效需几分钟，访问地址："
echo "  https://$ORG.github.io/$REPO/"
echo ""
echo "仓库地址：https://github.com/$REPO_FULL"
echo "══════════════════════════════════════════════════════"
