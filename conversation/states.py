from dataclasses import dataclass
from typing import Dict, Optional

@dataclass(frozen=True)
class StateSpec:
    key: str
    title: str
    question: str
    slot: str
    next_state: Optional[str]

FLOW: Dict[str, StateSpec] = {
    "GOAL": StateSpec("GOAL","Objetivo","Qual é o objetivo principal (o que você quer alcançar)?","goal","USERS"),
    "USERS": StateSpec("USERS","Usuários","Quem vai usar o sistema (papéis/usuários)?","users","CURRENT_PROCESS"),
    "CURRENT_PROCESS": StateSpec("CURRENT_PROCESS","Processo atual","Como é o processo/ferramenta atual (hoje)?","current_process","PAIN_POINTS"),
    "PAIN_POINTS": StateSpec("PAIN_POINTS","Dores","Quais dores/problemas estamos resolvendo?","pain_points","SUCCESS"),
    "SUCCESS": StateSpec("SUCCESS","Sucesso","Como vamos saber que deu certo (métricas/definição de sucesso)?","success_definition","IN_SCOPE"),
    "IN_SCOPE": StateSpec("IN_SCOPE","Escopo","O que está dentro do escopo (capacidades principais)?","in_scope","OUT_SCOPE"),
    "OUT_SCOPE": StateSpec("OUT_SCOPE","Fora do escopo","O que fica fora do escopo (explicitamente excluído)?","out_of_scope","BUSINESS_RULES"),
    "BUSINESS_RULES": StateSpec("BUSINESS_RULES","Regras de negócio","Quais regras de negócio/políticas devem ser seguidas?","business_rules","CONSTRAINTS"),
    "CONSTRAINTS": StateSpec("CONSTRAINTS","Restrições","Há aprovações, SLA, restrições ou 'não-negociáveis'?","constraints","DATA"),
    "DATA": StateSpec("DATA","Dados","Quais dados entram e saem (inputs/outputs)?","data_inputs_outputs","SENSITIVE_DATA"),
    "SENSITIVE_DATA": StateSpec("SENSITIVE_DATA","Dados sensíveis","Há dados sensíveis que devem ser evitados/mascarados?","sensitive_data","INTEGRATIONS"),
    "INTEGRATIONS": StateSpec("INTEGRATIONS","Integrações","Com quais sistemas deve integrar (se houver)?","integrations","DEPLOYMENT"),
    "DEPLOYMENT": StateSpec("DEPLOYMENT","Execução","Há restrições de onde roda (local/on-prem/cloud)?","deployment_constraints","ACCEPTANCE"),
    "ACCEPTANCE": StateSpec("ACCEPTANCE","Critérios de aceite","Dê 2–5 exemplos do que é 'pronto' (critérios de aceite).","acceptance_examples","NFR"),
    "NFR": StateSpec("NFR","Não-funcionais","Requisitos não-funcionais (segurança/privacidade, desempenho, disponibilidade, auditoria/logs)?","nfr_notes","RISKS"),
    "RISKS": StateSpec("RISKS","Riscos","Quais riscos ou dependências podem bloquear a entrega?","risks_dependencies","DONE"),
    "DONE": StateSpec("DONE","Encerramento","Quando quiser, digite **gerar** para criar o pacote (ou envie mais detalhes).","confirmed",None),
}
