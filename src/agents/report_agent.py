from pathlib import Path
import json
from typing import Dict, Any, List
from datetime import datetime
from src.utils.logging_utils import start_span, end_span, log_event

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def _safe_json_dump(path: Path, obj: Any):
    def fix(o):
        try:
            json.dumps(o)
            return o
        except Exception:
            return str(o)
    def sanitize(x):
        if isinstance(x, dict):
            return {k: sanitize(v) for k, v in x.items()}
        if isinstance(x, list):
            return [sanitize(v) for v in x]
        return fix(x)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(sanitize(obj), fh, ensure_ascii=False, indent=2)

def _safe_markdown_dump(path: Path, insights: Dict[str, Any], creatives: Dict[str, Any]):
    lines: List[str] = []
    ts = datetime.utcnow().isoformat() + "Z"
    lines.append(f"# Agentic FB Analyst Report\n\nGenerated: {ts}\n\n---\n")
    lines.append("## Insights Summary\n")
    hyps = insights.get("hypotheses", [])
    if not hyps:
        lines.append("_No hypotheses generated._\n")
    else:
        for h in hyps:
            lines.append(f"### {h.get('id')} — {h.get('title')}\n")
            lines.append(f"{h.get('summary', '')}\n\n")
            val = h.get("validation")
            if val:
                lines.append("**Validation:**\n\n")
                for k, v in val.items():
                    lines.append(f"- {k}: {v}\n")
            lines.append("\n")
    lines.append("\n## Creative Suggestions\n")
    cr = creatives.get("creatives", [])
    if not cr:
        lines.append("_No creatives generated._\n")
    else:
        for c in cr[:6]:
            lines.append(f"- **{c.get('headline','(no headline)')}** — {c.get('primary_text','')}\n")
            lines.append(f"  - persona: {c.get('persona')} | angle: {c.get('angle')} | cta: {c.get('cta')}\n\n")
    path_text = "\nReports written:\n"
    path_text += f"- insights.json\n- creatives.json\n- report.md\n- summary.json\n"
    lines.append("\n---\n")
    lines.append(path_text)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

class ReportAgent:
    def __init__(self):
        self.report_dir = REPORT_DIR

    def generate(self, insights: Dict[str, Any], creatives: Dict[str, Any], trace_id: str = None, parent_span_id: str = None) -> Dict[str, Any]:
        span = start_span("report.generate", trace_id=trace_id, parent_span_id=parent_span_id, agent="ReportAgent")
        try:
            log_event("report_agent.start", {"insights": len(insights.get("hypotheses", [])) if isinstance(insights, dict) else 0}, trace_id=span["trace_id"], span_id=span["span_id"], agent="ReportAgent")
            validation = {"ok": True, "issues": [], "counts": {"insights": len(insights.get("hypotheses", [])) if isinstance(insights, dict) else 0, "creatives": len(creatives.get("creatives", [])) if isinstance(creatives, dict) else 0}}
            log_event("report_agent.validation", validation, trace_id=span["trace_id"], span_id=span["span_id"], agent="ReportAgent")

            insights_path = self.report_dir / "insights.json"
            creatives_path = self.report_dir / "creatives.json"
            report_md_path = self.report_dir / "report.md"
            summary_path = self.report_dir / "summary.json"

            try:
                _safe_json_dump(insights_path, insights)
                _safe_json_dump(creatives_path, creatives)
                _safe_markdown_dump(report_md_path, insights, creatives)

                summary = {
                    "written": {
                        "insights": str(insights_path),
                        "creatives": str(creatives_path),
                        "report_md": str(report_md_path),
                        "summary_json": str(summary_path)
                    },
                    "counts": validation.get("counts", {}),
                    "issues": validation.get("issues", []),
                    "generated_at": datetime.utcnow().isoformat() + "Z"
                }
                _safe_json_dump(summary_path, summary)
                log_event("report_agent.written", summary, trace_id=span["trace_id"], span_id=span["span_id"], agent="ReportAgent")
                return {"paths": summary["written"], "summary": summary}
            except Exception as e:
                err = {"error": str(e)}
                log_event("report_agent.error", err, trace_id=span["trace_id"], span_id=span["span_id"], agent="ReportAgent")
                return {"paths": {}, "summary": {"ok": False, "error": str(e)}}
        finally:
            end_span(span)
