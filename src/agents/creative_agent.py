import random
from src.utils.logging_utils import start_span, end_span, log_event, make_trace_id

PERSONAS = {
    "women": "Young Women",
    "men": "Young Men",
    "india": "Indian Audience",
    "video": "Video Viewers",
}

ANGLES = [
    "Empowerment",
    "Affordability",
    "Convenience",
    "Sustainability",
    "Confidence",
    "Quality",
    "Entertainment",
    "Inspiration",
]

CTA = ["Shop Now", "Learn More", "Buy Now"]
PLATFORMS = ["facebook", "instagram", "both"]

def choose_persona(hyp):
    seg = hyp.get("segment_filter", {}) or {}
    c = str(seg.get("campaign_name", "")).lower()
    if "women" in c:
        return PERSONAS["women"]
    if "men" in c:
        return PERSONAS["men"]
    if "india" in c or str(seg.get("country", "")).lower() == "in":
        return PERSONAS["india"]
    if "video" in c:
        return PERSONAS["video"]
    return "General Audience"

class CreativeAgent:
    def __init__(self):
        pass

    def generate_creatives(self, evaluated_insights, trace_id: str = None, parent_span_id: str = None):
        trace_id = trace_id or make_trace_id()
        span = start_span("creatives.generate", trace_id=trace_id, parent_span_id=parent_span_id, agent="CreativeAgent")
        try:
            hyps = evaluated_insights.get("hypotheses", [])
            creatives = []
            log_event("creative.start", {"hypotheses": len(hyps)}, trace_id=trace_id, span_id=span["span_id"], agent="CreativeAgent")

            for h in hyps:
                hyp_id = h.get("id", f"hyp_{random.randint(1,99999)}")
                persona = choose_persona(h)
                summary = h.get("summary") or h.get("title") or "Performance opportunity"
                angle1 = ANGLES[hash(hyp_id + 'a') % len(ANGLES)]
                angle2 = ANGLES[hash(hyp_id + 'b') % len(ANGLES)]

                c1 = {
                    "id": f"creative_{hyp_id}_1",
                    "linked_hypothesis_id": hyp_id,
                    "persona": persona,
                    "angle": angle1,
                    "headline": f"Improve results for {summary}",
                    "primary_text": f"Boost performance by addressing: {summary}",
                    "description": f"This idea explores the '{angle1}' angle.",
                    "cta": CTA[hash(hyp_id + 'c1') % len(CTA)],
                    "platform": PLATFORMS[hash(hyp_id + 'p1') % len(PLATFORMS)],
                }
                c2 = {
                    "id": f"creative_{hyp_id}_2",
                    "linked_hypothesis_id": hyp_id,
                    "persona": persona,
                    "angle": angle2,
                    "headline": f"Re-engage audience for {summary}",
                    "primary_text": f"Recover performance for: {summary}",
                    "description": f"Alternative idea using the '{angle2}' angle.",
                    "cta": CTA[hash(hyp_id + 'c2') % len(CTA)],
                    "platform": PLATFORMS[hash(hyp_id + 'p2') % len(PLATFORMS)],
                }

                creatives.extend([c1, c2])
                log_event("creative.generated", {"hyp": hyp_id, "created": 2}, trace_id=trace_id, span_id=span["span_id"], agent="CreativeAgent")

            log_event("creative.end", {"total_creatives": len(creatives)}, trace_id=trace_id, span_id=span["span_id"], agent="CreativeAgent")
            return {"creatives": creatives}
        finally:
            end_span(span)
