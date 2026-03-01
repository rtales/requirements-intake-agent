import json, hashlib, uuid, datetime
from pathlib import Path
from jsonschema import validate
from core.config import file_config
from llm.providers.openai_compatible import OpenAICompatibleProvider
from docs_gen.render_docx import render_onepager_docx
from docs_gen.render_md import render_md

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "requirement.v1.json"

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def new_req_id() -> str:
    yr = datetime.datetime.utcnow().year
    return f"REQ-{yr}-{str(uuid.uuid4())[:8]}"

class RequirementsService:
    def __init__(self):
        self.provider = OpenAICompatibleProvider()

    def generate_package(self, *, raw_text: str, channel: str, owner_area: str | None, redaction_applied: bool):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        system_prompt = (
            "You are the Requirements Intake Agent. "
            "Convert the user's request into a JSON object that strictly conforms to the provided JSON Schema. "
            "Rules: do not invent facts; if something is missing, use 'unknown' (or empty lists where appropriate). "
            "Be concise and avoid redundancy. Return JSON only."
        )

        user_prompt = (
            "JSON SCHEMA:\n"
            f"{json.dumps(schema, ensure_ascii=False)}\n\n"
            "USER REQUEST (free text):\n"
            f"{raw_text}\n\n"
            "OUTPUT RULES:\n"
            "- Return ONLY valid JSON.\n"
            "- Generate IDs: R001.., AC001.., Q001.., RK001..\n"
            "- For evidence.source_excerpt, use short quotes from the request.\n"
        )

        res = self.provider.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=file_config.llm.common.max_tokens,
            temperature=file_config.llm.common.temperature,
        )

        package = json.loads(res.content)
        validate(instance=package, schema=schema)

        # Enforce traceability defaults
        package["meta"].setdefault("created_at", now_iso())
        package["meta"].setdefault("id", new_req_id())
        package["meta"].setdefault("owner_area", owner_area or "unknown")
        package["meta"]["source"]["channel"] = channel
        package["meta"]["source"]["raw_hash"] = sha256(raw_text)
        package["meta"]["source"]["redaction_applied"] = bool(redaction_applied)

        package["meta"]["llm_trace"].setdefault("provider", file_config.llm.provider)
        package["meta"]["llm_trace"].setdefault("model", file_config.llm.model)
        package["meta"]["llm_trace"]["tokens_in"] = int(res.tokens_in)
        package["meta"]["llm_trace"]["tokens_out"] = int(res.tokens_out)
        package["meta"]["llm_trace"]["cost_estimate"] = float(res.cost_estimate)
        package["meta"]["llm_trace"].setdefault("run_id", str(uuid.uuid4()))
        package["meta"]["llm_trace"].setdefault("policy", "pilot-readonly")

        return package

    def render_docx(self, package: dict) -> str:
        out_dir = Path("artifacts")
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"{package['meta']['id']}_onepager.docx"
        render_onepager_docx(package, out_path)
        return str(out_path)

    def render_md(self, package: dict) -> str:
        out_dir = Path("artifacts")
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"{package['meta']['id']}.md"
        out_path.write_text(render_md(package), encoding="utf-8")
        return str(out_path)
