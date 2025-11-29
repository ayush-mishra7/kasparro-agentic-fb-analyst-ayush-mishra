import json
import os
from datetime import datetime
from pathlib import Path

DL_DIR = Path("dead_letter")
DL_DIR.mkdir(exist_ok=True)


def write_dead_letter(name: str, payload: dict):
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    file = DL_DIR / f"{name}_{ts}.json"
    with open(file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return str(file)
