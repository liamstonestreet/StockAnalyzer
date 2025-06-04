# options.py
import pandas as pd
from datetime import datetime, timedelta

def get_mock_options_chain():
    """Returns a simulated options chain for covered calls."""
    today = datetime.today()
    data = [
        {"strike": 105, "expiration": today + timedelta(days=7), "premium": 1.20, "delta": 0.3},
        {"strike": 107, "expiration": today + timedelta(days=7), "premium": 0.85, "delta": 0.25},
        {"strike": 110, "expiration": today + timedelta(days=7), "premium": 0.45, "delta": 0.1},
        {"strike": 112, "expiration": today + timedelta(days=14), "premium": 0.30, "delta": 0.08},
        {"strike": 115, "expiration": today + timedelta(days=21), "premium": 0.20, "delta": 0.05},
    ]
    df = pd.DataFrame(data)
    df["expiration"] = pd.to_datetime(df["expiration"])
    df["days_to_expiration"] = (df["expiration"] - pd.Timestamp.now()).dt.days
    return df

def filter_conservative_calls(df, min_premium=0.5, max_delta=0.25, max_days=14):
    """Filters for conservative covered calls."""
    return df[
        (df["premium"] >= min_premium) &
        (df["delta"] <= max_delta) &
        (df["days_to_expiration"] <= max_days)
    ].sort_values(by="delta")
