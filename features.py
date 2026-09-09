"""
BO_AI_5M
features.py

ZERO v0.3
日本時間統一版
"""

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "MA5",
    "MA10",
    "MA20",
    "EMA20",
    "EMA50",
    "Return",
    "Return3",
    "Return5",
    "RSI",
    "ATR",
    "Hour",
    "DayOfWeek",
]


def build_features(data: pd.DataFrame):

    data = data.copy()

    # =========================
    # 時刻を日本時間に統一
    # =========================

    if data.index.tz is None:

        data.index = (
            data.index
            .tz_localize("UTC")
        )

    jst_index = (
        data.index
        .tz_convert(
            "Asia/Tokyo"
        )
    )

    # =========================
    # 移動平均
    # =========================

    data["MA5"] = (
        data["Close"]
        .rolling(5)
        .mean()
    )

    data["MA10"] = (
        data["Close"]
        .rolling(10)
        .mean()
    )

    data["MA20"] = (
        data["Close"]
        .rolling(20)
        .mean()
    )

    data["EMA20"] = (
        data["Close"]
        .ewm(
            span=20,
            adjust=False,
        )
        .mean()
    )

    data["EMA50"] = (
        data["Close"]
        .ewm(
            span=50,
            adjust=False,
        )
        .mean()
    )

    # =========================
    # 値動き
    # =========================

    data["Return"] = (
        data["Close"]
        .pct_change()
    )

    data["Return3"] = (
        data["Close"]
        .pct_change(3)
    )

    data["Return5"] = (
        data["Close"]
        .pct_change(5)
    )

    # =========================
    # RSI
    # =========================

    delta = (
        data["Close"]
        .diff()
    )

    gain = (
        delta
        .clip(lower=0)
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
        100
        - (
            100
            / (1 + rs)
        )
    )

    # =========================
    # ATR
    # =========================

    tr1 = (
        data["High"]
        - data["Low"]
    )

    tr2 = (
        data["High"]
        - data["Close"].shift(1)
    ).abs()

    tr3 = (
        data["Low"]
        - data["Close"].shift(1)
    ).abs()

    tr = pd.concat(
        [
            tr1,
            tr2,
            tr3,
        ],
        axis=1,
    ).max(axis=1)

    data["ATR"] = (
        tr
        .rolling(14)
        .mean()
    )

    # =========================
    # 日本時間
    # =========================

    data["Hour"] = (
        jst_index.hour
    )

    data["DayOfWeek"] = (
        jst_index.dayofweek
    )

    # =========================
    # 5分後の正解
    # =========================

    next_close = (
        data["Close"]
        .shift(-1)
    )

    data["Target"] = np.where(
        next_close.isna(),
        np.nan,
        np.where(
            next_close
            > data["Close"],
            1.0,
            np.where(
                next_close
                < data["Close"],
                0.0,
                np.nan,
            ),
        ),
    )

    # =========================
    # 特徴量不足だけ削除
    # =========================

    data = (
        data
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .dropna(
            subset=FEATURE_COLUMNS
        )
    )

    return data
