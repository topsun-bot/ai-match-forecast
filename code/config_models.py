"""
多模型配置 —— 决策台引擎支持运行时切换。
调用方式：python3 generate_report.py --model glm-5.2
真实接入前，请到对应平台确认 model id 是否更新。
"""

MODELS = {
    "glm-5.2": {
        "provider": "zhipu",
        "endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-5.2",
        "api_key_env": "ZHIPU_API_KEY",
        "label": "智谱 GLM-5.2",
        "note": "2026-06-13 发布，1M 上下文，OpenAI 兼容接口",
    },
    "gpt-4o": {
        "provider": "openai",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY",
        "label": "OpenAI GPT-4o",
        "note": "海外模型，投资人更熟悉",
    },
    "gemini-2.5-pro": {
        "provider": "gemini",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent",
        "model": "gemini-2.5-pro",
        "api_key_env": "GEMINI_API_KEY",
        "label": "Google Gemini 2.5 Pro",
        "note": "海外模型，长上下文强",
    },
}

DEFAULT_MODEL = "glm-5.2"
