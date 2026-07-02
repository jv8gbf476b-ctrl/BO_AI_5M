"""
BO_AI_5M
learning.py
"""

import json
import os
import pandas as pd

STATE_FILE = "learning_state.json"

MILESTONES = [30, 100, 300]


def load_state():

    if not os.path.exists(STATE_FILE):

        return {
            "notified": [],
            "model_version": 1
        }

    with open(
        STATE_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2
        )


def calc_rate(df):

    if df.empty:

        return 0, 0, 0

    total = len(df)

    wins = len(
        df[
            df["result"] == "WIN"
        ]
    )

    rate = wins / total * 100

    return total, wins, rate


def confidence_analysis(df):

    result = []

    if "confidence" not in df.columns:

        return result

    ranges = [

        ("90%以上",0.90,1.01),

        ("80〜90%",0.80,0.90),

        ("70〜80%",0.70,0.80),

        ("60〜70%",0.60,0.70),

        ("60%未満",0,0.60),

    ]

    for name,low,high in ranges:

        sub = df[
            (df["confidence"]>=low)
            &
            (df["confidence"]<high)
        ]

        total,wins,rate = calc_rate(sub)

        result.append({

            "name":name,

            "total":total,

            "wins":wins,

            "rate":rate

        })

    return result


def signal_analysis(df):

    result=[]

    for signal in ["HIGH","LOW"]:

        sub=df[
            df["signal"]==signal
        ]

        total,wins,rate=calc_rate(sub)

        result.append({

            "signal":signal,

            "total":total,

            "wins":wins,

            "rate":rate

        })

    return result
