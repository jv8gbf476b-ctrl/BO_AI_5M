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

        now_close = float(
            data.iloc[i]["Close"]
        )

        next_close = float(
            data.iloc[i + 1]["Close"]
        )

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
        print("improver: history empty")
        return False

    # WIN・LOSE・SKIPを含む全判定を数える
    history_count = len(df)

    print(
        "improver history count:",
        history_count,
    )

    if history_count in MILESTONES:
        print(
            "improver milestone reached:",
            history_count,
        )
        return True

    return False


def improve_model(data):

    if not should_improve():
        return False

    current_model = load_current_model()

    if current_model is None:
        print("improver: current model not found")
        return False

    print("improver: training candidate model")

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

    print(
        "current model rate:",
        round(current_rate, 2),
    )

    print(
        "candidate model rate:",
        round(candidate_rate, 2),
    )

    if candidate_rate <= current_rate:
        print(
            "improver: candidate rejected"
        )
        return False

    save_candidate_model(
        candidate_model
    )

    promote_candidate_model()

    print(
        "improver: candidate promoted"
    )

    return True
