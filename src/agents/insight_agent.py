# src/agents/insight_agent.py
import json
import uuid
from typing import Dict, Any
from difflib import get_close_matches

from src.utils.logging_utils import log_event
from src.utils.data_utils import load_dataset


class InsightAgent:
    """
    LLM-first Insight Agent with robust deterministic fallback and
    fuzzy-correction of segment_filter values to dataset reality.
    """

    def __init__(self, llm=None):
        # llm can be None (we'll still run fallback)
        self.llm = llm

    def _normalize(self, s):
        if not isinstance(s, str):
            return ""
        return s.strip().lower().replace("_", "").replace("-", "").replace(" ", "")

    def _fix_segment_values(self, segment_filter: Dict[str, Any], data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map segment_filter values to the closest allowed value from data_summary.
        If incoming value is missing or not close, pick the first allowed value.
        """
        corrected = {}
        mapping = {
            "campaign_name": "campaign_names",
            "creative_type": "creative_types",
            "audience_type": "audience_types",
            "platform": "platforms",
            "country": "countries",
        }

        for key, list_key in mapping.items():
            allowed = data_summary.get(list_key, []) or []
            incoming = segment_filter.get(key) if segment_filter else None

            if isinstance(incoming, str) and allowed:
                # attempt exact-case-insensitive match first
                lower_map = {a.lower(): a for a in allowed}
                if incoming.lower() in lower_map:
                    corrected[key] = lower_map[incoming.lower()]
                    continue

                # fuzzy match on normalized strings
                norm_allowed = {self._normalize(a): a for a in allowed}
                norm_in = self._normalize(incoming)
                best = get_close_matches(norm_in, list(norm_allowed.keys()), n=1, cutoff=0.35)
                if best:
                    corrected[key] = norm_allowed[best[0]]
                else:
                    # fallback to first allowed value
                    corrected[key] = allowed[0]
            else:
                # If no incoming value, choose first allowed or None
                corrected[key] = (allowed[0] if allowed else None)

        return corrected

    def _rule_based_hypotheses(self, df, data_summary) -> Dict[str, Any]:
        """
        Deterministic fallback: derive up to 4 sensible hypotheses using dataset aggregates.
        Uses actual dataset values (no invented segments).
        """
        hyps = []
        if df is None or df.empty:
            return {"hypotheses": []}

        def agg_on(col):
            g = df.groupby(col).agg(
                impressions=("impressions", "sum"),
                clicks=("clicks", "sum"),
                spend=("spend", "sum"),
                revenue=("revenue", "sum"),
            ).reset_index()
            if "impressions" in g.columns and "clicks" in g.columns:
                g["ctr"] = g["clicks"] / g["impressions"].clip(lower=1)
            else:
                g["ctr"] = 0.0
            g["roas"] = g.apply(lambda r: (r["revenue"] / r["spend"]) if r["spend"] > 0 else None, axis=1)
            return g

        # candidate: campaign with lowest ctr
        if "campaign_name" in df.columns:
            try:
                c = agg_on("campaign_name").sort_values("ctr", ascending=True)
                if not c.empty:
                    row = c.iloc[0]
                    hyps.append({
                        "id": f"hyp_campaign_low_ctr_{uuid.uuid4().hex[:6]}",
                        "title": f"Low CTR: {row['campaign_name']}",
                        "summary": f"Campaign '{row['campaign_name']}' shows low CTR ({row['ctr']:.4f}).",
                        "segment_filter": {"campaign_name": str(row["campaign_name"])}
                    })
            except Exception:
                pass

            # campaign with lowest roas
            try:
                c2 = agg_on("campaign_name").dropna(subset=["roas"]).sort_values("roas", ascending=True)
                if not c2.empty:
                    row = c2.iloc[0]
                    hyps.append({
                        "id": f"hyp_campaign_low_roas_{uuid.uuid4().hex[:6]}",
                        "title": f"Low ROAS: {row['campaign_name']}",
                        "summary": f"Campaign '{row['campaign_name']}' has low ROAS ({row['roas']:.2f}).",
                        "segment_filter": {"campaign_name": str(row["campaign_name"])}
                    })
            except Exception:
                pass

        # creative_type with lowest ctr
        if "creative_type" in df.columns:
            try:
                cr = agg_on("creative_type").sort_values("ctr", ascending=True)
                if not cr.empty:
                    row = cr.iloc[0]
                    hyps.append({
                        "id": f"hyp_creative_low_ctr_{uuid.uuid4().hex[:6]}",
                        "title": f"Low CTR for creative: {row['creative_type']}",
                        "summary": f"Creative type '{row['creative_type']}' shows low CTR ({row['ctr']:.4f}).",
                        "segment_filter": {"creative_type": str(row["creative_type"])}
                    })
            except Exception:
                pass

        # country with lowest roas
        if "country" in df.columns:
            try:
                ct = agg_on("country").dropna(subset=["roas"]).sort_values("roas", ascending=True)
                if not ct.empty:
                    row = ct.iloc[0]
                    hyps.append({
                        "id": f"hyp_country_low_roas_{uuid.uuid4().hex[:6]}",
                        "title": f"Low ROAS in country: {row['country']}",
                        "summary": f"Country '{row['country']}' shows low ROAS ({row['roas']:.2f}).",
                        "segment_filter": {"country": str(row["country"])}
                    })
            except Exception:
                pass

        # return up to 4
        return {"hypotheses": hyps[:4]}

    def generate_insights(self, user_query: str, data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Try LLM first. If no usable hypotheses, fallback to deterministic rule-based generation.
        Then ensure segment_filter values are corrected to match data_summary (fuzzy-correct).
        """
        # 1) LLM attempt (safe)
        if self.llm:
            try:
                with open("prompts/insight_prompt.md", "r", encoding="utf-8") as f:
                    prompt = f.read()
                snippet = json.dumps(data_summary, indent=2)[:2500]
                system = {"role": "system", "content": prompt}
                user = {"role": "user", "content": f"Query:\n{user_query}\n\nSummary:\n{snippet}"}
                resp = self.llm.chat([system, user])
                log_event("insight_raw", {"response": resp})

                parsed = None
                try:
                    parsed = json.loads(resp)
                except Exception:
                    try:
                        s = resp.index("{")
                        e = resp.rindex("}") + 1
                        parsed = json.loads(resp[s:e])
                    except Exception:
                        parsed = None

                if parsed and parsed.get("hypotheses"):
                    # Correct segment values and return
                    cleaned = []
                    for h in parsed.get("hypotheses", []):
                        seg = h.get("segment_filter", {}) or {}
                        fixed = self._fix_segment_values(seg, data_summary)
                        h["segment_filter"] = fixed
                        cleaned.append(h)
                    return {"hypotheses": cleaned}
                # else fall through to fallback
            except Exception as e:
                log_event("insight_llm_error", {"error": str(e)})

        # 2) Deterministic fallback (guaranteed)
        try:
            df = load_dataset()
        except Exception as e:
            log_event("insight_fallback_load_error", {"error": str(e)})
            return {"hypotheses": []}

        hyps = self._rule_based_hypotheses(df, data_summary)

        # Ensure the segment filters are corrected to match dataset values
        corrected = []
        for h in hyps.get("hypotheses", []):
            seg = h.get("segment_filter", {}) or {}
            fixed = self._fix_segment_values(seg, data_summary)
            h["segment_filter"] = fixed
            # placeholder validation; evaluator will compute real validation later
            h["validation"] = {
                "sample_size": None,
                "mean_ctr": None,
                "mean_roas": None,
                "confidence": 0.2,
                "comment": "Fallback hypothesis; evaluator will validate."
            }
            corrected.append(h)

        log_event("insight_fallback_generated", {"count": len(corrected)})
        return {"hypotheses": corrected}
