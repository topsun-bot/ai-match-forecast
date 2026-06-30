#!/usr/bin/env python3
"""HTML → PDF，用 Chrome/Edge/Brave 无头模式打印。零 Python 依赖。
用法：
    python3 export_pdf.py <报告.html> [输出.pdf]
找不到浏览器时给出手动降级提示（浏览器打开 HTML → Cmd+P → 存为 PDF）。
"""
import os
import sys
import subprocess

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def html_to_pdf(html_path, pdf_path=None):
    """把 HTML 转成 PDF。成功返回 PDF 绝对路径，失败抛 RuntimeError。"""
    chrome = find_chrome()
    if not chrome:
        raise RuntimeError(
            "未找到 Chrome/Edge/Brave。请装 Google Chrome，或手动：浏览器打开 HTML → Cmd+P → 存为 PDF。"
        )
    html_abs = os.path.abspath(html_path)
    if not os.path.exists(html_abs):
        raise RuntimeError(f"HTML 文件不存在：{html_abs}")
    pdf_abs = os.path.abspath(pdf_path or html_abs.rsplit(".", 1)[0] + ".pdf")

    # 先试 --headless=new（Chrome 112+），失败降级旧 --headless
    common = ["--disable-gpu", "--no-pdf-header-footer",
              f"--print-to-pdf={pdf_abs}", f"file://{html_abs}"]
    last_err = ""
    for flag in ("--headless=new", "--headless"):
        if os.path.exists(pdf_abs):
            os.remove(pdf_abs)
        try:
            r = subprocess.run([chrome, flag] + common, capture_output=True,
                               text=True, timeout=60)
            if os.path.exists(pdf_abs) and os.path.getsize(pdf_abs) > 0:
                return pdf_abs
            last_err = (r.stderr or r.stdout or "无输出")[:200]
        except Exception as e:
            last_err = str(e)[:200]
    raise RuntimeError(f"Chrome 转 PDF 失败：{last_err}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 export_pdf.py <报告.html> [输出.pdf]")
        sys.exit(1)
    try:
        out = html_to_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
        print(f"✓ PDF 已生成：{out}")
    except Exception as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)
