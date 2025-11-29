import uuid
import numpy as np
import pandas as pd
from utils.logging_utils import start_span, end_span, log_event, make_trace_id
from utils.data_utils import load_config

class InsightAgent:
    def __init__(self, llm=None):
        cfg = load_config()
        self.low_ctr_threshold = float(cfg.get("analysis", {}).get("low_ctr_threshold", 0.01))
        self.min_impressions_threshold = int(cfg.get("analysis", {}).get("min_impressions", 1000))
        self.llm = llm

    def generate_insights(self, df: pd.DataFrame, *, trace_id=None, parent_span=None):
        trace_id = trace_id or make_trace_id()
        span = start_span("insight.generate", trace_id=trace_id, parent_span_id=parent_span, agent="InsightAgent")
        try:
            hypotheses = []
            if df is None or df.empty:
                log_event("insight.generated", {"count": 0}, trace_id=trace_id, parent_span_id=span["span_id"], agent="InsightAgent")
                end_span(span)
                return {"hypotheses": []}
            if "campaign_name" in df.columns and "ctr" in df.columns:
                low_ctr = df.groupby("campaign_name")["ctr"].mean()
                worst_campaign = low_ctr.idxmin()
                worst_value = float(low_ctr.min())
                if worst_value < self.low_ctr_threshold:
                    hypotheses.append({
                        "id": f"hyp_campaign_low_ctr_{uuid.uuid4().hex[:6]}",
                        "title": "Low CTR in campaign",
                        "summary": f"Campaign '{worst_campaign}' has the lowest CTR ({worst_value:.4f}).",
                        "segment_filter": {"campaign_name": worst_campaign},
                        "validation": {}
                    })
            if "campaign_name" in df.columns and "roas" in df.columns:
                low_roas = df.groupby("campaign_name")["roas"].mean()
                worst_campaign = low_roas.idxmin()
                worst_value = float(low_roas.min())
                if not np.isnan(worst_value) and worst_value < float(np.nanmedian(df["roas"])):
                    hypotheses.append({
                        "id": f"hyp_campaign_low_roas_{uuid.uuid4().hex[:6]}",
                        "title": "Low ROAS in campaign",
                        "summary": f"Campaign '{worst_campaign}' has low ROAS ({worst_value:.2f}).",
                        "segment_filter": {"campaign_name": worst_campaign},
                        "validation": {}
                    })
            if "creative_type" in df.columns and "ctr" in df.columns:
                low_ctr = df.groupby("creative_type")["ctr"].mean()
                worst_creative = low_ctr.idxmin()
                worst_value = float(low_ctr.min())
                if worst_value < self.low_ctr_threshold:
                    hypotheses.append({
                        "id": f"hyp_creative_low_ctr_{uuid.uuid4().hex[:6]}",
                        "title": "Low CTR for creative type",
                        "summary": f"Creative type '{worst_creative}' has low CTR ({worst_value:.4f}).",
                        "segment_filter": {"creative_type": worst_creative},
                        "validation": {}
                    })
            if "country" in df.columns and "roas" in df.columns:
                low_roas = df.groupby("country")["roas"].mean()
                worst_country = low_roas.idxmin()
                worst_value = float(low_roas.min())
                hypotheses.append({
                    "id": f"hyp_country_low_roas_{uuid.uuid4().hex[:6]}",
                    "title": "Low ROAS in country",
                    "summary": f"Country '{worst_country}' has low ROAS ({worst_value:.2f}).",
                    "segment_filter": {"country": worst_country},
                    "validation": {}
                })
            log_event("insight.generated", {"count": len(hypotheses)}, trace_id=trace_id, parent_span_id=span["span_id"], agent="InsightAgent")
            end_span(span)
            return {"hypotheses": hypotheses}
        except Exception as e:
            log_event("insight.error", {"error": str(e)}, trace_id=trace_id, parent_span_id=span["span_id"], agent="InsightAgent")
            end_span(span)
            raise
