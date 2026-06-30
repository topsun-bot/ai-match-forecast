"""
【信息输入层】比赛数据采集。
- mock=True：返回内置样例数据，无需任何 API key，供样刊跑通
- mock=False：调用 Football-Data.org 免费版（需在 .env 设置 FOOTBALL_DATA_API_KEY）
  免费版覆盖 12 大赛事，含赛程/比分/积分；不含球员详细统计与赔率（付费档才有）
"""
import os
import json
import time
import datetime
import urllib.request
import urllib.error

FOOTBALL_DATA_ENDPOINT = "https://api.football-data.org/v4"
API_FOOTBALL_ENDPOINT = "https://v3.football.api-sports.io"
_API_FOOTBALL_LAST_CALL = 0.0  # 简易限速状态：请求间隔 ≥6.5 秒，规避免费档 10 req/min

MOCK_MATCHES = [
    {
        "id": "mock-001",
        "competition": "欧洲冠军联赛 · 决赛",
        "date": "2026-06-29",
        "time": "03:00",
        "venue": "温布利球场，伦敦",
        "home": {
            "name": "皇家马德里", "short": "RMA",
            "form": ["胜", "胜", "平", "胜", "胜"],
            "league_pos": 1,
            "goals_avg": 2.4,
        },
        "away": {
            "name": "曼城", "short": "MCI",
            "form": ["胜", "胜", "胜", "平", "胜"],
            "league_pos": 2,
            "goals_avg": 2.6,
        },
        "h2h": {"home_win": 2, "draw": 1, "away_win": 2, "avg_goals": 3.2},
        "injuries": {
            "home": [{"player": "贝林厄姆", "reason": "腿筋伤", "status": "出战成疑"}],
            "away": [{"player": "德布劳内", "reason": "腹股沟不适", "status": "大概率出场"}],
        },
        "odds": {"home_win": 2.35, "draw": 3.40, "away_win": 2.80},
    },
    {
        "id": "mock-002",
        "competition": "欧洲冠军联赛 · 半决赛",
        "date": "2026-06-29",
        "time": "03:00",
        "venue": "安联球场，慕尼黑",
        "home": {
            "name": "拜仁慕尼黑", "short": "BAY",
            "form": ["胜", "平", "胜", "胜", "负"],
            "league_pos": 1,
            "goals_avg": 2.7,
        },
        "away": {
            "name": "阿森纳", "short": "ARS",
            "form": ["胜", "胜", "平", "胜", "胜"],
            "league_pos": 2,
            "goals_avg": 2.1,
        },
        "h2h": {"home_win": 3, "draw": 1, "away_win": 1, "avg_goals": 2.8},
        "injuries": {
            "home": [{"player": "穆西亚拉", "reason": "膝盖疲劳", "status": "健康"}],
            "away": [{"player": "萨卡", "reason": "脚踝伤", "status": "出战成疑"}],
        },
        "odds": {"home_win": 2.10, "draw": 3.50, "away_win": 3.20},
    },
]


def get_matches(date_str=None, tier="free", mock=True, match_id=None):
    """获取当日比赛列表。tier 选数据源档位（free/paid/custom），match_id 指定时只返回该场。"""
    if mock:
        matches = list(MOCK_MATCHES)  # mock 不区分档位，统一用样例数据
    elif tier == "free":
        matches = _fetch_football_data_matches(date_str)
    elif tier == "paid":
        matches = _fetch_api_football_matches(date_str)
    elif tier == "custom":
        matches = _fetch_custom_matches(date_str)
    else:
        raise ValueError(f"未知数据档位：{tier}，可选 free/paid/custom")
    if match_id:
        matches = [m for m in matches if m["id"] == match_id]
    return matches


def _fetch_football_data_matches(date_str):
    """真实 Football-Data.org 接入 —— 下一阶段实现。"""
    key = os.getenv("FOOTBALL_DATA_API_KEY", "")
    if not key:
        raise RuntimeError(
            "未设置 FOOTBALL_DATA_API_KEY。请到 https://www.football-data.org/client/register "
            "免费注册，把 key 填入 .env 后，加 --no-mock 运行。"
        )
    raise NotImplementedError("真实 Football-Data 接入在下一阶段实现，本步请用 --mock 跑通样刊。")


def _fetch_api_football_matches(date_str):
    """付费档 API-Football v3（官方端点，免费档亦可调，配额 100 req/天、10 req/min）。
    覆盖 1200+ 赛事，含赔率/球员/伤停/积分。数据流：/fixtures?date= 拿当日比赛 →
    逐场补 standings（含近况 form/排名/场均进球）、h2h、injuries、odds。
    standigs 按 league 缓存省请求；子请求失败降级为占位，不阻断整场。
    """
    key = os.getenv("API_FOOTBALL_KEY", "")
    if not key:
        raise RuntimeError(
            "paid 档需 API_FOOTBALL_KEY。到 https://www.api-football.com/ 注册（免费档即给 key），"
            "填入 .env 后用 --data-tier paid 运行。"
        )
    date_str = date_str or datetime.date.today().isoformat()
    fx = _api_football_get("/fixtures", {"date": date_str}, key)
    matches, standings_cache = [], {}
    for item in fx.get("response", []):
        fixture = item.get("fixture", {}) or {}
        league = item.get("league", {}) or {}
        teams = item.get("teams", {}) or {}
        home_t, away_t = teams.get("home", {}) or {}, teams.get("away", {}) or {}
        league_id, season = league.get("id"), league.get("season")
        home_id, away_id = home_t.get("id"), away_t.get("id")

        table = standings_cache.get(league_id)
        if table is None and league_id and season:
            table = _fetch_standings_map(league_id, season, key)
            standings_cache[league_id] = table or {}
        home_row = (table or {}).get(home_id, {})
        away_row = (table or {}).get(away_id, {})

        h2h = _try(lambda: _fetch_h2h(home_id, away_id, key),
                   {"home_win": 0, "draw": 0, "away_win": 0, "avg_goals": 0.0})
        injuries = _try(lambda: _fetch_injuries(fixture.get("id"), home_id, away_id, key),
                        {"home": [], "away": []})
        odds = _try(lambda: _fetch_odds(fixture.get("id"), key), None)

        home_name, away_name = home_t.get("name", "?"), away_t.get("name", "?")
        matches.append({
            "id": f"apif-{fixture.get('id')}",
            "competition": _join_nonempty(" · ", league.get("name"), league.get("round")),
            "date": (fixture.get("date") or date_str)[:10],
            "time": (fixture.get("date") or "")[11:16],
            "venue": _venue(fixture),
            "home": {
                "name": home_name, "short": _short(home_name),
                "form": _parse_form(home_row.get("form", "")),
                "league_pos": home_row.get("rank", 0),
                "goals_avg": _goals_avg(home_row),
            },
            "away": {
                "name": away_name, "short": _short(away_name),
                "form": _parse_form(away_row.get("form", "")),
                "league_pos": away_row.get("rank", 0),
                "goals_avg": _goals_avg(away_row),
            },
            "h2h": h2h, "injuries": injuries,
            "odds": odds or {"home_win": None, "draw": None, "away_win": None},
        })
    if not matches:
        raise RuntimeError(f"API-Football 在 {date_str} 未返回任何比赛（休赛日、配额耗尽或网络问题）。")
    return matches


# ---- API-Football 辅助函数 ----

_API_FOOTBALL_MIN_INTERVAL = 6.5  # 免费档 10 req/min → 请求间隔 ≥6 秒；上 Pro 档可调小


def _api_football_get(path, params, key):
    """发起一次 API-Football GET，带限速与错误归一化。失败抛异常（由 _try 捕获降级）。"""
    global _API_FOOTBALL_LAST_CALL
    wait = _API_FOOTBALL_MIN_INTERVAL - (time.time() - _API_FOOTBALL_LAST_CALL)
    if wait > 0:
        time.sleep(wait)
    qs = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    url = f"{API_FOOTBALL_ENDPOINT}{path}?{qs}"
    req = urllib.request.Request(url, headers={"x-apisports-key": key}, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    _API_FOOTBALL_LAST_CALL = time.time()
    if data.get("errors"):
        raise RuntimeError(f"API-Football 错误：{data['errors']}")
    return data


def _try(fn, fallback):
    try:
        return fn()
    except Exception:
        return fallback


def _fetch_standings_map(league_id, season, key):
    data = _api_football_get("/standings", {"league": league_id, "season": season}, key)
    out = {}
    for entry in data.get("response", []):
        for group in (entry.get("league", {}) or {}).get("standings", []):
            for row in group:
                tid = (row.get("team") or {}).get("id")
                if tid:
                    out[tid] = row
    return out


def _fetch_h2h(home_id, away_id, key):
    data = _api_football_get("/fixtures/headtohead", {"h2h": f"{home_id}-{away_id}", "last": 5}, key)
    hw = d = aw = goals = 0
    for item in data.get("response", []):
        g = item.get("goals", {}) or {}
        hg, ag = g.get("home"), g.get("away")
        if hg is None or ag is None:
            continue
        goals += hg + ag
        if hg > ag:
            hw += 1
        elif hg < ag:
            aw += 1
        else:
            d += 1
    n = hw + d + aw
    return {"home_win": hw, "draw": d, "away_win": aw,
            "avg_goals": round(goals / n, 1) if n else 0.0}


def _fetch_injuries(fixture_id, home_id, away_id, key):
    data = _api_football_get("/injuries", {"fixture": fixture_id}, key)
    home, away = [], []
    for item in data.get("response", []):
        tid = (item.get("team") or {}).get("id")
        rec = {
            "player": (item.get("player") or {}).get("name", "?"),
            "reason": item.get("reason") or "未知",
            "status": _injury_status(item.get("type")),
        }
        if tid == home_id:
            home.append(rec)
        elif tid == away_id:
            away.append(rec)
    return {"home": home, "away": away}


def _fetch_odds(fixture_id, key):
    data = _api_football_get("/odds", {"fixture": fixture_id}, key)
    resp = data.get("response") or []
    if not resp:
        return None
    win = next((b for b in (resp[0].get("bets") or [])
                if (b.get("name") or "").lower() == "match winner"), None)
    if not win:
        return None
    vals = {v.get("value"): v.get("odd") for v in (win.get("values") or [])}
    return {
        "home_win": _to_float(vals.get("Home")),
        "draw": _to_float(vals.get("Draw")),
        "away_win": _to_float(vals.get("Away")),
    }


def _injury_status(t):
    t = (t or "").lower()
    if "missing" in t or "out" in t:
        return "缺阵"
    if "doubt" in t:
        return "出战成疑"
    return "未知"


def _to_float(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _parse_form(s):
    return [{"W": "胜", "D": "平", "L": "负"}.get(c.upper(), "平") for c in (s or "")][:5]


def _goals_avg(row):
    g = row.get("goals") or {}
    played = row.get("played", 0) or 0
    try:
        return round(g.get("for", 0) / played, 1) if played else 0.0
    except (TypeError, ZeroDivisionError):
        return 0.0


def _venue(fixture):
    v = fixture.get("venue") or {}
    return _join_nonempty("，", v.get("name"), v.get("city"))


def _short(name):
    return (name[:3] or "?").upper()


def _join_nonempty(sep, *parts):
    return sep.join(p for p in parts if p)


def _fetch_custom_matches(date_str):
    """自定义数据源 —— 用户在 .env 填 CUSTOM_DATA_URL，自行接入。"""
    url = os.getenv("CUSTOM_DATA_URL", "")
    if not url:
        raise RuntimeError(
            "自定义档需在 .env 设置 CUSTOM_DATA_URL（指向你自己的比赛数据 JSON 接口）。"
        )
    raise NotImplementedError("自定义数据源接入在下一阶段实现。")
