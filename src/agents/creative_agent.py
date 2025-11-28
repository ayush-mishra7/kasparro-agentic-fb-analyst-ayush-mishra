# src/agents/creative_agent.py
import json
from typing import Dict, Any
from src.utils.llm_client import LLMClient
from src.utils.logging_utils import log_event
import uuid

class CreativeAgent:
    """
    Creative Agent:
    - Attempt LLM creative generation first.
    - If LLM returns no valid JSON creatives, fall back to deterministic templated creatives
      using the validated hypotheses.
    """

    def __init__(self, llm: LLMClient = None):
        self.llm = llm

    def _extract_json_block(self, text: str) -> Dict[str, Any]:
        try:
            # find first { and last } and parse JSON substring
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except Exception:
            return {"creatives": []}

    def _template_creatives_for_hypothesis(self, hyp: Dict[str, Any]) -> Dict[str, Any]:
        # Basic templated creative variations (2 per hypothesis)
        seg = hyp.get("segment_filter", {})
        persona_parts = []
        if seg.get("audience_type"):
            persona_parts.append(seg.get("audience_type"))
        if seg.get("country"):
            persona_parts.append(seg.get("country"))
        persona = ", ".join(persona_parts) if persona_parts else "target audience"

        creatives = []
        # Variation 1: Comfort / Benefit
        creatives.append({
            "id": f"creative_{uuid.uuid4().hex[:6]}",
            "linked_hypothesis_id": hyp.get("id"),
            "persona": persona,
            "angle": "Comfort & benefit",
            "primary_text": f"Experience all-day comfort and support. Our undergarments keep you comfortable and confident.",
            "headline": "Comfort That Works",
            "description": "Breathable, soft fabrics designed for everyday life.",
            "cta": "Shop Now",
            "platform": seg.get("platform") or "facebook|instagram|both"
        })
        # Variation 2: Offer / Value
        creatives.append({
            "id": f"creative_{uuid.uuid4().hex[:6]}",
            "linked_hypothesis_id": hyp.get("id"),
            "persona": persona,
            "angle": "Price / trial",
            "primary_text": f"Try our bestsellers risk-free — comfortable, durable, and now at a great price.",
            "headline": "Try it Risk-free",
            "description": "30-day money-back guarantee.",
            "cta": "Shop Now",
            "platform": seg.get("platform") or "facebook|instagram|both"
        })
        return {"creatives": creatives}

    def generate_creatives(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        # prefer hypotheses that evaluator marked as low CTR or low ROAS (if any)
        candidates = []
        for h in insights.get("hypotheses", []):
            v = h.get("validation", {})
            # treat None as candidate, and also use thresholds
            if v.get("mean_ctr") is None or (isinstance(v.get("mean_ctr"), (int, float)) and v["mean_ctr"] < 0.02):
                candidates.append(h)

        # if none by validation, take all hypotheses
        if not candidates:
            candidates = insights.get("hypotheses", [])

        # If no hypotheses at all, return empty creatives
        if not candidates:
            return {"creatives": []}

        # Try LLM generation (if available)
        if self.llm:
            try:
                with open("prompts/creative_prompt.md", "r", encoding="utf-8") as f:
                    prompt = f.read()
                system = {"role": "system", "content": prompt}
                user = {"role": "user", "content": json.dumps(candidates, indent=2)}
                response = self.llm.chat([system, user])
                log_event("creative_llm_response", {"response": response})
                parsed = self._extract_json_block(response)
                if parsed.get("creatives"):
                    return parsed
                # else fallthrough to template fallback
            except Exception as e:
                log_event("creative_llm_error", {"error": str(e)})

        # Fallback: deterministic templates
        final_creatives = []
        for h in candidates:
            tpl = self._template_creatives_for_hypothesis(h)
            final_creatives.extend(tpl.get("creatives", []))

        log_event("creative_fallback_generated", {"count": len(final_creatives)})
        return {"creatives": final_creatives}
