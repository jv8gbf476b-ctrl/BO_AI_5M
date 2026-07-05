"""
Market Assistant
improver.py
"""

from history import load_history
from model import train_model
from model_store import (
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

    model = train_model(data)

    save_candidate_model(
        model
    )

    promote_candidate_model()

    return True
