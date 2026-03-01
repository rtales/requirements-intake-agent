from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml
from pathlib import Path

CONFIG_PATH = Path("configs/app.yaml")

class LLMCommonConfig(BaseModel):
    temperature: float = 0.2
    max_tokens: int = 1200
    timeout_sec: int = 600

class OpenAIConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    organization_id: str = ""
    project_id: str = ""

class GrokConfig(BaseModel):
    base_url: str = "https://api.x.ai/v1"
    model: str = "grok-4-0709"

class GeminiConfig(BaseModel):
    base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    model: str = "gemini-3-flash-preview"
    thinking_level: str = "low"
    include_thoughts: bool = False

class LLMConfig(BaseModel):
    provider: str = "grok"
    api_style: str = "chat_completions"
    common: LLMCommonConfig = LLMCommonConfig()
    openai: OpenAIConfig = OpenAIConfig()
    grok: GrokConfig = GrokConfig()
    gemini: GeminiConfig = GeminiConfig()

class GuardrailsConfig(BaseModel):
    max_input_chars: int = 12000
    max_questions_per_turn: int = 8
    max_llm_calls_per_request: int = 2
    allowed_intents: list[str] = ["requirements_intake","requirements_refine","requirements_export","faq_how_to_use"]
    disallowed_patterns: list[str] = []

class SecurityConfig(BaseModel):
    enable_redaction: bool = True
    store_raw_input: bool = False
    allowed_origins: list[str] = ["http://localhost:8501"]

class RedactionConfig(BaseModel):
    patterns: list[str] = ["cpf","email","tokenlike"]

class CostConfig(BaseModel):
    currency: str = "USD"
    monthly_budget: float = 50.0
    cache_enabled: bool = True

class FileConfig(BaseModel):
    name: str = "req-agent"
    env: str = "dev"

class AppFileConfig(BaseModel):
    app: FileConfig = FileConfig()
    llm: LLMConfig = LLMConfig()
    security: SecurityConfig = SecurityConfig()
    guardrails: GuardrailsConfig = GuardrailsConfig()
    redaction: RedactionConfig = RedactionConfig()
    cost: CostConfig = CostConfig()

def load_file_config() -> AppFileConfig:
    if not CONFIG_PATH.exists():
        return AppFileConfig()
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return AppFileConfig(**data)

class Settings(BaseSettings):
    req_agent_api_key: str = Field(default="", alias="REQ_AGENT_API_KEY")
    xai_api_key: str = Field(default="", alias="XAI_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    class Config:
        env_file = ".env"
        populate_by_name = True

settings = Settings()
file_config = load_file_config()

def get_effective_api_key() -> str:
    prov = (file_config.llm.provider or "grok").lower()
    if settings.req_agent_api_key:
        return settings.req_agent_api_key
    if prov == "grok" and settings.xai_api_key:
        return settings.xai_api_key
    if prov == "openai" and settings.openai_api_key:
        return settings.openai_api_key
    if prov == "gemini" and settings.gemini_api_key:
        return settings.gemini_api_key
    return ""
