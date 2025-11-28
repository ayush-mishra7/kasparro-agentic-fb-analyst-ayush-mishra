import pandas as pd
import yaml
from src.utils.logging_utils import log_event


def load_config(path="config/config.yaml"):
    return yaml.safe_load(open(path, "r"))


def load_dataset():
    cfg = load_config()
    df = pd.read_csv(cfg["data"]["path"])
    log_event("data_loaded", {"rows": len(df)})
    return df


def compute_basic_aggregates(df):
    """
    Produces a compact but explicit summary including ALL real segment values.
    This ensures the LLM can only choose valid segment filters.
    """

    summary = {}

    # Numeric summary
    summary["numeric_summary"] = df[[
        "spend", "impressions", "clicks", "purchases",
        "revenue", "ctr", "roas"
    ]].describe().to_dict()

    # Segment values (IMPORTANT: explicit list for LLM)
    summary["campaign_names"] = sorted(df["campaign_name"].dropna().unique().tolist())

    if "creative_type" in df.columns:
        summary["creative_types"] = sorted(df["creative_type"].dropna().unique().tolist())

    if "audience_type" in df.columns:
        summary["audience_types"] = sorted(df["audience_type"].dropna().unique().tolist())

    if "platform" in df.columns:
        summary["platforms"] = sorted(df["platform"].dropna().unique().tolist())

    if "country" in df.columns:
        summary["countries"] = sorted(df["country"].dropna().unique().tolist())

    log_event("summary_ready", {
        "campaign_names": summary.get("campaign_names"),
        "creative_types": summary.get("creative_types"),
        "audience_types": summary.get("audience_types"),
        "platforms": summary.get("platforms"),
        "countries": summary.get("countries"),
    })

    return summary
