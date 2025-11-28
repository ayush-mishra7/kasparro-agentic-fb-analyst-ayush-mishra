import pandas as pd
from src.agents.evaluator_agent import EvaluatorAgent

def test_evaluator_handles_empty_segment():
    df = pd.DataFrame({
        "campaign_name": ["A"],
        "impressions": [1000],
        "clicks": [50],
        "spend": [100],
        "revenue": [300],
        "purchases": [10],
        "roas": [3.0],
        "ctr": [0.05]
    })

    insights = {
        "hypotheses": [
            {
                "id": "hyp_1",
                "title": "Test",
                "summary": "Test",
                "segment_filter": {"campaign_name": "NON_EXISTENT"}
            }
        ]
    }

    evaluator = EvaluatorAgent()
    evaluated = evaluator.evaluate(df, insights)
    assert len(evaluated["hypotheses"]) == 1
    assert evaluated["hypotheses"][0]["validation"]["sample_size"] == 0