import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

LOGPATH = Path("logs/events.log.jsonl")


def parse_ts(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def load_events(path=LOGPATH):
    events = []
    if not path.exists():
        print(f"No log file at {path}. Run the pipeline to produce logs.")
        return events
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


def group_by_trace(events):
    traces = defaultdict(list)
    for e in events:
        traces[e.get("trace_id", "no-trace")].append(e)
    # sort each trace by timestamp
    for t, evs in traces.items():
        evs.sort(key=lambda e: parse_ts(e.get("timestamp", "")) or datetime.min)
    return traces


def pretty_print_trace(trace_id, events):
    print("=" * 80)
    print(f"Trace: {trace_id}  (events: {len(events)})")
    print("-" * 80)
    for e in events:
        ts = e.get("timestamp", "")
        agent = e.get("agent", "")
        etype = e.get("event_type", "")
        payload = e.get("payload", {})
        span = e.get("span_id", "")
        parent = e.get("parent_span_id", "")
        print(f"{ts} | {agent:12s} | {etype:30s} | span={span[:6]} parent={str(parent)[:6]} | {payload}")
    print("=" * 80)
    print()


def export_csv(trace_id, events, out_csv: Path):
    import csv
    rows = []
    for e in events:
        rows.append({
            "trace_id": e.get("trace_id"),
            "timestamp": e.get("timestamp"),
            "agent": e.get("agent"),
            "event_type": e.get("event_type"),
            "span_id": e.get("span_id"),
            "parent_span_id": e.get("parent_span_id"),
            "payload": json.dumps(e.get("payload", {}), ensure_ascii=False)
        })
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["trace_id","timestamp","agent","event_type","span_id","parent_span_id","payload"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote CSV with {len(rows)} rows to {out_csv}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", "-c", type=str, help="Export CSV path")
    args = parser.parse_args()

    events = load_events()
    if not events:
        return

    traces = group_by_trace(events)

    # print latest 3 traces (sorted by last event time)
    ranked = sorted(traces.items(), key=lambda kv: parse_ts(kv[1][-1].get("timestamp","")) or datetime.min, reverse=True)
    top = ranked[:5]

    for trace_id, evs in top:
        pretty_print_trace(trace_id, evs)
        if args.csv:
            export_csv(trace_id, evs, Path(args.csv))

if __name__ == "__main__":
    main()
