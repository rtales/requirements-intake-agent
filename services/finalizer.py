import json
import uuid
import hashlib
from pathlib import Path
from jsonschema import validate
from core.config import file_config
from llm.providers.openai_compatible import OpenAICompatibleProvider
from conversation.session_store import Session
from conversation.engine import summary_from_slots

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "requirement.v1.json"

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _selected_model() -> str:
    p = (file_config.llm.provider or "grok").lower()
    if p == "openai":
        return file_config.llm.openai.model
    if p == "grok":
        return file_config.llm.grok.model
    if p == "gemini":
        return file_config.llm.gemini.model
    return "unknown"

def _base_package(sess: Session) -> dict:
    slots = sess.slots
    title = slots.get("title") or f"Pacote de Requisitos — {str(slots.get('goal','a definir'))[:60]}"
    person = {"name":"unknown","role":"unknown","area":"unknown","email":"","phone":""}
    return {
        "meta": {
            "id": f"REQ-{str(uuid.uuid4())[:8]}",
            "title": title if len(title) >= 5 else "Pacote de Requisitos",
            "created_at": sess.created_at,
            "version": "v1",
            "status": "draft",
            "owner_area": slots.get("owner_area","unknown"),
            "source": {"channel":"free_text","raw_hash": sha256(json.dumps(sess.history, ensure_ascii=False)), "redaction_applied": bool(file_config.security.enable_redaction), "attachments":[]},
            "classification": {"sensitivity":"internal","domain":"other","confidence":0.7},
            "llm_trace": {"provider": file_config.llm.provider, "model": _selected_model(), "tokens_in": 0, "tokens_out": 0, "cost_estimate": 0.0, "run_id": str(uuid.uuid4()), "policy": "conversational-v6"}
        },
        "problem": {"context": slots.get("current_process","a definir"), "pain_points": slots.get("pain_points", []) or ["a definir"], "goal": slots.get("goal","a definir"), "success_definition": slots.get("success_definition", []) or ["a definir"]},
        "scope": {"in_scope": slots.get("in_scope", []) or ["a definir"], "out_of_scope": slots.get("out_of_scope", []) or ["a definir"], "assumptions": slots.get("assumptions", []) or [], "constraints": slots.get("constraints", []) or slots.get("deployment_constraints", []) or []},
        "stakeholders": {"requester": person, "product_owner": person, "tech_lead": person, "approvers": [], "users": slots.get("users", []) or ["a definir"]},
        "requirements": [],
        "acceptance_criteria": [],
        "nfr": {
            "security": {"status":"unknown","notes": str(slots.get("nfr_notes",""))[:500], "checks":[]},
            "privacy": {"status":"unknown","notes":"", "checks":[]},
            "availability": {"status":"unknown","notes":"", "checks":[]},
            "performance": {"status":"unknown","notes":"", "checks":[]},
            "observability": {"status":"unknown","notes":"", "checks":[]},
            "usability": {"status":"unknown","notes":"", "checks":[]},
            "compliance": {"status":"unknown","notes":"", "checks":[]},
        },
        "open_questions": [],
        "risks": [],
        "traceability": {"decision_log": [], "links": []}
    }

def _llm_generate_lists(pkg: dict, sess: Session) -> dict:
    provider = OpenAICompatibleProvider()
    summary = summary_from_slots(sess.slots)
    system = "Você é um analista de requisitos sênior. Responda em JSON. Não invente fatos."
    user = (
        "RESUMO:\n" + summary + "\n\n"
        "Gere JSON com: requirements, acceptance_criteria, open_questions, risks.\n"
        "IDs: R001.., AC001.., Q001.., RK001..\n"
        "requirement.type: functional|data|integration|reporting|ux|operational|security\n"
        "priority: must|should|could|wont\n"
        "evidence.source_ref: CHAT:session\n"
        "evidence.source_excerpt <=240 chars\n"
        "open_questions.status: open|answered|parked\n"
        "risks.impact/likelihood: low|medium|high\n"
    )
    res = provider.generate_json(system_prompt=system, user_prompt=user, max_tokens=file_config.llm.common.max_tokens, temperature=file_config.llm.common.temperature)
    data = json.loads(res.content)
    pkg["meta"]["llm_trace"]["tokens_in"] = int(res.tokens_in)
    pkg["meta"]["llm_trace"]["tokens_out"] = int(res.tokens_out)
    pkg["meta"]["llm_trace"]["cost_estimate"] = float(res.cost_estimate)
    pkg["requirements"] = data.get("requirements", []) or []
    pkg["acceptance_criteria"] = data.get("acceptance_criteria", []) or []
    pkg["open_questions"] = data.get("open_questions", []) or []
    pkg["risks"] = data.get("risks", []) or []
    return pkg

def _fallback_lists(pkg: dict) -> dict:
    pkg["requirements"] = [
        {"id":"R001","type":"functional","statement":"O sistema deve registrar e armazenar as informações necessárias do pedido.","priority":"must","rationale":"Base do escopo.","dependencies":[],"evidence":{"source_excerpt":"Resumo da conversa","source_ref":"CHAT:session"},"tests":[]}
    ]
    pkg["acceptance_criteria"] = [{"id":"AC001","criterion":"É possível exportar o pacote em DOCX e MD a partir do JSON.","linked_requirements":["R001"]}]
    pkg["open_questions"] = [{"id":"Q001","question":"Quais integrações são obrigatórias na primeira versão?","why_it_matters":"Define esforço e dependências.","target":"Product/Tech lead","status":"open"}]
    pkg["risks"] = [{"id":"RK001","risk":"Escopo indefinido pode gerar retrabalho.","impact":"medium","likelihood":"high","mitigation":"Validar escopo antes do desenvolvimento.","owner":"Product owner","status":"open"}]
    return pkg

def _llm_generate_analyst_report_md(sess: Session) -> str:
    provider = OpenAICompatibleProvider()
    briefing = {
        "contexto_inicial": sess.slots.get("initial_context",""),
        "objetivo": sess.slots.get("goal",""),
        "usuarios": sess.slots.get("users", []),
        "processo_atual": sess.slots.get("current_process",""),
        "dores": sess.slots.get("pain_points", []),
        "sucesso": sess.slots.get("success_definition", []),
        "escopo": sess.slots.get("in_scope", []),
        "fora_escopo": sess.slots.get("out_of_scope", []),
        "regras_negocio": sess.slots.get("business_rules", []),
        "restricoes": sess.slots.get("constraints", []),
        "dados": sess.slots.get("data_inputs_outputs", []),
        "dados_sensiveis": sess.slots.get("sensitive_data", []),
        "integracoes": sess.slots.get("integrations", []),
        "execucao": sess.slots.get("deployment_constraints", []),
        "criterios_aceite_exemplos": sess.slots.get("acceptance_examples", []),
        "nao_funcionais": sess.slots.get("nfr_notes", ""),
        "riscos_dependencias": sess.slots.get("risks_dependencies", []),
    }
    system = "Você é um analista de requisitos sênior. Escreva em PT-BR, com pragmatismo. Não invente fatos."
    user = (
        "Gere um relatório em Markdown com as seções: Visão geral, Escopo, Regras e cenários, Requisitos MoSCoW, "
        "Critérios Given/When/Then, Não-funcionais, Dados, Integrações, Fluxos, Riscos, Perguntas em aberto (top 10), Plano MVP->v1->v2.\n\n"
        f"Briefing JSON:\n{json.dumps(briefing, ensure_ascii=False)}\n"
    )
    res = provider.generate_json(system_prompt=system, user_prompt=user, max_tokens=file_config.llm.common.max_tokens, temperature=file_config.llm.common.temperature)
    return res.content.strip()

def _save_analyst_report(req_id: str, md: str) -> str:
    out_dir = Path("artifacts")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{req_id}_analyst_report.md"
    path.write_text(md, encoding="utf-8")
    return str(path)

def build_package_from_session(sess: Session) -> dict:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    pkg = _base_package(sess)

    try:
        md = _llm_generate_analyst_report_md(sess)
        if md:
            report_path = _save_analyst_report(pkg["meta"]["id"], md)
            pkg["traceability"]["links"].append(report_path)
    except Exception:
        pass

    try:
        pkg = _llm_generate_lists(pkg, sess)
        validate(instance=pkg, schema=schema)
        return pkg
    except Exception:
        pkg = _fallback_lists(pkg)
        validate(instance=pkg, schema=schema)
        return pkg
