"""
【决策台引擎】多模型抽象层。
统一 chat(messages) 接口，适配智谱 GLM-5.2 / OpenAI GPT-4o / Google Gemini。
- 无 key 或 --mock 时自动走 mock 模式（返回占位文本，供样刊跑通，零依赖）
- 有 key 时走真实 HTTP 调用（仅用标准库 urllib，无需装 SDK）
"""
import os
import json
import urllib.request
import urllib.error

from config_models import MODELS, DEFAULT_MODEL


class LLMRouter:
    def __init__(self, model_name=None, mock=False):
        key = model_name or DEFAULT_MODEL
        if key not in MODELS:
            raise ValueError(f"未知模型：{key}，可选：{list(MODELS.keys())}")
        self.model_key = key
        self.cfg = MODELS[key]
        self.api_key = os.getenv(self.cfg["api_key_env"], "")
        self.mock = mock or os.getenv("LLM_MOCK") == "1"
        if not self.mock and not self.api_key:
            self.mock = True

    @property
    def label(self):
        return self.cfg["label"]

    def chat(self, messages, temperature=0.7, max_tokens=2000, json_mode=False):
        """messages: [{"role":"system"|"user"|"assistant","content":"..."}] -> str"""
        if self.mock:
            return self._mock_chat(messages)
        provider = self.cfg["provider"]
        if provider in ("zhipu", "openai"):
            return self._chat_openai_compat(messages, temperature, max_tokens, json_mode)
        if provider == "gemini":
            return self._chat_gemini(messages, temperature, max_tokens, json_mode)
        raise NotImplementedError(f"未实现的 provider：{provider}")

    def _chat_openai_compat(self, messages, temperature, max_tokens, json_mode=False):
        body = {
            "model": self.cfg["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(
            self.cfg["endpoint"],
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _chat_gemini(self, messages, temperature, max_tokens, json_mode=False):
        contents = []
        system_text = ""
        for m in messages:
            if m["role"] == "system":
                system_text += m["content"] + "\n"
            else:
                contents.append({"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]})
        gen_cfg = {"temperature": temperature, "maxOutputTokens": max_tokens}
        if json_mode:
            gen_cfg["responseMimeType"] = "application/json"
            gen_cfg["thinkingConfig"] = {"thinkingBudget": 2048}
        body = {
            "contents": contents,
            "generationConfig": gen_cfg,
        }
        if system_text:
            body["systemInstruction"] = {"parts": [{"text": system_text}]}
        url = f"{self.cfg['endpoint']}?key={self.api_key}"
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _mock_chat(self, messages):
        """mock 模式：直接返回占位文本，由 analyst 负责生成结构化结果。"""
        joined = "\n".join(m.get("content", "") for m in messages)
        if "PREDICT" in joined or "预测" in joined:
            return '{"mock": true}'
        return "（mock 模式占位输出 —— analyst 会在 mock 下自行生成结构化结果）"
