from typing import List
from src.utils.logging_utils import start_span, end_span, log_event

class PlannerAgent:
    def __init__(self):
        pass

    def generate_plan(self) -> List[str]:
        span = start_span("planner.generate", agent="PlannerAgent")
        try:
            steps = [
                "load_dataset",
                "generate_insights",
                "evaluate_insights",
                "generate_creatives",
                "generate_report",
            ]
            log_event("planner.plan.created", {"steps": steps}, trace_id=span["trace_id"], span_id=span["span_id"], agent="PlannerAgent")
            return steps
        finally:
            end_span(span)

    def run(self, trace_id: str = None) -> List[str]:
        span = start_span("planner.run", trace_id=trace_id, agent="PlannerAgent")
        try:
            plan = self.generate_plan()
            log_event("planner.plan.generated", {"count": len(plan)}, trace_id=span["trace_id"], span_id=span["span_id"], agent="PlannerAgent")
            return plan
        finally:
            end_span(span)
