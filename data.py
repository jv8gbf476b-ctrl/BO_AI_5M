"""
BO_AI_5M
data.py
"""

import yfinance as yf

from config import SYMBOL
from config import INTERVAL
from config import PERIOD


def load_data():

    df = yf.download(
        SYMBOL,
        interval=INTERVAL,
        period=PERIOD,
        auto_adjust=True,
        progress=False,
    )

    if df.empty:
        raise Exception("データ取得失敗")

    df = df.rename(
        columns={
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "Volume": "Volume",
        }
    )

    return df
