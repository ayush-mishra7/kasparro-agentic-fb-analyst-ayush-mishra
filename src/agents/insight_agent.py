# src/agents/insight_agent.py
import json
from typing import Dict, Any
from src.utils.llm_client import LLMClient
from src.utils.logging_utils import log_event
from src.utils.data_utils import load_dataset  # used for fallback rule-based generation
import pandas as pd
import uuid

class InsightAgent:
    """
    Insight Agent:
    - Attempt LLM-driven insight generation first.
    - If LLM output is empty / unparsable / contains no hypotheses, fall back to a deterministic
      rule-based generator that uses the actual dataset to create testable hypotheses.
    """

    def __init__(self, llm: LLMClient = None):
        # llm can be None or misconfigured; allow fallback without it
        self.llm = llm

    def _clean_segments(self, hyp: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure segment_filter values are valid, else choose first available value
        seg = hyp.get("segment_filter", {})
        mapping = {
            "campaign_name": summary.get("campaign_names"),
            "creative_type": summary.get("creative_types"),
            "audience_type": summary.get("audience_types"),
            "platform": summary.get("platforms"),
            "country": summary.get("countries")
        }
        for key, allowed in mapping.items():
            if allowed:
                val = seg.get(key)
                if (val is None) or (val not in allowed):
                    seg[key] = allowed[0]
        hyp["segment_filter"] = seg
        return hyp

    def _rule_based_hypotheses(self, df: pd.DataFrame, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic generator:
        - finds campaign/creative_type/country with worst CTR and worst ROAS,
          and creates hypotheses (up to 4).
        """
        hyps = []

        if df.empty:
            return {"hypotheses": []}

        # prepare aggregated stats
        def safe_agg(group_key):
            agg = (
                df.groupby(group_key)
                  .agg(impressions=("impressions", "sum"),
                       clicks=("clicks", "sum"),
                       spend=("spend", "sum"),
                       revenue=("revenue", "sum"))
                  .reset_index()
            )
            if "impressions" in agg.columns and "clicks" in agg.columns:
                agg["ctr"] = agg["clicks"] / agg["impressions"].clip(lower=1)
            else:
                agg["ctr"] = 0.0
            agg["roas"] = agg.apply(lambda r: (r["revenue"] / r["spend"]) if r["spend"] > 0 else None, axis=1)
            return agg

        # 1) Worst CTR by campaign
        if "campaign_name" in df.columns:
            by_campaign = safe_agg("campaign_name")
            by_campaign = by_campaign.sort_values("ctr").reset_index(drop=True)
            if not by_campaign.empty:
                worst = by_campaign.iloc[0]
                hyps.append({
                    "id": f"hyp_campaign_low_ctr_{uuid.uuid4().hex[:6]}",
                    "title": "Low CTR in campaign",
                    "summary": f"Campaign '{worst['campaign_name']}' has the lowest CTR ({worst['ctr']:.4f}).",
                    "segment_filter": {"campaign_name": worst["campaign_name"]}
                })

        # 2) Worst ROAS by campaign
        if "campaign_name" in df.columns:
            by_campaign_roas = safe_agg("campaign_name")
            # drop None roas
            by_campaign_roas = by_campaign_roas.dropna(subset=["roas"])
            if not by_campaign_roas.empty:
                worst_roas = by_campaign_roas.sort_values("roas").iloc[0]
                hyps.append({
                    "id": f"hyp_campaign_low_roas_{uuid.uuid4().hex[:6]}",
                    "title": "Low ROAS in campaign",
                    "summary": f"Campaign '{worst_roas['campaign_name']}' has low ROAS ({worst_roas['roas']:.2f}).",
                    "segment_filter": {"campaign_name": worst_roas["campaign_name"]}
                })

        # 3) Worst CTR by creative_type
        if "creative_type" in df.columns:
            by_creative = safe_agg("creative_type")
            by_creative = by_creative.sort_values("ctr").reset_index(drop=True)
            if not by_creative.empty:
                worst_c = by_creative.iloc[0]
                hyps.append({
                    "id": f"hyp_creative_low_ctr_{uuid.uuid4().hex[:6]}",
                    "title": "Low CTR for creative type",
                    "summary": f"Creative type '{worst_c['creative_type']}' has low CTR ({worst_c['ctr']:.4f}).",
                    "segment_filter": {"creative_type": worst_c["creative_type"]}
                })

        # 4) Worst ROAS by country
        if "country" in df.columns:
            by_country = safe_agg("country")
            by_country = by_country.dropna(subset=["roas"])
            if not by_country.empty:
                worst_country = by_country.sort_values("roas").iloc[0]
                hyps.append({
                    "id": f"hyp_country_low_roas_{uuid.uuid4().hex[:6]}",
                    "title": "Low ROAS in country",
                    "summary": f"Country '{worst_country['country']}' has low ROAS ({worst_country['roas']:.2f}).",
                    "segment_filter": {"country": worst_country["country"]}
                })

        # truncate to 4 hypotheses max
        return {"hypotheses": hyps[:4]}

    def generate_insights(self, user_query: str, data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Try LLM first. If LLM returns no usable hypotheses (empty / unparsable),
        fall back to deterministic rule-based generation using the CSV.
        """
        # Attempt LLM only if available
        if self.llm:
            try:
                with open("prompts/insight_prompt.md", "r", encoding="utf-8") as f:
                    prompt = f.read()
                snippet = json.dumps(data_summary, indent=2)[:2500]
                system = {"role": "system", "content": prompt}
                user = {"role": "user", "content": f"Query:\n{user_query}\n\nSummary:\n{snippet}"}
                response = self.llm.chat([system, user])
                log_event("insight_raw", {"response": response})

                # parse robustly
                parsed = None
                try:
                    parsed = json.loads(response)
                except Exception:
                    # try to extract JSON substring
                    try:
                        start = response.index("{")
                        end = response.rindex("}") + 1
                        parsed = json.loads(response[start:end])
                    except Exception:
                        parsed = None

                if parsed and parsed.get("hypotheses"):
                    # Clean segment filters to be valid (if necessary)
                    cleaned = []
                    for h in parsed.get("hypotheses", []):
                        cleaned.append(self._clean_segments(h, data_summary))
                    return {"hypotheses": cleaned}
                # fall through to deterministic fallback if LLM produced nothing
            except Exception as e:
                log_event("insight_llm_error", {"error": str(e)})

        # Deterministic fallback using raw dataset
        try:
            df = load_dataset()
        except Exception as e:
            log_event("insight_fallback_failed", {"error": str(e)})
            return {"hypotheses": []}

        # Generate rule-based hypotheses
        hyps = self._rule_based_hypotheses(df, data_summary)

        # Evaluate and attach placeholder validation (Evaluator will later overwrite with real validation)
        for h in hyps.get("hypotheses", []):
            h["validation"] = {
                "sample_size": None,
                "mean_ctr": None,
                "mean_roas": None,
                "confidence": 0.2,
                "comment": "Generated by rule-based fallback; evaluator should validate."
            }

        log_event("insight_fallback_generated", {"count": len(hyps.get("hypotheses", []))})
        return hyps
