"""
Market Assistant
learning.py
学習レポート
"""

import json
import os

STATE_FILE = "learning_state.json"

MILESTONES = [
    30,
    100,
    300,
    600,
    1000,
    1500,
    2000,
]


def load_state():

    if not os.path.exists(STATE_FILE):
        return {
            "notified": [],
            "model_version": 1,
        }

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2,
        )


def calc_rate(df):

    if df.empty:
        return 0, 0, 0, 0.0

    total = len(df)
    wins = len(df
