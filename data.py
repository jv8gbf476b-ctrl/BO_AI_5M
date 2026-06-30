"""
BO_AI_5M
data.py
"""

import yfinance as yf
import pandas as pd


TICKER = "JPY=X"


def load_data():

    data = yf.download(
        TICKER,
        period="60d",
        interval="5m",
        auto_adjust=False,
        progress=False,
    )

    if data.empty:
        raise RuntimeError(
            "データ取得失敗"
        )

    if isinstance(
        data.columns,
        pd.MultiIndex,
    ):
        data.columns = (
            data.columns.get_level_values(0)
        )

    data = data[
        [
            "Open",
            "High",
            "Low",
            "Close",
        ]
    ].dropna()

    return data
