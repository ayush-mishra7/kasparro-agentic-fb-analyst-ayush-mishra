import yaml
import pandas as pd
import time
from pathlib import Path
from utils.logging_utils import log_event, start_span, end_span
from typing import Dict

CFG_PATHS = [Path("config/config.yaml"), Path("config.yaml"), Path("src/config.yaml")]

def load_config() -> Dict:
    for p in CFG_PATHS:
        if p.exists():
            try:
                return yaml.safe_load(open(p, "r"))
            except Exception:
                continue
    return {"data": {"path": "data/synthetic_fb_ads_undergarments.csv"}, "logging": {"log_dir": "logs"}, "analysis": {"low_ctr_threshold": 0.01, "min_impressions": 1000, "roas_threshold": 1.0, "min_clicks": 10}, "creatives": {"top_n": 5, "llm_model": "gpt-4.1"}, "reporting": {"output_path": "reports/report.md"}}

def load_dataset(retries=3, delay=1.0):
    cfg = load_config()
    path = Path(cfg["data"]["path"])
    attempt = 0
    while attempt < retries:
        try:
            try:
                df = pd.read_csv(path)
            except pd.errors.EmptyDataError:
                log_event("data.load.success", {"rows": 0, "note": "empty_file"}, agent="DataUtils")
                return pd.DataFrame()
            df = df.copy()
            for col in df.columns:
                if df[col].dtype == "object":
                    df[col] = df[col].astype(str).str.strip()
            log_event("data.load.success", {"rows": len(df)}, agent="DataUtils")
            return df
        except FileNotFoundError as e:
            log_event("data.load.error", {"error": str(e), "attempt": attempt + 1}, agent="DataUtils")
            attempt += 1
            time.sleep(delay * attempt)
        except Exception as e:
            log_event("data.load.error", {"error": str(e), "attempt": attempt + 1}, agent="DataUtils")
            attempt += 1
            time.sleep(delay * attempt)
    log_event("data.load.failed", {"path": str(path)}, agent="DataUtils")
    raise FileNotFoundError(f"Could not load dataset after {retries} retries.")

def compute_basic_aggregates(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {"rows": 0}
    res = {"rows": len(df)}
    if "impressions" in df.columns:
        res["impressions_sum"] = int(df["impressions"].sum())
    if "clicks" in df.columns:
        res["clicks_sum"] = int(df["clicks"].sum())
    return res

def write_dead_letter(name: str, payload: dict):
    DL_DIR = Path("dead_letter")
    DL_DIR.mkdir(exist_ok=True)
    ts = pd.Timestamp.utcnow().strftime("%Y%m%dT%H%M%SZ")
    file = DL_DIR / f"{name}_{ts}.json"
    with open(file, "w", encoding="utf-8") as f:
        import json
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return str(file)
