# req-agent (v0.6)

Agente conversacional para levantamento de requisitos (PT-BR), com 1 pergunta por vez (após a resposta) e comando **gerar** a qualquer momento.

## Configuração
```bash
cp configs/app.sample.yaml configs/app.yaml
```

Crie `.env`:
```bash
cat > .env <<'EOF'
REQ_AGENT_API_KEY=SEU_TOKEN_AQUI
# ou: XAI_API_KEY=SEU_TOKEN_AQUI
EOF
```

## Executar
API:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

UI:
```bash
streamlit run ui/streamlit_app.py --server.port 8501
```

## Saídas
- Pacote JSON validado pelo schema (sem campos extras)
- Export DOCX/MD
- Relatório do analista salvo como `.md` em `artifacts/` (caminho registrado em `traceability.links`)
