"""
【决策执行层】球评模拟 + 综合推算。
两阶段（单次模型调用，省 token）：
  ① 基于 match 数据生成 3 位模拟 Top 球评员视角点评
  ② 综合数据 + 球评观点 → 预测比分 + 置信度 + 核心逻辑
mock 模式下不调用模型，直接生成结构化样刊数据。
"""
import json
import re
from llm_router import LLMRouter


PUNDIT_STYLE = [
    {"name": "Guillem Balagué", "outlet": "BBC Sport", "angle": "西班牙足球视角，看中场控制与节奏"},
    {"name": "Jonathan Wilson", "outlet": "The Guardian", "angle": "战术结构派，看阵型与空间博弈"},
    {"name": "Gabriele Marcotti", "outlet": "ESPN", "angle": "全局视角，看体能、轮换与心理势能"},
]


def analyze(match, router: LLMRouter):
    """输入一场 match，返回结构化分析结果。"""
    if router.mock:
        return _mock_analyze(match)
    return _llm_analyze(match, router)


def _llm_analyze(match, router):
    sys_prompt = (
        "你是《全球智库AI赛事预测日报》的首席分析师。基于给定比赛数据，"
        "先模拟三位全球顶级足球评论员的核心观点，再综合所有信息推算最终预测比分。"
        "严格只输出一个 JSON 对象，不要任何额外文字。"
    )
    user_prompt = _build_user_prompt(match)
    raw = router.chat([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt + "\n\nPREDICT：请按下列 JSON Schema 输出：\n" + json.dumps(_schema(), ensure_ascii=False)},
    ], temperature=0.6, max_tokens=8000, json_mode=True)
    return _safe_json(raw, fallback=lambda: _mock_analyze(match))


def _build_user_prompt(match):
    home, away = match["home"], match["away"]
    return (
        f"赛事：{match['competition']}\n"
        f"{home['name']} vs {away['name']}\n"
        f"场地/时间：{match.get('venue','')} · {match.get('date','')} {match.get('time','')}\n\n"
        f"【主队 {home['name']}】近5场：{''.join(home['form'])}｜联赛第{home['league_pos']}｜场均进球{home['goals_avg']}\n"
        f"【客队 {away['name']}】近5场：{''.join(away['form'])}｜联赛第{away['league_pos']}｜场均进球{away['goals_avg']}\n"
        f"【近5次交锋】主胜{match['h2h']['home_win']} 平{match['h2h']['draw']} 客胜{match['h2h']['away_win']}｜场均{match['h2h']['avg_goals']}球\n"
        f"【伤停】主队：{_fmt_injuries(match['injuries']['home'])}｜客队：{_fmt_injuries(match['injuries']['away'])}\n"
        f"【赔率参考（免费档占位）】主胜{match['odds']['home_win']} 平{match['odds']['draw']} 客胜{match['odds']['away_win']}\n"
    )


def _fmt_injuries(items):
    if not items:
        return "无"
    return "；".join(f"{x['player']}（{x['status']}）" for x in items)


def _schema():
    return {
        "pundits": [
            {"name": "评论员名", "outlet": "媒体", "lean": "home|away|draw", "take": "一句话核心观点"}
        ],
        "prediction": {"home": 0, "away": 0, "confidence": 0.0, "winner": "队名或平局"},
        "reasoning": {
            "data_insight": "基于数据的洞察（近况/交锋/伤停）",
            "pundit_summary": "三位球评员观点的共性摘要",
            "ai_synthesis": "AI 综合推算逻辑",
        },
    }


def _safe_json(raw, fallback):
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return fallback()
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return fallback()


def _mock_analyze(match):
    """基于 match 数据生成合理的样刊结构化结果。"""
    home, away = match["home"], match["away"]
    h_goal, a_goal = match["h2h"]["home_win"], match["h2h"]["away_win"]
    home_inj = bool(match["injuries"]["home"] and match["injuries"]["home"][0]["status"] == "出战成疑")
    away_inj = bool(match["injuries"]["away"] and match["injuries"]["away"][0]["status"] == "出战成疑")

    home_strength = home["goals_avg"] + (0.3 if not home_inj else 0) + (home["form"].count("胜") * 0.1)
    away_strength = away["goals_avg"] + (0.3 if not away_inj else 0) + (away["form"].count("胜") * 0.1)
    diff = home_strength - away_strength

    if diff > 0.3:
        ph, pa, winner = 2, 1, home["name"]
    elif diff < -0.3:
        ph, pa, winner = 1, 2, away["name"]
    else:
        ph, pa, winner = 1, 1, "平局"
    confidence = round(min(0.75, 0.5 + abs(diff) * 0.15), 2)

    pundits = []
    for p in PUNDIT_STYLE:
        lean = "home" if diff > 0.1 else ("away" if diff < -0.1 else "draw")
        take = _mock_pundit_take(p, home, away, home_inj, away_inj, lean)
        pundits.append({"name": p["name"], "outlet": p["outlet"], "lean": lean, "take": take})

    return {
        "pundits": pundits,
        "prediction": {"home": ph, "away": pa, "confidence": confidence, "winner": winner},
        "reasoning": {
            "data_insight": _mock_data_insight(home, away, match["h2h"], home_inj, away_inj),
            "pundit_summary": _mock_pundit_summary(pundits, winner),
            "ai_synthesis": _mock_synthesis(home, away, ph, pa, winner, confidence),
        },
    }


def _mock_pundit_take(p, home, away, home_inj, away_inj, lean):
    base = f"{home['name']} vs {away['name']}："
    if "Balagué" in p["name"]:
        if home_inj:
            return base + f"{home['name']}若失去中场核心，节奏将被削弱，{away['name']}的控球优势会放大。"
        return base + f"中场是胜负手，{home['name'] if lean=='home' else away['name']}的传导深度足以撕裂对手防线。"
    if "Wilson" in p["name"]:
        return base + "阵型压缩与转换速度决定比赛，谁能在大禁区前沿制造人数优势，谁就掌握主动。"
    return base + f"体能与轮换深度被低估，{home['name'] if lean=='home' else away['name']}近期的心理势能更稳。"


def _mock_data_insight(home, away, h2h, home_inj, away_inj):
    parts = [
        f"双方近5次交锋场均{h2h['avg_goals']}球，进攻效率高",
        f"{home['name']}场均{home['goals_avg']}球、近5场{home['form'].count('胜')}胜",
        f"{away['name']}场均{away['goals_avg']}球、近5场{away['form'].count('胜')}胜",
    ]
    if home_inj:
        parts.append(f"{home['name']}核心球员出战成疑，火力折损")
    if away_inj:
        parts.append(f"{away['name']}核心球员带伤，稳定性下降")
    return "；".join(parts) + "。"


def _mock_pundit_summary(pundits, winner):
    leans = [p["lean"] for p in pundits]
    h = leans.count("home")
    a = leans.count("away")
    if h > a:
        return f"三位专家中 {h} 位倾向主队，认为主场惯性 + 阵容完整度是关键。"
    if a > h:
        return f"三位专家中 {a} 位倾向客队，认为客队近期状态与战术纪律更胜一筹。"
    return "三位专家观点分歧，普遍认为这将是一场势均力敌的低比分博弈。"


def _mock_synthesis(home, away, ph, pa, winner, conf):
    pct = int(conf * 100)
    return (
        f"综合交锋历史、近况、伤停与专家观点，AI 推算 {home['name']} {ph}-{pa} {away['name']}，"
        f"赛果倾向「{winner}」，置信度 {pct}%。该置信度仅反映数据一致性强度，不构成投注建议。"
    )
