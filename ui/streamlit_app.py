import yaml
from pathlib import Path
import requests
import streamlit as st

CONFIG_PATH = Path("configs/app.yaml")
SAMPLE_PATH = Path("configs/app.sample.yaml")

def load_config():
    if not CONFIG_PATH.exists():
        return yaml.safe_load(SAMPLE_PATH.read_text(encoding="utf-8"))
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

def save_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")

st.set_page_config(page_title="req-agent — Chat de Requisitos", layout="wide")

st.sidebar.title("req-agent")
st.sidebar.caption("Agente de Levantamento de Requisitos")
api_base = st.sidebar.text_input("API base URL", value="http://127.0.0.1:8000/api/v1")

tab_chat, tab_settings = st.tabs(["Chat", "Configurações"])

with tab_settings:
    st.subheader("Configurações")
    cfg = load_config()
    cfg.setdefault("llm", {})
    cfg["llm"].setdefault("common", {})
    cfg["llm"].setdefault("openai", {})
    cfg["llm"].setdefault("grok", {})
    cfg["llm"].setdefault("gemini", {})

    providers = ["grok", "openai", "gemini"]
    provider = st.selectbox("Provedor LLM", providers, index=providers.index(cfg["llm"].get("provider","grok")) if cfg["llm"].get("provider") in providers else 0)
    cfg["llm"]["provider"] = provider

    st.markdown("### Provedor")
    if provider == "grok":
        cfg["llm"]["grok"]["base_url"] = st.text_input("base_url", value=cfg["llm"]["grok"].get("base_url","https://api.x.ai/v1"))
        cfg["llm"]["grok"]["model"] = st.text_input("model", value=cfg["llm"]["grok"].get("model","grok-4-0709"))
    elif provider == "openai":
        cfg["llm"]["openai"]["base_url"] = st.text_input("base_url", value=cfg["llm"]["openai"].get("base_url","https://api.openai.com/v1"))
        cfg["llm"]["openai"]["model"] = st.text_input("model", value=cfg["llm"]["openai"].get("model","gpt-4o-mini"))
    else:
        cfg["llm"]["gemini"]["base_url"] = st.text_input("base_url", value=cfg["llm"]["gemini"].get("base_url","https://generativelanguage.googleapis.com/v1beta/openai/"))
        cfg["llm"]["gemini"]["model"] = st.text_input("model", value=cfg["llm"]["gemini"].get("model","gemini-3-flash-preview"))

    st.markdown("### Parâmetros comuns")
    common = cfg["llm"]["common"]
    col1, col2, col3 = st.columns(3)
    common["temperature"] = col1.slider("temperature", 0.0, 1.0, float(common.get("temperature",0.2)), 0.05)
    common["max_tokens"] = col2.number_input("max_tokens", min_value=128, max_value=4096, value=int(common.get("max_tokens",1200)), step=64)
    common["timeout_sec"] = col3.number_input("timeout_sec", min_value=5, max_value=3600, value=int(common.get("timeout_sec",600)), step=5)
    cfg["llm"]["common"] = common

    if st.button("Salvar configurações"):
        save_config(cfg)
        st.success("Salvo. Reinicie a API para aplicar.")

with tab_chat:
    st.title("Chat de Requisitos")
    st.caption("Perguntas aparecem **após** sua resposta. Digite **gerar** a qualquer momento.")

    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_question" not in st.session_state:
        st.session_state.current_question = None
    if "package" not in st.session_state:
        st.session_state.package = None

    top = st.columns([1,1,1,2])
    if top[0].button("Nova sessão"):
        r = requests.post(f"{api_base}/sessions", timeout=60)
        r.raise_for_status()
        data = r.json()
        st.session_state.session_id = data["session_id"]
        st.session_state.messages = [{"role":"assistant","content": data["assistant_message"]}]
        st.session_state.current_question = None
        st.session_state.package = None
        st.rerun()

    if st.session_state.session_id:
        top[1].markdown(f"**Sessão:** `{st.session_state.session_id[:8]}…`")

        if top[2].button("Gerar pacote"):
            r = requests.post(f"{api_base}/sessions/{st.session_state.session_id}/finalize", timeout=300)
            if r.status_code != 200:
                st.error(r.text)
            else:
                st.session_state.package = r.json()["package"]
                st.success("Pacote gerado.")
                st.rerun()

    if st.session_state.session_id and st.session_state.current_question:
        st.info(f"**Pergunta:** {st.session_state.current_question}")

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if st.session_state.session_id:
        user_in = st.chat_input("Sua resposta (ou digite 'gerar')...")
        if user_in:
            st.session_state.messages.append({"role":"user","content": user_in})
            r = requests.post(f"{api_base}/sessions/{st.session_state.session_id}/message", json={"message": user_in}, timeout=300)
            if r.status_code != 200:
                st.session_state.messages.append({"role":"assistant","content": f"Erro: {r.text}"})
            else:
                data = r.json()
                st.session_state.messages.append({"role":"assistant","content": data["assistant_message"]})
                st.session_state.current_question = data.get("question")
                if data.get("has_package") and data.get("package"):
                    st.session_state.package = data.get("package")
            st.rerun()

    if st.session_state.package:
        st.divider()
        st.subheader("Saídas")
        pkg = st.session_state.package

        links = (pkg.get("traceability") or {}).get("links") or []
        report_path = next((x for x in reversed(links) if str(x).endswith("_analyst_report.md")), None)
        if report_path:
            st.markdown("### Relatório do Analista (arquivo)")
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            except Exception:
                st.info(f"Relatório salvo em: {report_path}")

        st.markdown("### Pacote JSON (canônico)")
        st.json(pkg)

        c1, c2 = st.columns(2)
        if c1.button("Exportar DOCX"):
            r = requests.post(f"{api_base}/requirements/render/docx", json=pkg, timeout=180)
            st.write(r.json() if r.status_code == 200 else r.text)
        if c2.button("Exportar MD"):
            r = requests.post(f"{api_base}/requirements/render/md", json=pkg, timeout=180)
            st.write(r.json() if r.status_code == 200 else r.text)
