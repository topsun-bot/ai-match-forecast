#!/usr/bin/env python3
"""《全球智库AI赛事预测日报》本地网页服务器。零依赖（仅标准库）。
启动后浏览器自动打开首页，列出所有已生成的日报，点击查看。

用法：
    python3 web_server.py              # 默认端口 8000
    python3 web_server.py --port 8080

发给别人看：本服务只在你的电脑上（localhost）。要公网分享，用 ngrok（临时 URL）
或部署到 GitHub Pages（永久 URL）——见使用说明。
"""
import os
import re
import argparse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, unquote

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(HERE, "reports")
REPORTS_REAL = os.path.realpath(REPORTS_DIR)


def _scan_reports():
    """扫描 reports/ 下的日报 HTML，按日期倒序返回 [(date, filename), ...]。"""
    if not os.path.isdir(REPORTS_DIR):
        return []
    items = []
    for fn in os.listdir(REPORTS_DIR):
        if fn.startswith("日报-") and fn.endswith(".html"):
            m = re.search(r"(\d{4}-\d{2}-\d{2})", fn)
            items.append((m.group(1) if m else fn, fn))
    items.sort(key=lambda x: x[0], reverse=True)
    return items


def _render_index(reports):
    rows = "".join(
        f'<li><a href="/reports/{fn}"><span class="date">{date}</span><span class="go">查看 →</span></a></li>'
        for date, fn in reports
    )
    if not reports:
        rows = '<li class="empty">还没有报告。先双击「AI赛事预测日报.command」生成一份。</li>'
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
  .hint {{ margin-top:34px; padding-top:20px; border-top:1px solid #1c3358;
    color:#5f7aa0; font-size:12px; line-height:1.9; }}
  .hint b {{ color:#8ba3c7; }}
</style></head><body><div class="card">
  <div class="brand">Global Think Tank · AI Match Forecast</div>
  <h1>全球智库AI赛事预测日报</h1>
  <div class="tagline">AI 多源数据决策台 · 赛事预测存档</div>
  <ul>{rows}</ul>
  <div class="hint">
    <b>本页为本地预览</b>（仅你的电脑可见）。生成新报告请双击「AI赛事预测日报.command」。<br>
    <b>发给别人看</b>：用 ngrok 生成临时公网链接，或部署到 GitHub Pages 获得永久地址。
  </div>
</div></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", ""):
            self._send_html(_render_index(_scan_reports()))
            return
        if path.startswith("/reports/"):
            rel = unquote(path[len("/reports/"):])
            fp = os.path.realpath(os.path.join(REPORTS_DIR, rel))
            if fp.startswith(REPORTS_REAL + os.sep) and os.path.isfile(fp):
                with open(fp, "rb") as f:
                    self._send_bytes(f.read(), "text/html; charset=utf-8")
                return
        self._send_html("<h1>404</h1><p>页面不存在。</p>", status=404)

    def _send_html(self, body, status=200):
        self._send_bytes(body.encode("utf-8"), "text/html; charset=utf-8", status)

    def _send_bytes(self, body, ctype, status=200):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    p = argparse.ArgumentParser(description="全球智库AI赛事预测日报 · 本地网页")
    p.add_argument("--port", type=int, default=8000, help="端口（默认 8000）")
    args = p.parse_args()
    url = f"http://localhost:{args.port}"
    print(f"《全球智库AI赛事预测日报》本地网页已启动：{url}")
    print("浏览器应已自动打开。按 Ctrl+C 停止服务。")
    webbrowser.open(url)
    try:
        HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
