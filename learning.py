"""
Market Assistant
learning.py
学習レポート
"""

import json
import os


STATE_FILE = "learning_state.json"

FIRST_MILESTONES = [
    30,
    100,
]

REPORT_INTERVAL = 300


def load_state():

    if not os.path.exists(
        STATE_FILE
    ):
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

    state.setdefault(
        "notified",
        [],
    )

    state.setdefault(
        "model_version",
        1,
    )

    state.setdefault(
        "last_improve",
        0,
    )

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


def calc_rate(df):

    if df.empty:
        return 0, 0, 0, 0.0

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


def get_report_milestones(
    history_count,
):

    milestones = list(
        FIRST_MILESTONES
    )

    current = REPORT_INTERVAL

    while current <= history_count:

        milestones.append(
            current
        )

        current += REPORT_INTERVAL

    return milestones


def make_learning_report(
    df,
    milestone,
):

    trade_df = df[
        df["result"] != "NO_TRADE"
    ]

    skip_df = df[
        df["result"] == "NO_TRADE"
    ]

    (
        total,
        wins,
        losses,
        rate,
    ) = calc_rate(
        trade_df
    )

    history_total = len(df)
    skip_total = len(skip_df)

    skip_rate = (
        skip_total
        / history_total
        * 100
        if history_total
        else 0.0
    )

    text = f"""
🤖 Market Assistant 学習レポート

総データ {milestone}件 到達

全判定 : {history_total}件
実取引 : {total}戦
勝ち : {wins}
負け : {losses}
勝率 : {rate:.1f}%

SKIP : {skip_total}件
SKIP率 : {skip_rate:.1f}%
"""

    text += "\n📌 HIGH / LOW\n"

    for signal in [
        "HIGH",
        "LOW",
    ]:

        sub = trade_df[
            trade_df["signal"] == signal
        ]

        (
            signal_total,
            signal_wins,
            signal_losses,
            signal_rate,
        ) = calc_rate(
            sub
        )

        if signal_total > 0:

            text += (
                f"{signal} : "
                f"{signal_total}戦 "
                f"{signal_wins}勝 "
                f"{signal_losses}敗 "
                f"勝率{signal_rate:.1f}%\n"
            )

    text += (
        "\n次の300件まで"
        "学習を継続します。"
    )

    return text


def check_learning(df):

    if df.empty:
        return None

    history_count = len(df)

    state = load_state()

    notified = state.get(
        "notified",
        [],
    )

    milestones = (
        get_report_milestones(
            history_count
        )
    )

    pending_milestones = [
        milestone
        for milestone in milestones
        if milestone not in notified
    ]

    if not pending_milestones:
        return None

    # 過去の未通知分を連続送信せず、
    # 現在到達している最新の節目だけ通知する
    milestone = max(
        pending_milestones
    )

    for reached in milestones:

        if reached not in notified:
            notified.append(
                reached
            )

    notified.sort()

    state["notified"] = notified

    save_state(
        state
    )

    return make_learning_report(
        df,
        milestone,
    )
