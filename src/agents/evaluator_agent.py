import pandas as pd
from typing import Dict, Any
from src.utils.logging_utils import log_event
from src.utils.data_utils import load_config
from difflib import get_close_matches


class EvaluatorAgent:
    """
    Evaluator Agent
    Validates each hypothesis against the raw DataFrame
    """

    def __init__(self):
        self.cfg = load_config()

        # thresholds
        self.low_ctr_threshold = float(
            self.cfg.get("analysis", {}).get("low_ctr_threshold", 0.01)
        )
        self.min_impressions_threshold = int(
            self.cfg.get("analysis", {}).get("min_impressions", 100)
        )

    def _normalize(self, s: Any) -> str:
        if not isinstance(s, str):
            return ""
        return s.strip().lower().replace("_", "").replace("-", "").replace(" ", "")

    def _fuzzy_match(self, value, col_values):
        """
        Matches dirty labels like:
            ' OMEN  Cot ton   Classics '
        to any best-match campaign name.
        """
        if not isinstance(value, str):
            return None
        
        norm_value = self._normalize(value)
        norm_map = {self._normalize(v): v for v in col_values}

        matches = get_close_matches(norm_value, list(norm_map.keys()), n=1, cutoff=0.4)
        if matches:
            return norm_map[matches[0]]
        return None

    def _apply_segment_filter(self, df: pd.DataFrame, segment: Dict[str, Any]) -> pd.DataFrame:
        filtered = df.copy()

        for col, val in segment.items():
            if col not in filtered.columns:
                continue
            if val is None:
                continue

            # fuzzy match on string columns
            if isinstance(val, str):
                best = self._fuzzy_match(val, filtered[col].unique())
                if best:
                    filtered = filtered[filtered[col] == best]
            else:
                filtered = filtered[filtered[col] == val]

        return filtered

    def _compute_validation(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) == 0:
            return {
                "sample_size": 0,
                "total_impressions": 0,
                "mean_ctr": 0,
                "mean_roas": None,
                "confidence": 0.1,
                "comment": "No impressions in this segment."
            }

        impressions = df.get("impressions", pd.Series([0])).sum()
        clicks = df.get("clicks", pd.Series([0])).sum()
        spend = df.get("spend", pd.Series([0])).sum()
        revenue = df.get("revenue", pd.Series([0])).sum()

        ctr = clicks / impressions if impressions > 0 else 0
        roas = revenue / spend if spend > 0 else None

        return {
            "sample_size": len(df),
            "total_impressions": int(impressions),
            "mean_ctr": ctr,
            "mean_roas": roas,
            "confidence": 0.7 if impressions > self.min_impressions_threshold else 0.3,
            "comment": "Validated successfully."
        }

    def evaluate(self, df: pd.DataFrame, hypotheses: Dict[str, Any]):
        results = {"hypotheses": []}

        for hyp in hypotheses.get("hypotheses", []):
            seg = hyp.get("segment_filter", {})
            filtered = self._apply_segment_filter(df, seg)
            validation = self._compute_validation(filtered)

            hyp["validation"] = validation
            results["hypotheses"].append(hyp)

        log_event("evaluation_results", results)
        return results
