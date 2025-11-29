from src.agents.evaluator_agent import EvaluatorAgent
import pandas as pd


def test_evaluator_missing_columns():
    """Evaluator should gracefully handle missing segmentation columns."""
    df = pd.DataFrame({"foo": [1, 2, 3]})

    agent = EvaluatorAgent()
    insights = {
        "hypotheses": [
            {"id": "h1", "segment_filter": {"campaign_name": "nonexistent"}}
        ]
    }

    out = agent.evaluate(df, insights)
    v = out["hypotheses"][0]["validation"]

    assert v["sample_size"] == 0
    assert v["total_impressions"] == 0
    assert v["mean_ctr"] == 0
    assert v["mean_roas"] is None


def test_evaluator_extreme_values():
    """Test extreme values like huge impressions and zero spend."""

    df = pd.DataFrame({
        "campaign_name": ["A", "A"],
        "creative_type": ["X", "X"],
        "audience_type": ["Y", "Y"],
        "platform": ["FB", "FB"],
        "country": ["IN", "IN"],
        "impressions": [1_000_000, 2_000_000],
        "clicks": [0, 0],
        "spend": [0, 0],            # zero spend → ROAS = None
        "revenue": [0, 0],
    })

    agent = EvaluatorAgent()
    insights = {"hypotheses": [{"id": "h1", "segment_filter": {"campaign_name": "A"}}]}

    out = agent.evaluate(df, insights)
    v = out["hypotheses"][0]["validation"]

    assert v["mean_ctr"] == 0
    assert v["mean_roas"] is None
    assert v["total_impressions"] == 3_000_000
