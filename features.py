"""
BO_AI_5M
features.py
"""

import pandas as pd


def build_features(data: pd.DataFrame):

    data = data.copy()

    data["MA5"] = data["Close"].rolling(5).mean()
    data["MA10"] = data["Close"].rolling(10).mean()
    data["MA20"] = data["Close"].rolling(20).mean()

    data["EMA20"] = (
        data["Close"]
        .ewm(span=20, adjust=False)
        .mean()
    )

    data["EMA50"] = (
        data["Close"]
        .ewm(span=50, adjust=False)
        .mean()
    )

    data["Return"] = data["Close"].pct_change()
    data["Return3"] = data["Close"].pct_change(3)
    data["Return5"] = data["Close"].pct_change(5)

    delta = data["Close"].diff()

    gain = (
        delta.clip(lower=0)
        .rolling(14)
        .mean()
    )

    loss = (
        (-delta.clip(upper=0))
        .rolling(14)
        .mean()
    )

    rs = gain / loss

    data["RSI"] = (
        100 - (100 / (1 + rs))
    )

    tr1 = data["High"] - data["Low"]
    tr2 = (
        data["High"]
        - data["Close"].shift()
    ).abs()

    tr3 = (
        data["Low"]
        - data["Close"].shift()
    ).abs()

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1,
    ).max(axis=1)

    data["ATR"] = tr.rolling(14).mean()

    data["Hour"] = data.index.hour
    data["DayOfWeek"] = data.index.dayofweek

    data["Target"] = (
        data["Close"].shift(-1)
        > data["Close"]
    ).astype(int)

    data = data.dropna()

    return data
