from typing import Dict, Any
import random
from utils.logging_utils import make_trace_id, start_span, log_event, end_span

PERSONAS = {"women": "Young Women", "men": "Young Men", "india": "Indian Audience", "video": "Fashion Enthusiasts"}
ANGLES = ["Empowerment", "Convenience", "Affordability", "Sustainability", "Confidence", "Quality", "Entertainment", "Inspiration", "Culture", "Modernity"]
CTA = ["Shop Now", "Learn More", "Buy Now"]
PLATFORMS = ["facebook", "instagram", "both"]

def choose_persona(hypothesis):
    seg = hypothesis.get("segment_filter", {})
    name = (seg.get("campaign_name") or "").lower()
    if "women" in name:
        return PERSONAS["women"]
    if "men" in name:
        return PERSONAS["men"]
    if "india" in name or "in" in name:
        return PERSONAS["india"]
    if "video" in name:
        return PERSONAS["video"]
    return "General Audience"

class CreativeAgent:
    def __init__(self, llm=None):
        self.llm = llm

    def generate_creatives(self, evaluated_insights: Dict[str, Any], trace_id: str = None, parent_span: str = None) -> Dict[str, Any]:
        trace_id = trace_id or make_trace_id()
        root_span = start_span("creative_agent.run", trace_id=trace_id, parent_span_id=parent_span, agent="CreativeAgent")
        hypotheses = evaluated_insights.get("hypotheses", [])
        creatives = []
        log_event("creative.start", {"hypotheses": len(hypotheses)}, trace_id=trace_id, parent_span_id=root_span["span_id"], agent="CreativeAgent")
        for hyp in hypotheses:
            hyp_id = hyp.get("id", "unknown")
            hyp_span = start_span(f"creative.generate.{hyp_id}", trace_id=trace_id, parent_span_id=root_span["span_id"], agent="CreativeAgent")
            persona = choose_persona(hyp)
            summary = hyp.get("summary", "Performance Improvement Opportunity")
            c1 = {"id": f"creative_{hyp_id}_1", "linked_hypothesis_id": hyp_id, "persona": persona, "angle": random.choice(ANGLES), "primary_text": f"Boost performance for {summary}", "headline": f"Improve results for {summary}", "description": f"This creative explores a new angle to fix: {summary}", "cta": random.choice(CTA), "platform": random.choice(PLATFORMS)}
            c2 = {"id": f"creative_{hyp_id}_2", "linked_hypothesis_id": hyp_id, "persona": persona, "angle": random.choice(ANGLES), "primary_text": f"Re-engage your audience for {summary}", "headline": f"Re-ignite {summary}", "description": f"Alternative concept to recover performance for: {summary}", "cta": random.choice(CTA), "platform": random.choice(PLATFORMS)}
            creatives.extend([c1, c2])
            log_event("creative.generated", {"hypothesis": hyp_id, "creatives_count": 2}, trace_id=trace_id, parent_span_id=hyp_span["span_id"], agent="CreativeAgent")
            end_span(hyp_span)
        log_event("creative.end", {"total_creatives": len(creatives)}, trace_id=trace_id, parent_span_id=root_span["span_id"], agent="CreativeAgent")
        end_span(root_span)
        return {"creatives": creatives}
