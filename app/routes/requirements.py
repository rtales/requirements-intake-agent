from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from core.config import file_config
from core.guardrails import guardrails_check
from core.redaction import redact_if_enabled
from services.requirements_service import RequirementsService

router = APIRouter()

class CreateRequirementRequest(BaseModel):
    raw_text: str = Field(..., min_length=10, max_length=200000)
    channel: str = Field(default="free_text")
    owner_area: str | None = None

@router.post("/requirements")
def create_requirement(req: CreateRequirementRequest):
    if len(req.raw_text) > file_config.guardrails.max_input_chars:
        raise HTTPException(status_code=413, detail="Input too large")
    decision = guardrails_check(req.raw_text)
    if not decision.allowed:
        raise HTTPException(status_code=400, detail=decision.message)
    raw_text_redacted, redaction_applied = redact_if_enabled(req.raw_text)
    svc = RequirementsService()
    return svc.generate_package(raw_text=raw_text_redacted, channel=req.channel, owner_area=req.owner_area, redaction_applied=redaction_applied)

@router.post("/requirements/render/docx")
def render_docx(package: dict):
    svc = RequirementsService()
    return {"path": svc.render_docx(package)}

@router.post("/requirements/render/md")
def render_md(package: dict):
    svc = RequirementsService()
    return {"path": svc.render_md(package)}
