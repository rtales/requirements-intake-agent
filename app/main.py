from fastapi import FastAPI
from app.routes import requirements, sessions
from core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="req-agent",
    version="0.6.0",
    description="Agente de Levantamento de Requisitos (PT-BR, pergunta após resposta, Grok por padrão).",
)

app.include_router(requirements.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")

@app.get("/healthz")
def healthz():
    return {"ok": True}
