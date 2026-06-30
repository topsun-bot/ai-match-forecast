#!/usr/bin/env python3
"""同步代码到 GitHub Pages 部署目录的 code/ 子目录。
【本地操作，不 push、不联网】—— 安全可逆。配合 publish_to_github.sh 推送。

白名单复制：只推 .py/.sh/.html/.command/.txt/.md + .env.example + .gitignore
排除：.env（含 Gemini key）、__pycache__/、reports/（HTML 已在根目录，PDF 不推）

用法：python3 sync_code.py [--site-dir PATH]
默认部署目录：~/Documents/ai-match-forecast-site/code/
"""
import os
import shutil
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SITE_DIR = os.path.expanduser("~/Documents/ai-match-forecast-site")

INCLUDE_EXT = {".py", ".sh", ".html", ".command", ".txt", ".md", ".yml", ".yaml"}
EXCLUDE_NAMES = {".env", "__pycache__", "reports", ".DS_Store"}
EXTRA_FILES = {".env.example", ".gitignore"}
WORKFLOW_EXT = {".yml", ".yaml"}


def _should_include(fn):
    if fn in EXCLUDE_NAMES and fn not in EXTRA_FILES:
        return False
    if fn in EXTRA_FILES:
        return True
    return os.path.splitext(fn)[1] in INCLUDE_EXT


def _sync_workflows(code_dir):
    """递归同步 .github/ 子树到 code/.github/（让 GitHub Actions workflow 随发布推到仓库）。
    只同步 .yml/.yaml，保持白名单安全。
    """
    gh = os.path.join(HERE, ".github")
    if not os.path.isdir(gh):
        return 0
    n = 0
    for root, dirs, files in os.walk(gh):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_NAMES]
        rel = os.path.relpath(root, HERE)
        dst_root = os.path.join(code_dir, rel)
        os.makedirs(dst_root, exist_ok=True)
        for fn in files:
            if os.path.splitext(fn)[1] not in WORKFLOW_EXT:
                continue
            shutil.copy2(os.path.join(root, fn), os.path.join(dst_root, fn))
            print(f"  ✓ {os.path.join(rel, fn)}")
            n += 1
    return n


def main():
    p = argparse.ArgumentParser(description="同步代码到部署目录 code/ 子目录（本地，不 push）")
    p.add_argument("--site-dir", default=DEFAULT_SITE_DIR)
    args = p.parse_args()
    code_dir = os.path.join(args.site_dir, "code")
    os.makedirs(code_dir, exist_ok=True)
    copied = 0
    for fn in sorted(os.listdir(HERE)):
        src = os.path.join(HERE, fn)
        if not os.path.isfile(src) or not _should_include(fn):
            continue
        shutil.copy2(src, os.path.join(code_dir, fn))
        copied += 1
        print(f"  ✓ {fn}")
    copied += _sync_workflows(code_dir)
    print(f"\n✓ 已同步 {copied} 个文件到：{code_dir}")
    print(f"  排除：.env（含 key）、__pycache__/、reports/（HTML 已在根，PDF 不推）")


if __name__ == "__main__":
    main()
