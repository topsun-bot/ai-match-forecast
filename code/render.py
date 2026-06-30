"""【输出层】把 analyst 的结构化结果渲染成高逼格 HTML 日报。"""
import os
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "report_template.html")


def render_report(date_str, issue, model_label, data_tier_label, n_matches, results):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()
    matches_html = "\n".join(_render_match(r) for r in results)
    pipeline_html = _render_pipeline(data_tier_label, model_label, n_matches)
    return (
        tpl.replace("{{DATE}}", date_str)
        .replace("{{ISSUE}}", issue)
        .replace("{{MODEL_LABEL}}", model_label)
        .replace("{{PIPELINE}}", pipeline_html)
        .replace("{{MATCHES}}", matches_html)
        .replace("{{FOOTER_TIME}}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    )


def _render_pipeline(data_tier_label, model_label, n_matches):
    return f"""
  <div class="pipeline">
    <div class="pipe-stage">
      <div class="pipe-num">①</div>
      <div class="pipe-title">数据源</div>
      <div class="pipe-val">{data_tier_label}</div>
      <div class="pipe-sub">可切换：免费 / 付费 / 自定义</div>
    </div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-stage">
      <div class="pipe-num">②</div>
      <div class="pipe-title">大模型决策</div>
      <div class="pipe-val">{model_label}</div>
      <div class="pipe-sub">多模型可切换</div>
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


def _render_match(r):
    m = r["match"]
    a = r["analysis"]
    home, away = m["home"], m["away"]
    pred = a["prediction"]
    reas = a["reasoning"]
    conf_pct = int(pred.get("confidence", 0) * 100)
    return f"""
  <section class="match-card">
    <div class="match-meta">{m['competition']} · {m.get('venue', '')} · 开球 {m.get('time', '')}</div>
    <div class="score-row">
      <div class="team home">{home['name']}<br>{_form_badges(home['form'])}</div>
      <div class="score">{pred['home']} : {pred['away']}</div>
      <div class="team away"><br>{_form_badges(away['form'])}{away['name']}</div>
    </div>
    <div class="confidence">
      <span class="conf-label">AI 置信度</span>
      <div class="bar"><div class="bar-fill" style="width:{conf_pct}%"></div></div>
      <span class="conf-val">{conf_pct}%</span>
      <span class="winner">倾向：{pred['winner']}</span>
    </div>
    <div class="logic-grid">
      <div class="logic-box"><h4>数据洞察</h4><p>{reas['data_insight']}</p></div>
      <div class="logic-box"><h4>球评员观点摘要</h4><p>{reas['pundit_summary']}</p></div>
      <div class="logic-box gold"><h4>AI 综合推算</h4><p>{reas['ai_synthesis']}</p></div>
    </div>
    <div class="data-table">
      {_row('场均进球', f"{home['goals_avg']}", f"{away['goals_avg']}")}
      {_row('联赛排名', f"第 {home['league_pos']}", f"第 {away['league_pos']}")}
      {_row('近5次交锋', f"主胜 {m['h2h']['home_win']}", f"客胜 {m['h2h']['away_win']}（平 {m['h2h']['draw']}，场均 {m['h2h']['avg_goals']} 球）")}
      {_row('伤停', _fmt_inj(m['injuries']['home']), _fmt_inj(m['injuries']['away']))}
      {_row('赔率参考（占位）', str(m['odds']['home_win']), str(m['odds']['away_win']))}
    </div>
    <h4 class="pundits-title">海外 Top 球评员观点（AI 模拟）</h4>
    <div class="pundits-grid">
      {"".join(_render_pundit(p) for p in a['pundits'])}
    </div>
  </section>
"""


def _form_badges(form):
    color = {"胜": "w", "平": "d", "负": "l"}
    cells = "".join(f'<i class="f-{color.get(x, "d")}">{x}</i>' for x in form)
    return f'<span class="form">{cells}</span>'


def _row(label, home_val, away_val):
    return (
        f'<div class="drow"><span class="dl">{label}</span>'
        f'<span class="dv home">{home_val}</span>'
        f'<span class="dv away">{away_val}</span></div>'
    )


def _fmt_inj(items):
    if not items:
        return "无"
    return "；".join(f"{x['player']}（{x['status']}）" for x in items)


def _render_pundit(p):
    lean_label = {"home": "挺主队", "away": "挺客队", "draw": "看平局"}.get(p.get("lean", "draw"), "")
    return f"""
      <div class="pundit-card">
        <div class="pundit-head"><span class="pundit-name">{p['name']}</span><span class="pundit-lean">{lean_label}</span></div>
        <div class="pundit-outlet">{p['outlet']}</div>
        <p class="pundit-take">{p['take']}</p>
      </div>"""
