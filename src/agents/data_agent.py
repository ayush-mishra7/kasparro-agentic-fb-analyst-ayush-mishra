from typing import Dict, Any
from src.utils.data_utils import load_dataset, compute_basic_aggregates
from src.utils.logging_utils import log_event

class DataAgent:
    """
    Data Agent — loads and summarizes dataset.
    """

    def run(self) -> Dict[str, Any]:
        df = load_dataset()
        summary = compute_basic_aggregates(df)
        log_event("data_agent_summary_ready", {"keys": list(summary.keys())})
        return {"dataframe": df, "summary": summary}