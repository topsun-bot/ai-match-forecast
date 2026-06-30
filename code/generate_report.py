#!/usr/bin/env python3
"""
《全球智库AI赛事预测日报》CLI 入口。
小白快速跑通（零依赖、零 key）：
    cd subprojects/ai_match_predictor
    python3 generate_report.py
浏览器会自动打开《样刊》。看完确认风格后，下一步接真实数据与 GLM-5.2。
"""
import os
import sys
import argparse
import datetime
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from config_models import MODELS, DEFAULT_MODEL
from data_provider import get_matches
from llm_router import LLMRouter
import analyst
import render


def _load_env(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    p = argparse.ArgumentParser(description="全球智库AI赛事预测日报")
    p.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODELS.keys()), help="决策模型")
    p.add_argument("--data-tier", dest="data_tier", default="free", choices=["free", "paid", "custom"], help="数据源档位：free 免费档（默认）/ paid 付费档（可选）/ custom 自定义")
    p.add_argument("--date", default="today", help="日期 YYYY-MM-DD，或 today")
    p.add_argument("--match", default=None, help="只生成指定 id 的比赛，例如 mock-001")
    p.add_argument("--mock-data", dest="mock_data", action="store_true", default=True, help="比赛数据用样例（默认开）")
    p.add_argument("--no-mock-data", dest="mock_data", action="store_false", help="比赛数据走真实 Football-Data（下一阶段实现）")
    p.add_argument("--mock-llm", dest="mock_llm", action="store_true", default=False, help="强制 LLM 走 mock（默认有 key 就真实）")
    p.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    p.add_argument("--pdf", action="store_true", help="生成 HTML 后自动导出 PDF（用 Chrome 无头打印）")
    p.add_argument("--out", default=os.path.join(HERE, "reports"), help="输出目录")
    args = p.parse_args()

    _load_env(os.path.join(HERE, ".env"))

    date_str = datetime.date.today().isoformat() if args.date == "today" else args.date

    matches = get_matches(date_str, tier=args.data_tier, mock=args.mock_data, match_id=args.match)
    if not matches:
        print(f"未找到比赛（date={date_str}, tier={args.data_tier}, mock_data={args.mock_data}）")
        return

    router = LLMRouter(args.model, mock=args.mock_llm)
    print(f"模型：{router.label}（{'mock' if router.mock else '真实'}模式）｜数据档：{args.data_tier}")
    print(f"比赛 {len(matches)} 场，分析中…")

    results = []
    for m in matches:
        print(f"  · {m['home']['name']} vs {m['away']['name']}")
        results.append({"match": m, "analysis": analyst.analyze(m, router)})

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, f"日报-{date_str}.html")
    issue = f"第 {date_str.replace('-', '')} 期"
    from config_data import DATA_TIERS
    data_tier_label = DATA_TIERS.get(args.data_tier, {}).get("label", args.data_tier)
    html = render.render_report(date_str, issue, router.label, data_tier_label, len(results), results)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✓ 报告已生成：{out_path}")

    if args.pdf:
        try:
            from export_pdf import html_to_pdf
            pdf_path = html_to_pdf(out_path)
            print(f"✓ PDF 已生成：{pdf_path}")
        except Exception as e:
            print(f"⚠ PDF 导出失败：{e}")
            print("  可手动：浏览器打开 HTML → Cmd+P → 存为 PDF。")

    if not args.no_open:
        webbrowser.open(f"file://{out_path}")


if __name__ == "__main__":
    main()
