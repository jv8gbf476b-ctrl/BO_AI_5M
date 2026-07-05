"""
Market Assistant
improver.py
自己改善エンジン
"""

from history import load_history
from model import train_fresh_model
from model import predict_with_model
from model_store import (
    load_current_model,
    save_candidate_model,
    promote_candidate_model,
)

MILESTONES = [
    300,
    600,
    1000,
    1500,
    2000,
]


def calc_model_win_rate(model, data):

    total = 0
    wins = 0

    for i in range(len(data) - 1):

        row = data.iloc[[i]]
        next_close = float(data.iloc[i + 1]["Close"])
        now_close = float(data.iloc[i]["Close"])

        up_prob, down_prob = predict_with_model(
            model,
            row,
        )

        if up_prob >= down_prob:
            signal = "HIGH"
        else:
            signal = "LOW"

        if next_close > now_close:
            actual = "HIGH"
        elif next_close < now_close:
            actual = "LOW"
        else:
            actual = "FLAT"

        total += 1

        if signal == actual:
            wins += 1

    if total == 0:
        return 0.0

    return wins / total * 100


def should_improve():

    df = load_history()

    if df.empty:
        return False

    trade_df = df[
        df["result"] != "NO_TRADE"
    ]

    trade_count = len(trade_df)

    return trade_count in MILESTONES


def improve_model(data):

    if not should_improve():
        return False

    current_model = load_current_model()

    if current_model is None:
        return False

    candidate_model = train_fresh_model(
        data
    )

    current_rate = calc_model_win_rate(
        current_model,
        data,
    )

    candidate_rate = calc_model_win_rate(
        candidate_model,
        data,
    )

    if candidate_rate <= current_rate:
        return False

    save_candidate_model(
        candidate_model
    )

    promote_candidate_model()

    return True
