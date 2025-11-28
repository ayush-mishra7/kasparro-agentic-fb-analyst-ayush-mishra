import json
import os
from datetime import datetime
from typing import Any, Dict
import yaml
import uuid

def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

_cfg = load_config()
LOG_DIR = _cfg["logging"]["log_dir"]
os.makedirs(LOG_DIR, exist_ok=True)

def log_event(event_type: str, payload: Dict[str, Any]) -> None:
    """
    Append a JSON log line for observability.
    """
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "payload": payload,
    }
    log_path = os.path.join(LOG_DIR, "events.log.jsonl")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")