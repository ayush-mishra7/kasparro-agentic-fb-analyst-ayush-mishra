import json
import uuid
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "events.log.jsonl"

def _now_iso():
    return datetime.utcnow().isoformat() + "Z"

def make_trace_id():
    return uuid.uuid4().hex

def make_span_id():
    return uuid.uuid4().hex

class SpanCtx(dict):
    def __init__(self, d):
        super().__init__(d)
    @property
    def span_id(self):
        return self.get("span_id")
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

def _ensure_jsonable(v):
    try:
        json.dumps(v)
        return v
    except Exception:
        return str(v)

def log_event(event_type, payload=None, trace_id=None, span_id=None, parent_span_id=None, agent=None):
    p = payload or {}
    p2 = {k: _ensure_jsonable(v) for k, v in p.items()}
    entry = {
        "timestamp": _now_iso(),
        "trace_id": trace_id or make_trace_id(),
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "agent": agent,
        "event_type": event_type,
        "payload": p2,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[{event_type}] {p2}")
    return entry["trace_id"]

def start_span(event_type=None, trace_id=None, parent_span_id=None, agent=None, payload=None, **kwargs):
    if event_type is None and "event" in kwargs:
        event_type = kwargs.get("event")
    if trace_id is None:
        trace_id = make_trace_id()
    span_id = make_span_id()
    log_event(f"{event_type}.start", payload or {}, trace_id=trace_id, span_id=span_id, parent_span_id=parent_span_id, agent=agent)
    return SpanCtx({"trace_id": trace_id, "span_id": span_id, "event_type": event_type, "parent_span_id": parent_span_id, "agent": agent})

def end_span(span_ctx):
    if span_ctx is None:
        return
    if isinstance(span_ctx, tuple) or isinstance(span_ctx, list):
        if len(span_ctx) >= 2 and isinstance(span_ctx[1], dict):
            span_ctx = span_ctx[1]
    if not isinstance(span_ctx, dict) and not isinstance(span_ctx, SpanCtx):
        return
    trace_id = span_ctx.get("trace_id")
    span_id = span_ctx.get("span_id")
    event_type = span_ctx.get("event_type") or "span"
    parent_span_id = span_ctx.get("parent_span_id")
    agent = span_ctx.get("agent")
    log_event(f"{event_type}.end", {}, trace_id=trace_id, span_id=span_id, parent_span_id=parent_span_id, agent=agent)
