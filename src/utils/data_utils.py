import time
from pathlib import Path
import yaml
import pandas as pd
from pandas.errors import EmptyDataError
from src.utils.logging_utils import log_event, start_span, end_span

DEFAULT_CONFIG_PATHS = [
    Path("config/config.yaml"),
    Path("src/config.yaml"),
    Path("config.yaml"),
]

def load_config():
    for p in DEFAULT_CONFIG_PATHS:
        if p.exists():
            cfg = yaml.safe_load(p.read_text())
            return cfg or {}
    return {}

def load_dataset(retries: int = 3, delay: float = 1.0) -> pd.DataFrame:
    cfg = load_config()
    data_path = cfg.get("data", {}).get("path", "data/synthetic_fb_ads_undergarments.csv")
    path = Path(data_path)

    attempt = 0
    while attempt < retries:
        try:
            try:
                df = pd.read_csv(path)
            except EmptyDataError:
                log_event("data.load.success", {"rows": 0, "note": "empty_file"}, agent="DataUtils")
                return pd.DataFrame()

            # basic cleanup: strip whitespace from object columns
            for col in df.columns:
                if df[col].dtype == "object":
                    df[col] = df[col].astype(str).str.strip()
            log_event("data.load.success", {"rows": len(df)}, agent="DataUtils")
            return df
        except Exception as e:
            log_event("data.load.error", {"attempt": attempt + 1, "error": str(e)}, agent="DataUtils")
            attempt += 1
            time.sleep(delay * attempt)
    log_event("data.load.failed", {"path": str(path)}, agent="DataUtils")
    raise FileNotFoundError(f"Could not load dataset after {retries} retries.")

def compute_basic_aggregates(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}
    res = {}
    try:
        impressions = int(df["impressions"].sum()) if "impressions" in df.columns else 0
        clicks = int(df["clicks"].sum()) if "clicks" in df.columns else 0
        spend = float(df["spend"].sum()) if "spend" in df.columns else 0.0
        revenue = float(df["revenue"].sum()) if "revenue" in df.columns else 0.0
        ctr = clicks / impressions if impressions > 0 else 0.0
        roas = revenue / spend if spend > 0 else None
        res = {
            "rows": len(df),
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "revenue": revenue,
            "ctr": ctr,
            "roas": roas,
        }
    except Exception as e:
        log_event("data.aggregate.error", {"error": str(e)}, agent="DataUtils")
    return res
