from typing import Dict, Any
from utils.data_utils import load_dataset, compute_basic_aggregates
from utils.logging_utils import log_event

class DataAgent:
    def run(self) -> Dict[str, Any]:
        df = load_dataset()
        summary = compute_basic_aggregates(df)
        log_event("data_agent_summary_ready", {"keys": list(summary.keys())})
        return {"dataframe": df, "summary": summary}
