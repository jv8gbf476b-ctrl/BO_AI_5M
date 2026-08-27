"""
BO_AI_5M
AI研究所
live_test.py

完全未来データ検証
"""

import json
import os

from history import load_history
from research.walkforward_lab import (
    prepare_history,
    filter_condition,
)


STATE_FILE = "research/live_test_state.json"


CANDIDATES = [
    {
        "name": "LOW_50_55_03_06",
        "signal": "LOW",
        "minimum": 0.50,
        "maximum": 0.55,
        "start_hour": 3,
        "end_hour": 6,
    },
    {
        "name": "LOW_55_60_18_21",
        "signal": "LOW",
        "minimum": 0.55,
        "maximum": 0.60,
        "start_hour": 18,
        "end_hour": 21,
    },
    {
        "name": "HIGH_65_70_12_15",
        "signal": "HIGH",
        "minimum": 0.65,
        "maximum": 0.70,
        "start_hour": 12,
        "end_hour": 15,
    },
    {
        "name": "HIGH_55_60_00_03",
        "signal": "HIGH",
        "minimum": 0.55,
        "maximum": 0.60,
        "start_hour": 0,
        "end_hour": 3,
    },
]


def load_state():

    if not os.path.exists(
        STATE_FILE
    ):
        return None

    with open(
        STATE_FILE,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


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


def initialize():

    history = load_history()

    state = {
        "start_row": len(history),
    }

    save_state(
        state
    )

    return state


def get_future_history():

    state = load_state()

    if state is None:
        state = initialize()

    history = load_history()

    start_row = int(
        state["start_row"]
    )

    if len(history) <= start_row:
        return history.iloc[0:0]

    return history.iloc[
        start_row:
    ].copy()


def calc_result(df):

    total = len(df)

    wins = len(
        df[
            df["result"] == "WIN"
        ]
    )

    losses = len(
        df[
            df["result"] == "LOSE"
        ]
    )

    rate = (
        wins / total * 100
        if total
        else 0.0
    )

    return (
        total,
        wins,
        losses,
        rate,
    )


def make_live_report():

    state = load_state()

    if state is None:

        state = initialize()

        return (
            "🧪 AI研究所 未来検証開始\n\n"
            f"開始位置 : "
            f"{state['start_row']}行\n\n"
            "ここから追加される"
            "新規データだけで検証します。"
        )

    future_raw = (
        get_future_history()
    )

    if future_raw.empty:

        return (
            "🧪 AI研究所 未来検証\n\n"
            "新しいデータ待ち"
        )

    future = prepare_history()

    start_row = int(
        state["start_row"]
    )

    # prepare_history後の行番号ではなく
    # 時刻を使って未来部分を取得する
    raw_history = load_history()

    if start_row >= len(
        raw_history
    ):

        return (
            "🧪 AI研究所 未来検証\n\n"
            "新しいデータ待ち"
        )

    time_column = (
        "entry_time_jst"
        if "entry_time_jst"
        in raw_history.columns
        else "entry_time"
    )

    start_time = (
        raw_history.iloc[
            start_row
        ][time_column]
    )

    start_time = (
        future[
            "_analysis_time"
            >= future[
                "_analysis_time"
            ].min()
        ]
    )

    # start_row以降に存在する
    # 最初の時刻を取得
    future_raw_time = (
        raw_history.iloc[
            start_row:
        ][time_column]
    )

    first_future_time = (
        future_raw_time.iloc[0]
    )

    import pandas as pd

    first_future_time = (
        pd.to_datetime(
            first_future_time,
            errors="coerce",
        )
    )

    future = future[
        future["_analysis_time"]
        >= first_future_time
    ]

    text = (
        "🧪 AI研究所 未来検証\n\n"
        f"未来データ : "
        f"{len(future_raw)}件\n\n"
    )

    for candidate in CANDIDATES:

        target = filter_condition(
            future,
            candidate["signal"],
            candidate["minimum"],
            candidate["maximum"],
            candidate["start_hour"],
            candidate["end_hour"],
        )

        (
            total,
            wins,
            losses,
            rate,
        ) = calc_result(
            target
        )

        text += (
            f"{candidate['name']}\n"
            f"{total}戦 "
            f"{wins}勝 "
            f"{losses}敗 "
            f"勝率{rate:.1f}%\n\n"
        )

    return text


if __name__ == "__main__":

    print(
        make_live_report()
    )
