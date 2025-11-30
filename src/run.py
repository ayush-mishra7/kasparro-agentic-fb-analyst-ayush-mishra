from src.utils.logging_utils import start_span, end_span, log_event
from src.utils.data_utils import load_dataset
from src.agents.planner import PlannerAgent
from src.agents.insight_agent import InsightAgent
from src.agents.evaluator_agent import EvaluatorAgent
from src.agents.creative_agent import CreativeAgent
from src.agents.report_agent import ReportAgent

def main():
    root = start_span("pipeline.start", agent="Pipeline")

    try:
        planner = PlannerAgent()
        pspan = start_span("planner.run", trace_id=root["trace_id"], agent="PlannerAgent")
        plan = planner.run(trace_id=pspan["trace_id"])
        end_span(pspan)

        if "load_dataset" in plan:
            ds = start_span("dataset.load", trace_id=root["trace_id"], agent="Dataset")
            df = load_dataset()
            end_span(ds)
        else:
            df = None

        if "generate_insights" in plan:
            ins_agent = InsightAgent()
            ins = start_span("insight.generate", trace_id=root["trace_id"], agent="InsightAgent")
            insights = ins_agent.generate(df)
            end_span(ins)
        else:
            insights = None

        if "evaluate_insights" in plan:
            ev_agent = EvaluatorAgent()
            ev = start_span("insights.evaluate", trace_id=root["trace_id"], agent="EvaluatorAgent")
            insights = ev_agent.evaluate(df, insights)
            end_span(ev)

        if "generate_creatives" in plan:
            cr_agent = CreativeAgent()
            cr = start_span("creatives.generate", trace_id=root["trace_id"], agent="CreativeAgent")
            creatives = cr_agent.generate_creatives(insights)
            end_span(cr)
        else:
            creatives = None

        if "generate_report" in plan:
            rp_agent = ReportAgent()
            rp = start_span("report.generate", trace_id=root["trace_id"], agent="ReportAgent")
            rp_agent.generate(insights, creatives, trace_id=root["trace_id"])
            end_span(rp)

    except Exception as e:
        log_event("pipeline.error", {"error": str(e)}, trace_id=root["trace_id"], agent="Pipeline")
    finally:
        end_span(root)

if __name__ == "__main__":
    main()
