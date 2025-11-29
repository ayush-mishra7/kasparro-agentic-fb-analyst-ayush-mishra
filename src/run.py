import sys
from pathlib import Path
import pandas as pd

from utils.logging_utils import start_span, end_span, log_event
from agents.planner import PlannerAgent
from utils.data_utils import load_dataset
from agents.insight_agent import InsightAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.creative_agent import CreativeAgent
from agents.report_agent import ReportAgent

def main():
    root_span = start_span("pipeline.start", agent="Pipeline")

    try:
        planner = PlannerAgent()
        planner_span = start_span(
            "planner.run",
            trace_id=root_span["trace_id"],
            parent_span_id=root_span["span_id"],
            agent="PlannerAgent"
        )
        plan = planner.generate_plan(trace_id=planner_span["trace_id"])
        end_span(planner_span)

        if "load_dataset" in plan:
            ds_span = start_span(
                "dataset.load",
                trace_id=root_span["trace_id"],
                parent_span_id=root_span["span_id"]
            )
            df = load_dataset()
            end_span(ds_span)
        else:
            df = None

        if "generate_insights" in plan:
            insight_agent = InsightAgent()
            ins_span = start_span(
                "insight.generate",
                trace_id=root_span["trace_id"],
                parent_span_id=root_span["span_id"]
            )
            insights = insight_agent.generate_insights(
                df,
                trace_id=root_span["trace_id"],
                parent_span=ins_span["span_id"]
            )
            end_span(ins_span)
        else:
            insights = {"hypotheses": []}

        if "evaluate_insights" in plan:
            evaluator = EvaluatorAgent()
            ev_span = start_span(
                "insights.evaluate",
                trace_id=root_span["trace_id"],
                parent_span_id=root_span["span_id"]
            )
            evaluated = evaluator.evaluate(
                df,
                insights,
                trace_id=root_span["trace_id"],
                parent_span=ev_span["span_id"]
            )
            end_span(ev_span)
        else:
            evaluated = {"hypotheses": []}

        if "generate_creatives" in plan:
            creative = CreativeAgent()
            cr_span = start_span(
                "creatives.generate",
                trace_id=root_span["trace_id"],
                parent_span_id=root_span["span_id"]
            )
            creatives = creative.generate_creatives(
                evaluated,
                trace_id=root_span["trace_id"],
                parent_span=cr_span["span_id"]
            )
            end_span(cr_span)
        else:
            creatives = {"creatives": []}

        if "generate_report" in plan:
            reporter = ReportAgent()
            rp_span = start_span(
                "report.generate",
                trace_id=root_span["trace_id"],
                parent_span_id=root_span["span_id"]
            )
            reporter.run(
                evaluated,
                creatives,
                trace_id=root_span["trace_id"],
                parent_span=rp_span["span_id"]
            )
            end_span(rp_span)

    except Exception as e:
        log_event(
            "pipeline.error",
            {"error": str(e)},
            trace_id=root_span["trace_id"],
            agent="Pipeline"
        )

    finally:
        end_span(root_span)

if __name__ == "__main__":
    main()
