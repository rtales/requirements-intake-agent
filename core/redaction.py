import re
from core.config import file_config

CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b")
EMAIL_RE = re.compile(r"\b[\w.\-+]+@[\w\-]+\.[\w\-\.]+\b")
TOKENLIKE_RE = re.compile(r"\b(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")

def redact(text: str) -> str:
    text = CPF_RE.sub("<ID>", text)
    text = EMAIL_RE.sub("<EMAIL>", text)
    text = TOKENLIKE_RE.sub("<SECRET>", text)
    return text

def redact_if_enabled(text: str):
    if not file_config.security.enable_redaction:
        return text, False
    redacted = redact(text)
    return redacted, (redacted != text)
