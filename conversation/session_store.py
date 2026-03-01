import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import uuid
import datetime

SESS_DIR = Path(".sessions")
SESS_DIR.mkdir(exist_ok=True)

def now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

@dataclass
class Session:
    session_id: str
    created_at: str
    state: str
    slots: Dict[str, Any]
    history: List[Dict[str, str]]
    package: Optional[Dict[str, Any]] = None

def new_session() -> Session:
    sid = str(uuid.uuid4())
    return Session(session_id=sid, created_at=now_iso(), state="INTRO", slots={}, history=[], package=None)

def path_for(session_id: str) -> Path:
    return SESS_DIR / f"{session_id}.json"

def save(sess: Session) -> None:
    path_for(sess.session_id).write_text(json.dumps(asdict(sess), ensure_ascii=False, indent=2), encoding="utf-8")

def load(session_id: str) -> Session:
    data = json.loads(path_for(session_id).read_text(encoding="utf-8"))
    return Session(**data)

def exists(session_id: str) -> bool:
    return path_for(session_id).exists()
