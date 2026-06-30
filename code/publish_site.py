#!/usr/bin/env python3
"""把 reports/ 的日报同步到 GitHub Pages 部署目录，生成静态首页。
【本地操作，不 push、不联网】—— 安全可逆。配合 publish_to_github.sh 推送。

用法：python3 publish_site.py [--site-dir PATH]
默认部署目录：~/Documents/ai-match-forecast-site（在 huazhijian 外，独立仓库）
"""
import os
import re
import shutil
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(HERE, "reports")
DEFAULT_SITE_DIR = os.path.expanduser("~/Documents/ai-match-forecast-site")


def _scan():
    items = []
    for fn in os.listdir(REPORTS_DIR):
        if fn.startswith("日报-") and fn.endswith(".html"):
            m = re.search(r"(\d{4}-\d{2}-\d{2})", fn)
            items.append((m.group(1) if m else fn, fn))
    items.sort(key=lambda x: x[0], reverse=True)
    return items


def _index_html(reports):
    rows = "".join(
        f'<li><a href="{fn}"><span class="date">{date}</span><span class="go">查看 →</span></a></li>'
        for date, fn in reports
    )
    empty = '<li class="empty">还没有报告。先在本地生成一份。</li>' if not reports else ""
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>全球智库AI赛事预测日报</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:"PingFang SC","Noto Sans CJK SC","Microsoft YaHei",-apple-system,sans-serif;
    background:#060d1f; color:#e6edf7; min-height:100vh; display:flex;
    flex-direction:column; align-items:center; padding:60px 20px; }}
  .card {{ max-width:560px; width:100%; }}
  .brand {{ color:#c9a96e; font-size:12px; letter-spacing:4px; text-transform:uppercase; }}
  h1 {{ font-size:30px; margin:6px 0 4px; font-weight:700; }}
  .tagline {{ color:#8ba3c7; font-size:13px; margin-bottom:30px; }}
  ul {{ list-style:none; }}
  li a {{ display:flex; justify-content:space-between; align-items:center;
    padding:20px 24px; background:#0a1b33; border:1px solid #1c3358;
    border-radius:10px; margin-bottom:12px; color:#e6edf7; text-decoration:none;
    font-size:18px; transition:.15s; }}
  li a:hover {{ border-color:#c9a96e; background:#13293f; }}
  .date {{ font-weight:600; }}
  .go {{ color:#c9a96e; font-size:14px; }}
  .empty {{ color:#8ba3c7; font-size:14px; padding:18px 0; list-style:none; }}
  .footer {{ margin-top:34px; padding-top:20px; border-top:1px solid #1c3358;
    color:#5f7aa0; font-size:12px; line-height:1.9; }}
</style></head><body><div class="card">
  <div class="brand">Global Think Tank · AI Match Forecast</div>
  <h1>全球智库AI赛事预测日报</h1>
  <div class="tagline">AI 多源数据决策台 · 赛事预测存档</div>
  <ul>{rows}{empty}</ul>
  <div class="footer">由 AI 基于公开比赛数据与模拟专家观点自动生成，仅作技术演示，不构成投注/投资建议。</div>
</div></body></html>"""


def main():
    p = argparse.ArgumentParser(description="同步日报到 GitHub Pages 部署目录（本地，不 push）")
    p.add_argument("--site-dir", default=DEFAULT_SITE_DIR)
    args = p.parse_args()
    reports = _scan()
    os.makedirs(args.site_dir, exist_ok=True)
    # .nojekyll：让 GitHub Pages 直接 serve 原始 HTML，跳过 Jekyll（保护中文文件名/下划线文件不被过滤）
    open(os.path.join(args.site_dir, ".nojekyll"), "w").close()
    copied = 0
    for _, fn in reports:
        shutil.copy2(os.path.join(REPORTS_DIR, fn), os.path.join(args.site_dir, fn))
        copied += 1
    with open(os.path.join(args.site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(_index_html(reports))
    print(f"✓ 已同步 {copied} 份日报到：{args.site_dir}")
    print(f"✓ 静态首页 index.html 已生成")
    print(f"  本地准备完成。下一步：bash publish_to_github.sh 推送（需你确认）。")


if __name__ == "__main__":
    main()
