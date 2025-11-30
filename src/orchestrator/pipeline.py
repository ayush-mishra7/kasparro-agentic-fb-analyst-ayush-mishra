import os
import json
from src.utils.logging_utils import log_event, make_trace_id
from src.utils.data_utils import load_dataset, compute_basic_aggregates
from src.utils.llm_client import LLMClient
from src.agents.insight_agent import InsightAgent
from src.agents.planner import PlannerAgent
from src.agents.evaluator_agent import EvaluatorAgent
from src.agents.creative_agent import CreativeAgent

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def save_report(path, evaluated_insights, creatives):
    lines = ["# FB Ads Performance Analysis Report", ""]
    lines.append("## Insights (validated)")
    for h in evaluated_insights.get("hypotheses", []):
        title = h.get("title", h.get("id", "hypothesis"))
        summary = h.get("summary", "")
        val = h.get("validation", {})
        lines.append(f"### {title}")
        lines.append(f"{summary}")
        lines.append("")
        lines.append(f"- Segment filter: {h.get('segment_filter')}")
        lines.append(f"- Sample size: {val.get('sample_size')}")
        lines.append(f"- Mean CTR: {val.get('mean_ctr')}")
        lines.append(f"- Mean ROAS: {val.get('mean_roas')}")
        lines.append(f"- Confidence: {val.get('confidence')}")
        lines.append("")
    lines.append("## Creative Ideas")
    for c in creatives.get("creatives", []):
        lines.append(f"### {c.get('headline','Creative')}")
        lines.append(f"- {c.get('primary_text')}")
        lines.append(f"- CTA: {c.get('cta')}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def run_pipeline(user_query: str):
    cfg = {}
    reports_dir = "reports"
    ensure_dir(reports_dir)
    df = load_dataset()
    data_summary = compute_basic_aggregates(df)
    log_event("data_ready", {"rows": len(df)})
    try:
        llm = LLMClient()
    except Exception as e:
        log_event("llm_init_failed", {"error": str(e)})
        llm = None
    planner = PlannerAgent(llm) if llm else PlannerAgent(None)
    plan = planner.plan(user_query, data_summary) if hasattr(planner, "plan") else planner.generate_plan()
    log_event("planner_done", {"plan": plan})
    insight_agent = InsightAgent(llm)
    insights = insight_agent.generate_insights(df)
    log_event("insights_generated", {"count": len(insights.get("hypotheses", []))})
    evaluator = EvaluatorAgent()
    evaluated = evaluator.evaluate(df, insights)
    log_event("insights_evaluated", {"count": len(evaluated.get("hypotheses", []))})
    creative_agent = CreativeAgent(llm)
    creatives = creative_agent.generate_creatives(evaluated)
    log_event("creatives_generated", {"count": len(creatives.get("creatives", []))})
    insights_path = os.path.join(reports_dir, "insights.json")
    creatives_path = os.path.join(reports_dir, "creatives.json")
    report_path = os.path.join(reports_dir, "report.md")
    save_json(insights_path, evaluated)
    save_json(creatives_path, creatives)
    save_report(report_path, evaluated, creatives)
    log_event("pipeline_complete", {"insights": insights_path, "creatives": creatives_path, "report": report_path})
