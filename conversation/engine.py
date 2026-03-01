from typing import Dict, Any, List
from conversation.states import FLOW
import re

FINALIZE_COMMANDS = {"gerar", "/gerar", "finalizar", "/finalizar", "encerrar", "fim", "generate", "/generate", "done", "/done"}

def _split_items(text: str) -> List[str]:
    raw = re.split(r"(?:\n|;|\r|\t|•|\-|\d+\.)+", text)
    return [x.strip() for x in raw if x.strip()][:15]

def _split_users(text: str) -> List[str]:
    raw = re.split(r"(?:\n|,|;|/|\||\s{2,})+", text)
    return [x.strip() for x in raw if x.strip()][:15]

def set_slot(state: str, user_text: str, slots: Dict[str, Any]) -> Dict[str, Any]:
    key = FLOW[state].slot
    if key == "users":
        slots[key] = _split_users(user_text)
    elif key in {
        "pain_points","success_definition","in_scope","out_of_scope","business_rules","constraints",
        "data_inputs_outputs","sensitive_data","integrations","deployment_constraints","acceptance_examples",
        "risks_dependencies"
    }:
        slots[key] = _split_items(user_text)
    elif key == "confirmed":
        slots[key] = user_text.strip().lower() in {"sim","s","ok","confirmo","confirmar","gerar","fim"}
    else:
        slots[key] = user_text.strip()[:2000]
    return slots

def build_intro_message() -> str:
    return (
        "Olá! Eu sou o **Agente de Levantamento de Requisitos**.\n\n"
        "Como funciona:\n"
        "- Você descreve o pedido rapidamente (3–5 linhas).\n"
        "- Eu faço **uma pergunta por vez**, sempre **depois** da sua resposta.\n"
        "- A qualquer momento você pode digitar **gerar** para criar o pacote de requisitos.\n\n"
        "Vamos começar: descreva o que você quer construir e por quê."
    )

def current_question(state: str) -> str:
    return FLOW[state].question

def next_state(state: str) -> str:
    return FLOW[state].next_state or state

def is_finalize_command(text: str) -> bool:
    return text.strip().lower() in FINALIZE_COMMANDS

def summary_from_slots(slots: Dict[str, Any]) -> str:
    def fmt_list(xs):
        if not xs:
            return "- (a definir)"
        return "\n".join([f"- {x}" for x in xs])

    return (
        "Resumo até aqui:\n\n"
        f"**Objetivo:** {slots.get('goal','a definir')}\n\n"
        f"**Usuários:**\n{fmt_list(slots.get('users', []))}\n\n"
        f"**Processo atual:** {slots.get('current_process','a definir')}\n\n"
        f"**Dores:**\n{fmt_list(slots.get('pain_points', []))}\n\n"
        f"**Sucesso:**\n{fmt_list(slots.get('success_definition', []))}\n\n"
        f"**Dentro do escopo:**\n{fmt_list(slots.get('in_scope', []))}\n\n"
        f"**Fora do escopo:**\n{fmt_list(slots.get('out_of_scope', []))}\n\n"
        f"**Regras de negócio:**\n{fmt_list(slots.get('business_rules', []))}\n\n"
        f"**Restrições:**\n{fmt_list(slots.get('constraints', []))}\n\n"
        f"**Dados:**\n{fmt_list(slots.get('data_inputs_outputs', []))}\n\n"
        f"**Dados sensíveis:**\n{fmt_list(slots.get('sensitive_data', []))}\n\n"
        f"**Integrações:**\n{fmt_list(slots.get('integrations', []))}\n\n"
        f"**Execução:**\n{fmt_list(slots.get('deployment_constraints', []))}\n\n"
        f"**Critérios de aceite (exemplos):**\n{fmt_list(slots.get('acceptance_examples', []))}\n\n"
        f"**Não-funcionais:** {slots.get('nfr_notes','a definir')}\n\n"
        f"**Riscos/dependências:**\n{fmt_list(slots.get('risks_dependencies', []))}\n"
    )
