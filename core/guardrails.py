import re
from dataclasses import dataclass
from core.config import file_config

@dataclass
class GuardrailsDecision:
    allowed: bool
    intent: str
    message: str = ""

INTENT_PATTERNS = [
    ("requirements_export", re.compile(r"\b(export|generate docx|docx|markdown|md|pdf)\b", re.I)),
    ("requirements_refine", re.compile(r"\b(refine|adjust|update|questions|gaps)\b", re.I)),
    ("requirements_intake", re.compile(r"\b(requirement|request|user stor(y|ies)|acceptance criteria|scope|nfr|backlog)\b", re.I)),
    ("faq_how_to_use", re.compile(r"\b(how to use|install|run|configure)\b", re.I)),
]

def classify_intent(text: str) -> str:
    for intent, pat in INTENT_PATTERNS:
        if pat.search(text):
            return intent
    return "unknown"

def guardrails_check(user_text: str) -> GuardrailsDecision:
    # Deny patterns from config
    for pat in file_config.guardrails.disallowed_patterns:
        if re.search(pat, user_text):
            msg = (
                "Out of scope for the Requirements Intake Agent. "
                "I can help convert your need into requirements (scope, user stories, acceptance criteria, NFRs). "
                "Describe the system or deliverable you need."
            )
            return GuardrailsDecision(allowed=False, intent="unknown", message=msg)

    intent = classify_intent(user_text)

    if intent == "unknown":
        # allow guided intake
        msg = (
            "I am the Requirements Intake Agent. "
            "Share (1) objective, (2) who will use it, (3) constraints/integrations, "
            "and I'll return a structured requirements package."
        )
        return GuardrailsDecision(allowed=True, intent="requirements_intake", message=msg)

    if intent not in file_config.guardrails.allowed_intents:
        msg = (
            "Out of scope for the Requirements Intake Agent. "
            "I can convert your need into a requirements package."
        )
        return GuardrailsDecision(allowed=False, intent=intent, message=msg)

    return GuardrailsDecision(allowed=True, intent=intent, message="")
