import httpx
from core.config import file_config, get_effective_api_key
from llm.base import LLMProvider, LLMResult

class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible Chat Completions client supporting OpenAI / Grok(xAI) / Gemini(OpenAI-compat)."""

    def __init__(self):
        self.provider = (file_config.llm.provider or "grok").lower()
        common = file_config.llm.common

        self.org_id = ""
        self.project_id = ""
        self.gemini_extra = None

        if self.provider == "openai":
            cfg = file_config.llm.openai
            self.base_url = cfg.base_url.rstrip("/")
            self.model = cfg.model
            self.org_id = (cfg.organization_id or "").strip()
            self.project_id = (cfg.project_id or "").strip()

        elif self.provider == "grok":
            cfg = file_config.llm.grok
            self.base_url = cfg.base_url.rstrip("/")
            self.model = cfg.model

        elif self.provider == "gemini":
            cfg = file_config.llm.gemini
            self.base_url = cfg.base_url.rstrip("/")
            self.model = cfg.model
            self.gemini_extra = {
                "google": {
                    "thinking_config": {
                        "thinking_level": getattr(cfg, "thinking_level", "low"),
                        "include_thoughts": bool(getattr(cfg, "include_thoughts", False)),
                    }
                }
            }
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        self.timeout = int(common.timeout_sec)
        self.api_key = get_effective_api_key()

    def generate_json(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> LLMResult:
        if not self.api_key:
            raise RuntimeError("Missing API key. Set REQ_AGENT_API_KEY (or XAI_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY).")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self.provider == "openai":
            if self.org_id:
                headers["OpenAI-Organization"] = self.org_id
            if self.project_id:
                headers["OpenAI-Project"] = self.project_id

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }

        if self.provider == "gemini" and self.gemini_extra:
            payload["extra_body"] = self.gemini_extra

        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(url, headers=headers, json=payload)
            if r.status_code >= 400:
                raise RuntimeError(f"LLM error {r.status_code}: {r.text}")
            data = r.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {}) or {}
        tokens_in = int(usage.get("prompt_tokens", 0))
        tokens_out = int(usage.get("completion_tokens", 0))

        cost_estimate = 0.0
        if isinstance(data, dict) and "cost_in_usd_ticks" in data:
            try:
                cost_estimate = float(data.get("cost_in_usd_ticks", 0.0))
            except Exception:
                cost_estimate = 0.0

        return LLMResult(content=content, tokens_in=tokens_in, tokens_out=tokens_out, cost_estimate=cost_estimate)
