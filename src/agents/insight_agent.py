import uuid
import numpy as np
import pandas as pd
from typing import Dict, Any
from src.utils.logging_utils import start_span, end_span, log_event
from src.utils.data_utils import load_config

class InsightAgent:
    def __init__(self):
        cfg = load_config()
        self.low_ctr_threshold = float(cfg.get("analysis", {}).get("low_ctr_threshold", 0.01))
        self.min_impressions_threshold = int(cfg.get("analysis", {}).get("min_impressions", 1000))

    def _safe_mean(self, series):
        try:
            return float(np.nanmean(series))
        except Exception:
            return None

    def generate_insights(self, df: pd.DataFrame, trace_id: str = None, parent_span_id: str = None) -> Dict[str, Any]:
        span = start_span("insight.generate", trace_id=trace_id, parent_span_id=parent_span_id, agent="InsightAgent")
        try:
            hypotheses = []
            if df is None or not isinstance(df, pd.DataFrame):
                log_event("insight.error", {"error": "invalid_input"}, trace_id=span["trace_id"], span_id=span["span_id"], agent="InsightAgent")
                return {"hypotheses": []}

            if "campaign_name" in df.columns and "ctr" in df.columns:
                grouped = df.groupby("campaign_name")["ctr"].mean()
                if not grouped.empty:
                    worst_campaign = grouped.idxmin()
                    worst_value = float(grouped.min())
                    if worst_value < self.low_ctr_threshold:
                        hypotheses.append({
                            "id": f"hyp_campaign_low_ctr_{uuid.uuid4().hex[:6]}",
                            "title": "Low CTR in campaign",
                            "summary": f"Campaign '{worst_campaign}' has the lowest CTR ({worst_value:.4f}).",
                            "segment_filter": {"campaign_name": worst_campaign},
                            "validation": {}
                        })

            if "campaign_name" in df.columns and "roas" in df.columns:
                grouped = df.groupby("campaign_name")["roas"].mean()
                if not grouped.empty:
                    worst_campaign = grouped.idxmin()
                    worst_value = float(grouped.min())
                    median_roas = self._safe_mean(df["roas"])
                    if median_roas is not None and worst_value < median_roas:
                        hypotheses.append({
                            "id": f"hyp_campaign_low_roas_{uuid.uuid4().hex[:6]}",
                            "title": "Low ROAS in campaign",
                            "summary": f"Campaign '{worst_campaign}' has low ROAS ({worst_value:.2f}).",
                            "segment_filter": {"campaign_name": worst_campaign},
                            "validation": {}
                        })

            if "creative_type" in df.columns and "ctr" in df.columns:
                grouped = df.groupby("creative_type")["ctr"].mean()
                if not grouped.empty:
                    worst_creative = grouped.idxmin()
                    worst_value = float(grouped.min())
                    if worst_value < self.low_ctr_threshold:
                        hypotheses.append({
                            "id": f"hyp_creative_low_ctr_{uuid.uuid4().hex[:6]}",
                            "title": "Low CTR for creative type",
                            "summary": f"Creative type '{worst_creative}' has low CTR ({worst_value:.4f}).",
                            "segment_filter": {"creative_type": worst_creative},
                            "validation": {}
                        })

            if "country" in df.columns and "roas" in df.columns:
                grouped = df.groupby("country")["roas"].mean()
                if not grouped.empty:
                    worst_country = grouped.idxmin()
                    worst_value = float(grouped.min())
                    hypotheses.append({
                        "id": f"hyp_country_low_roas_{uuid.uuid4().hex[:6]}",
                        "title": "Low ROAS in country",
                        "summary": f"Country '{worst_country}' has low ROAS ({worst_value:.2f}).",
                        "segment_filter": {"country": worst_country},
                        "validation": {}
                    })

            log_event("insight.generated", {"count": len(hypotheses)}, trace_id=span["trace_id"], span_id=span["span_id"], agent="InsightAgent")
            return {"hypotheses": hypotheses}
        except Exception as e:
            log_event("insight.error", {"error": str(e)}, trace_id=span["trace_id"], span_id=span["span_id"], agent="InsightAgent")
            raise
        finally:
            end_span(span)

    def generate(self, df: pd.DataFrame, trace_id: str = None, parent_span_id: str = None) -> Dict[str, Any]:
        return self.generate_insights(df, trace_id=trace_id, parent_span_id=parent_span_id)
