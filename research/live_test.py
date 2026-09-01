"""
BO_AI_5M
AI研究所
live_test.py

完全未来データ検証

2026年8月27日に確定した
history.csv 10476行目以降のみを
未来データとして検証する。
"""

import pandas as pd

from history import load_history


# 未来検証を開始した時点
# この数字は今後変更しない
START_ROW = 10476


CANDIDATES = [
    {
        "name": "LOW / 50〜55% / 03〜06時",
        "signal": "LOW",
        "minimum": 0.50,
        "maximum": 0.55,
        "start_hour": 3,
        "end_hour": 6,
    },
    {
        "name": "LOW / 55〜60% / 18〜21時",
        "signal": "LOW",
        "minimum": 0.55,
        "maximum": 0.60,
        "start_hour": 18,
        "end_hour": 21,
    },
    {
        "name": "HIGH / 65〜70% / 12〜15時",
        "signal": "HIGH",
        "minimum": 0.65,
        "maximum": 0.70,
        "start_hour": 12,
        "end_hour": 15,
    },
    {
        "name": "HIGH / 55〜60% / 00〜03時",
        "signal": "HIGH",
        "minimum": 0.55,
        "maximum": 0.60,
        "start_hour": 0,
        "end_hour": 3,
    },
]


def prepare_future_history():

    history = load_history()

    if history.empty:
        return pd.DataFrame(), 0

    history_total = len(
        history
    )

    if history_total <= START_ROW:
        return (
            pd.DataFrame(),
            history_total,
        )

    # 10476行目以降だけ取得
    future = history.iloc[
        START_ROW:
    ].copy()

    required_columns = [
        "result",
        "signal",
        "confidence",
    ]

    for column in required_columns:

        if column not in future.columns:
            raise RuntimeError(
                f"history.csv に "
                f"{column} 列がありません"
            )

    future["confidence"] = (
        pd.to_numeric(
            future["confidence"],
            errors="coerce",
        )
    )

    if (
        "entry_time_jst"
        in future.columns
    ):

        time_column = (
            "entry_time_jst"
        )

    elif (
        "entry_time"
        in future.columns
    ):

        time_column = (
            "entry_time"
        )

    else:

        raise RuntimeError(
            "history.csv に"
            "時刻列がありません"
        )

    future["_analysis_time"] = (
        pd.to_datetime(
            future[time_column],
            errors="coerce",
        )
    )

    future = future.dropna(
        subset=[
            "confidence",
            "_analysis_time",
        ]
    )

    future["_hour"] = (
        future[
            "_analysis_time"
        ].dt.hour
    )

    return (
        future,
        history_total,
    )


def filter_candidate(
    df,
    candidate,
):

    if df.empty:
        return df

    result = df[
        df["result"].isin(
            [
                "WIN",
                "LOSE",
            ]
        )
    ]

    result = result[
        result["signal"]
        == candidate["signal"]
    ]

    result = result[
        result["confidence"]
        >= candidate["minimum"]
    ]

    if (
        candidate["maximum"]
        is not None
    ):

        result = result[
            result["confidence"]
            < candidate["maximum"]
        ]

    result = result[
        (
            result["_hour"]
            >= candidate[
                "start_hour"
            ]
        )
        &
        (
            result["_hour"]
            < candidate[
                "end_hour"
            ]
        )
    ]

    return result


def calc_result(df):

    total = len(
        df
    )

    wins = len(
        df[
            df["result"]
            == "WIN"
        ]
    )

    losses = len(
        df[
            df["result"]
            == "LOSE"
        ]
    )

    rate = (
        wins
        / total
        * 100
        if total > 0
        else 0.0
    )

    return (
        total,
        wins,
        losses,
        rate,
    )


def make_live_report():

    (
        future,
        history_total,
    ) = prepare_future_history()

    future_rows = max(
        history_total
        - START_ROW,
        0,
    )

    text = (
        "🧪 AI研究所 未来検証\n\n"
        f"固定開始位置 : "
        f"{START_ROW}行\n"
        f"現在位置 : "
        f"{history_total}行\n"
        f"未来データ : "
        f"{future_rows}件\n\n"
    )

    if future.empty:

        text += (
            "新しいデータ待ち"
        )

        return text

    valid_trades = future[
        future["result"].isin(
            [
                "WIN",
                "LOSE",
            ]
        )
    ]

    text += (
        f"採点済み実取引 : "
        f"{len(valid_trades)}戦\n\n"
    )

    for candidate in CANDIDATES:

        target = (
            filter_candidate(
                future,
                candidate,
            )
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
            f"勝率"
            f"{rate:.1f}%\n\n"
        )

    return text


if __name__ == "__main__":

    print(
        make_live_report()
    )
