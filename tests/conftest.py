import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    """A standard clean dataframe for testing evaluator logic."""
    return pd.DataFrame({
        "campaign_name": ["A", "A", "B"],
        "creative_type": ["Video", "Image", "Video"],
        "audience_type": ["Broad", "Retargeting", "Broad"],
        "platform": ["Facebook", "Instagram", "Facebook"],
        "country": ["IN", "IN", "US"],
        "impressions": [1000, 2000, 500],
        "clicks": [10, 40, 2],
        "spend": [100, 150, 50],
        "revenue": [400, 600, 70],
    })
