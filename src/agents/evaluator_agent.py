import pandas as pd
from typing import Dict, Any
from src.utils.data_utils import load_config
from src.utils.logging_utils import start_span, end_span, log_event

class EvaluatorAgent:
    def __init__(self):
        cfg = load_config()
        self.low_ctr_threshold = float(cfg.get("analysis", {}).get("low_ctr_threshold", 0.01))
        self.min_impressions_threshold = int(cfg.get("analysis", {}).get("min_impressions", 1000))
        self.min_clicks_threshold = int(cfg.get("analysis", {}).get("min_clicks", 10))
        self.roas_threshold = float(cfg.get("analysis", {}).get("roas_threshold", 1.0))

    def _compute_validation(self, df: pd.DataFrame) -> Dict[str, Any]:
        impressions = int(df["impressions"].sum()) if "impressions" in df.columns else 0
        clicks = int(df["clicks"].sum()) if "clicks" in df.columns else 0
        spend = float(df["spend"].sum()) if "spend" in df.columns else 0.0
        revenue = float(df["revenue"].sum()) if "revenue" in df.columns else 0.0

        mean_ctr = (clicks / impressions) if impressions > 0 else 0.0
        mean_roas = (revenue / spend) if spend > 0 else None
        sample_size = len(df)

        confidence = 0.7
        if impressions < self.min_impressions_threshold:
            confidence = 0.1

        return {
            "sample_size": sample_size,
            "total_impressions": impressions,
            "total_clicks": clicks,
            "mean_ctr": mean_ctr,
            "mean_roas": mean_roas,
            "confidence": confidence,
        }

    def validate(self, df: pd.DataFrame, segment_filter: Dict[str, Any]) -> Dict[str, Any]:
        try:
            df_seg = df.copy()
            for col, val in (segment_filter or {}).items():
                if col not in df_seg.columns:
                    return {
                        "sample_size": 0,
                        "total_impressions": 0,
                        "total_clicks": 0,
                        "mean_ctr": 0.0,
                        "mean_roas": None,
                        "confidence": 0.1,
                    }
                df_seg = df_seg[df_seg[col] == val]
            return self._compute_validation(df_seg)
        except Exception as e:
            return {
                "sample_size": 0,
                "total_impressions": 0,
                "total_clicks": 0,
                "mean_ctr": 0.0,
                "mean_roas": None,
                "confidence": 0.1,
                "error": str(e),
            }

    def evaluate(self, df: pd.DataFrame, insights: Dict[str, Any], trace_id: str = None, parent_span_id: str = None) -> Dict[str, Any]:
        span = start_span("insights.evaluate", trace_id=trace_id, parent_span_id=parent_span_id, agent="EvaluatorAgent")
        try:
            results = []
            for h in insights.get("hypotheses", []):
                seg = h.get("segment_filter", {}) or {}
                validation = self.validate(df, seg)
                r = {
                    "id": h.get("id"),
                    "title": h.get("title"),
                    "summary": h.get("summary"),
                    "segment_filter": seg,
                    "validation": validation,
                }
                results.append(r)
            log_event("insights.evaluated", {"count": len(results)}, trace_id=span["trace_id"], span_id=span["span_id"], agent="EvaluatorAgent")
            return {"hypotheses": results}
        finally:
            end_span(span)
