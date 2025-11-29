import pandas as pd
from utils.data_utils import load_config
from utils.logging_utils import start_span, end_span, log_event, make_trace_id

class EvaluatorAgent:
    def __init__(self):
        cfg = load_config()
        self.low_ctr_threshold = float(cfg.get("analysis", {}).get("low_ctr_threshold", 0.01))
        self.min_impressions_threshold = int(cfg.get("analysis", {}).get("min_impressions", 1000))
        self.min_clicks_threshold = int(cfg.get("analysis", {}).get("min_clicks", 10))
        self.roas_threshold = float(cfg.get("analysis", {}).get("roas_threshold", 1.0))

    def _compute_validation(self, df: pd.DataFrame) -> dict:
        impressions = int(df["impressions"].sum()) if "impressions" in df.columns and not df.empty else 0
        clicks = int(df["clicks"].sum()) if "clicks" in df.columns and not df.empty else 0
        spend = float(df["spend"].sum()) if "spend" in df.columns and not df.empty else 0.0
        revenue = float(df["revenue"].sum()) if "revenue" in df.columns and not df.empty else 0.0
        ctr = float(clicks / impressions) if impressions > 0 else 0.0
        roas = float(revenue / spend) if spend > 0 else None
        status = "good"
        if impressions < self.min_impressions_threshold:
            status = "insufficient_impressions"
        elif clicks < self.min_clicks_threshold:
            status = "low_clicks"
        elif ctr < self.low_ctr_threshold:
            status = "low_ctr"
        elif roas is not None and roas < self.roas_threshold:
            status = "low_roas"
        return {"sample_size": int(len(df)) if df is not None else 0, "impressions": impressions, "clicks": clicks, "ctr": ctr, "roas": roas, "status": status}

    def validate(self, df: pd.DataFrame, segment_filter: dict) -> dict:
        try:
            df_seg = df.copy() if df is not None else pd.DataFrame()
            for col, val in (segment_filter or {}).items():
                if col not in df_seg.columns:
                    return {"sample_size": 0, "impressions": 0, "clicks": 0, "ctr": 0.0, "mean_roas": None, "confidence": 0.1, "comment": "segment_not_found"}
                df_seg = df_seg[df_seg[col] == val]
            computed = self._compute_validation(df_seg)
            return {"sample_size": int(len(df_seg)), "total_impressions": int(computed["impressions"]), "mean_ctr": float(computed["ctr"]), "mean_roas": computed["roas"], "confidence": 0.7 if computed["status"] == "good" else 0.5, "comment": "Validated successfully."}
        except Exception as e:
            return {"sample_size": 0, "total_impressions": 0, "mean_ctr": 0.0, "mean_roas": None, "confidence": 0.1, "comment": f"error:{str(e)}"}

    def evaluate(self, df: pd.DataFrame, insights: dict, trace_id=None, parent_span=None) -> dict:
        trace_id = trace_id or make_trace_id()
        span = start_span("insights.evaluate", trace_id=trace_id, parent_span_id=parent_span, agent="EvaluatorAgent")
        results = []
        for h in insights.get("hypotheses", []):
            seg = h.get("segment_filter", {})
            validation = self.validate(df, seg)
            out = {"id": h.get("id"), "title": h.get("title"), "summary": h.get("summary"), "segment_filter": seg, "validation": validation}
            results.append(out)
        end_span(span)
        return {"hypotheses": results}
