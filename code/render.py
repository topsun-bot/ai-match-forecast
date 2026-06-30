"""【输出层】把 analyst 的结构化结果渲染成投资人版 HTML 日报。

支持两种数据路径，自动容错：
- grounding 路径（Gemini Google Search）：有推理链 chain + 球评，无结构化表格
- mock / API-Football 路径：有完整数据表格 + 三栏逻辑 + 球评徽章
"""
import os
import html as _html
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "report_template.html")


def _esc(s):
    return _html.escape(str(s)) if s is not None else ""


def render_report(date_str, issue, model_label, data_tier_label, n_matches, results, citations=None):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()
    matches_html = "\n".join(_render_match(r) for r in results)
    pipeline_html = _render_pipeline(data_tier_label, model_label, n_matches)
    citations_html = _render_citations(citations)
    return (
        tpl.replace("{{DATE}}", date_str)
        .replace("{{ISSUE}}", issue)
        .replace("{{MODEL_LABEL}}", model_label)
        .replace("{{PIPELINE}}", pipeline_html)
        .replace("{{CITATIONS}}", citations_html)
        .replace("{{MATCHES}}", matches_html)
        .replace("{{FOOTER_TIME}}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    )


def _render_pipeline(data_tier_label, model_label, n_matches):
    return f"""
  <div class="pipeline">
    <div class="pipe-stage">
      <div class="pipe-num">①</div>
      <div class="pipe-title">数据源</div>
      <div class="pipe-val">{_esc(data_tier_label)}</div>
      <div class="pipe-sub">Gemini Google Search 实时接地</div>
    </div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-stage">
      <div class="pipe-num">②</div>
      <div class="pipe-title">大模型决策</div>
      <div class="pipe-val">{_esc(model_label)}</div>
      <div class="pipe-sub">推理 + 球评综合</div>
    </div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-stage gold">
      <div class="pipe-num">③</div>
      <div class="pipe-title">预测结果</div>
      <div class="pipe-val">{n_matches} 场预测</div>
      <div class="pipe-sub">见下方详细报告</div>
    </div>
  </div>
"""


def _render_citations(citations):
    if not citations:
        return ""
    items = "".join(
        f'<li><a href="{_esc(c["uri"])}" target="_blank" rel="noopener">{_esc(c.get("title") or c["uri"])}</a></li>'
        for c in citations[:12] if c.get("uri")
    )
    if not items:
        return ""
    return (
        '<div class="grounding">'
        '<div class="grounding-title">数据来源 · Gemini Google Search 实时接地</div>'
        f'<ul class="grounding-list">{items}</ul>'
        '</div>'
    )


def _render_match(r):
    m = r["match"]
    a = r["analysis"]
    home, away = m["home"], m["away"]
    pred = a.get("prediction", {})
    reas = a.get("reasoning", {})
    conf_pct = int(pred.get("confidence", 0) * 100)

    has_form = bool(home.get("form")) and bool(away.get("form"))
    home_form = _form_badges(home["form"]) if has_form else ""
    away_form = _form_badges(away["form"]) if has_form else ""

    logic_html = _render_chain(reas["chain"]) if reas.get("chain") else _render_logic_grid(reas)
    data_html = _render_data_table(m)
    pundits = a.get("pundits", [])
    pundits_html = "".join(_render_pundit(p) for p in pundits) if pundits else ""

    meta = " · ".join(p for p in [m.get("competition", ""), m.get("venue", ""),
                                    ("开球 " + m["time"]) if m.get("time") else ""] if p)
    pundits_block = (f'<h3 class="block-title">球评观点</h3><div class="pundits-grid">{pundits_html}</div>'
                     if pundits_html else "")

    return f"""
  <section class="match-card">
    <div class="match-meta">{_esc(meta)}</div>
    <div class="score-row">
      <div class="team home">{_esc(home['name'])}{home_form}</div>
      <div class="score">{pred.get('home', 0)} : {pred.get('away', 0)}</div>
      <div class="team away">{away_form}{_esc(away['name'])}</div>
    </div>
    <div class="confidence">
      <span class="conf-label">AI 置信度</span>
      <div class="bar"><div class="bar-fill" style="width:{conf_pct}%"></div></div>
      <span class="conf-val">{conf_pct}%</span>
      <span class="winner">倾向：{_esc(pred.get('winner', ''))}</span>
    </div>
    <h3 class="block-title">推理过程</h3>
    {logic_html}
    {data_html}
    {pundits_block}
  </section>
"""


def _render_chain(chain):
    items = "".join(f"<li>{_esc(step)}</li>" for step in chain if step)
    return f'<ol class="reasoning-chain">{items}</ol>' if items else ""


def _render_logic_grid(reas):
    boxes = []
    if reas.get("data_insight"):
        boxes.append(f'<div class="logic-box"><h4>数据洞察</h4><p>{_esc(reas["data_insight"])}</p></div>')
    if reas.get("pundit_summary"):
        boxes.append(f'<div class="logic-box"><h4>球评员观点摘要</h4><p>{_esc(reas["pundit_summary"])}</p></div>')
    if reas.get("ai_synthesis"):
        boxes.append(f'<div class="logic-box gold"><h4>AI 综合推算</h4><p>{_esc(reas["ai_synthesis"])}</p></div>')
    return f'<div class="logic-grid">{"".join(boxes)}</div>' if boxes else ""


def _render_data_table(m):
    home, away = m["home"], m["away"]
    rows = []
    if home.get("league_pos") or away.get("league_pos"):
        rows.append(_row("排名",
                         f"第 {home['league_pos']}" if home.get("league_pos") else "—",
                         f"第 {away['league_pos']}" if away.get("league_pos") else "—"))
    if home.get("goals_avg") or away.get("goals_avg"):
        rows.append(_row("场均进球", f"{home['goals_avg']}", f"{away['goals_avg']}"))
    h2h = m.get("h2h") or {}
    if h2h:
        rows.append(_row("近况交锋", f"主胜 {h2h.get('home_win', 0)}",
                         f"客胜 {h2h.get('away_win', 0)}（平 {h2h.get('draw', 0)}，场均 {h2h.get('avg_goals', 0)} 球）"))
    inj = m.get("injuries") or {}
    if inj.get("home") or inj.get("away"):
        rows.append(_row("伤停", _fmt_inj(inj.get("home", [])), _fmt_inj(inj.get("away", []))))
    odds = m.get("odds") or {}
    if odds.get("home_win") or odds.get("away_win"):
        rows.append(_row("赔率参考", str(odds.get("home_win")), str(odds.get("away_win"))))
    if not rows:
        return ""
    return f'<div class="data-table">{"".join(rows)}</div>'


def _form_badges(form):
    color = {"胜": "w", "平": "d", "负": "l"}
    cells = "".join(f'<i class="f-{color.get(x, "d")}">{_esc(x)}</i>' for x in form)
    return f'<span class="form">{cells}</span>'


def _row(label, home_val, away_val):
    return (
        f'<div class="drow"><span class="dl">{_esc(label)}</span>'
        f'<span class="dv home">{_esc(home_val)}</span>'
        f'<span class="dv away">{_esc(away_val)}</span></div>'
    )


def _fmt_inj(items):
    if not items:
        return "无"
    return "；".join(f"{x['player']}（{x['status']}）" for x in items)


def _render_pundit(p):
    lean_label = {"home": "挺主队", "away": "挺客队", "draw": "看平局"}.get(p.get("lean", ""), "")
    lean_html = f'<span class="pundit-lean">{lean_label}</span>' if lean_label else ""
    outlet_html = f'<div class="pundit-outlet">{_esc(p.get("outlet", ""))}</div>' if p.get("outlet") else ""
    return f"""
      <div class="pundit-card">
        <div class="pundit-head"><span class="pundit-name">{_esc(p.get('name', ''))}</span>{lean_html}</div>
        {outlet_html}
        <p class="pundit-take">{_esc(p.get('take', ''))}</p>
      </div>"""
