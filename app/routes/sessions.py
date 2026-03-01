from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from core.guardrails import guardrails_check
from core.redaction import redact_if_enabled
from conversation.session_store import new_session, save, load, exists
from conversation.engine import build_intro_message, current_question, set_slot, next_state, summary_from_slots, is_finalize_command
from services.finalizer import build_package_from_session

router = APIRouter()

class CreateSessionResponse(BaseModel):
    session_id: str
    assistant_message: str

class UserMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=200000)

class UserMessageResponse(BaseModel):
    session_id: str
    state: str
    assistant_message: str
    question: str | None = None
    has_package: bool = False
    package: dict | None = None

@router.post("/sessions", response_model=CreateSessionResponse)
def create_session():
    sess = new_session()
    assistant = build_intro_message()
    sess.history.append({"role":"assistant","content":assistant})
    save(sess)
    return CreateSessionResponse(session_id=sess.session_id, assistant_message=assistant)

@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    if not exists(session_id):
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    sess = load(session_id)
    return {"session_id": sess.session_id, "created_at": sess.created_at, "state": sess.state, "slots": sess.slots, "history": sess.history[-50:], "has_package": sess.package is not None, "package": sess.package}

@router.post("/sessions/{session_id}/message", response_model=UserMessageResponse)
def send_message(session_id: str, req: UserMessageRequest):
    if not exists(session_id):
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    sess = load(session_id)

    decision = guardrails_check(req.message)
    if not decision.allowed:
        return UserMessageResponse(session_id=sess.session_id, state=sess.state, assistant_message=decision.message, question=None, has_package=sess.package is not None, package=sess.package)

    if is_finalize_command(req.message):
        pkg = build_package_from_session(sess)
        sess.package = pkg
        save(sess)
        return UserMessageResponse(session_id=sess.session_id, state=sess.state, assistant_message="✅ Pacote gerado. Export DOCX/MD e relatório do analista em artifacts/.", question=None, has_package=True, package=pkg)

    user_text, _ = redact_if_enabled(req.message)
    sess.history.append({"role":"user","content": req.message})

    if sess.state == "INTRO":
        sess.slots["initial_context"] = user_text[:2000]
        sess.state = "GOAL"
        assistant = "Entendi. Vamos estruturar isso. Primeira pergunta:"
        q = current_question(sess.state)
        sess.history.append({"role":"assistant","content":assistant})
        sess.history.append({"role":"assistant","content":q})
        save(sess)
        return UserMessageResponse(session_id=sess.session_id, state=sess.state, assistant_message=assistant, question=q, has_package=False, package=None)

    sess.slots = set_slot(sess.state, user_text, sess.slots)
    sess.state = next_state(sess.state)

    if sess.state == "DONE":
        assistant = summary_from_slots(sess.slots) + "\n\nQuando quiser, digite **gerar** para produzir o pacote."
        q = current_question("DONE")
    else:
        assistant = "Ok."
        q = current_question(sess.state)

    sess.history.append({"role":"assistant","content":assistant})
    sess.history.append({"role":"assistant","content":q})
    save(sess)

    return UserMessageResponse(session_id=sess.session_id, state=sess.state, assistant_message=assistant, question=q, has_package=sess.package is not None, package=sess.package)
