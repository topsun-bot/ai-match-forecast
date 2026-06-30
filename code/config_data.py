"""
数据源档位配置 —— 左侧"数据源"可选三档。
- free：Football-Data.org 免费版（赛程/战绩/积分，无球员详数据/赔率）—— 默认
- paid：API-Football 付费档（~$15/月，含赔率/球员数据/伤病）—— 可选开关
- custom：用户自定义数据源（在 .env 填 CUSTOM_DATA_URL，自行接入）
"""

DATA_TIERS = {
    "free": {
        "label": "Football-Data 免费档",
        "note": "12 大赛事 · 赛程/战绩/积分 · 无球员详数据与赔率",
        "api_key_env": "FOOTBALL_DATA_API_KEY",
    },
    "paid": {
        "label": "API-Football 付费档",
        "note": "1200+ 赛事 · 含赔率/球员数据/伤病 · ~$15/月（可选）",
        "api_key_env": "API_FOOTBALL_KEY",
    },
    "custom": {
        "label": "自定义数据源",
        "note": "用户在 .env 填 CUSTOM_DATA_URL，自行接入",
        "api_key_env": "CUSTOM_DATA_URL",
    },
}

DEFAULT_TIER = "free"
