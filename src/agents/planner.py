from utils.logging_utils import start_span, end_span

class PlannerAgent:
    def __init__(self, llm=None):
        self.llm = llm

    def generate_plan(self, trace_id=None):
        span = start_span("planner.generate", trace_id=trace_id, agent="PlannerAgent")
        steps = ["load_dataset", "generate_insights", "evaluate_insights", "generate_creatives", "generate_report"]
        end_span(span)
        return steps

    def run(self, trace_id=None):
        span = start_span("planner.run", trace_id=trace_id, agent="PlannerAgent")
        plan = self.generate_plan(trace_id=span["trace_id"])
        end_span(span)
        return plan
