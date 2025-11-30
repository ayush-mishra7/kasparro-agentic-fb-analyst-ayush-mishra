import json
import uuid
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("logs") / "events.log.jsonl"

def _now_iso():
    return datetime.utcnow().isoformat() + "Z"

def make_trace_id() -> str:
    return uuid.uuid4().hex

def make_span_id() -> str:
    return uuid.uuid4().hex

def _ensure_jsonable(v):
    try:
        json.dumps(v)
        return v
    except Exception:
        try:
            import numpy as _np
            if isinstance(v, (_np.integer,)):
                return int(v)
            if isinstance(v, (_np.floating,)):
                return float(v)
            if isinstance(v, _np.ndarray):
                return v.tolist()
        except Exception:
            pass
        return str(v)

def log_event(event_type, payload=None, trace_id=None, span_id=None, parent_span_id=None, agent=None):
    p = payload or {}
    p2 = {k: _ensure_jsonable(v) for k, v in p.items()}
    entry = {
        "timestamp": _now_iso(),
        "trace_id": trace_id or make_trace_id(),
        "span_id": span_id or None,
        "parent_span_id": parent_span_id or None,
        "agent": agent or None,
        "event_type": event_type,
        "payload": p2,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[{event_type}] {entry['payload']}")
    return entry

def start_span(event_type, trace_id=None, parent_span_id=None, agent=None):
    trace_id = trace_id or make_trace_id()
    span_id = make_span_id()
    event = f"{event_type}.start"
    log_event(event, {}, trace_id=trace_id, span_id=span_id, parent_span_id=parent_span_id, agent=agent)
    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "event_type": event_type,
        "parent_span_id": parent_span_id,
        "agent": agent,
        "started_at": _now_iso(),
    }

def end_span(span_ctx):
    if not span_ctx:
        return None
    if isinstance(span_ctx, dict):
        trace_id = span_ctx.get("trace_id")
        span_id = span_ctx.get("span_id")
        event_type = span_ctx.get("event_type")
        agent = span_ctx.get("agent")
        event = f"{event_type}.end"
        log_event(event, {}, trace_id=trace_id, span_id=span_id, parent_span_id=span_ctx.get("parent_span_id"), agent=agent)
        return True
    return None
