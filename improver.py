"""
Market Assistant
improver.py
自己改善エンジン
"""

import json
import os

from history import load_history
from model import train_fresh_model
from model import predict_with_model
from model_store import (
    load_current_model,
    save_candidate_model,
    promote_candidate_model,
)

STATE_FILE = "learning_state.json"

IMPROVE_INTERVAL = 300
FIRST_IMPROVE = 300


def load_state():

    if not os.path.exists(STATE_FILE):
        return {
            "notified": [],
            "model_version": 1,
            "last_improve": 0,
        }

    with open(
        STATE_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        state = json.load(f)

    state.setdefault("notified", [])
    state.setdefault("model_version", 1)
    state.setdefault("last_improve", 0)

    return state


def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2,
        )


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

        signal = (
            "HIGH"
            if up_prob >= down_prob
            else "LOW"
        )

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

    history_count = len(df)

    state = load_state()

    last_improve = state["last_improve"]

    print(
        "history:",
        history_count,
    )

    print(
        "last improve:",
        last_improve,
    )

    if history_count < FIRST_IMPROVE:
        return False

    milestone = (
        history_count
        // IMPROVE_INTERVAL
    ) * IMPROVE_INTERVAL

    if milestone <= last_improve:
        return False

    state["last_improve"] = milestone
    save_state(state)

    print(
        "improve milestone:",
        milestone,
    )

    return True


def improve_model(data):

    if not should_improve():
        return False

    current_model = load_current_model()

    if current_model is None:
        print(
            "current model not found"
        )
        return False

    print(
        "training candidate..."
    )

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
        "current:",
        round(current_rate, 2),
    )

    print(
        "candidate:",
        round(candidate_rate, 2),
    )

    if candidate_rate <= current_rate:

        print(
            "candidate rejected"
        )

        return False

    save_candidate_model(
        candidate_model
    )

    promote_candidate_model()

    state = load_state()

    state["model_version"] += 1

    save_state(state)

    print(
        "candidate promoted"
    )

    return True
