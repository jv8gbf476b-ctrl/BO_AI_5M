"""
BO_AI_5M
AI研究所
confidence_deep_lab.py

信頼度 × 方向 × 時間帯
深掘り分析
"""

import pandas as pd

from history import load_history


CONFIDENCE_BUCKETS = [
    ("50〜55%", 0.50, 0.55),
    ("55〜60%", 0.55, 0.60),
    ("60〜65%", 0.60, 0.65),
    ("65〜70%", 0.65, 0.70),
    ("70〜75%", 0.70, 0.75),
    ("75〜80%", 0.75, 0.80),
    ("80%以上", 0.80, None),
]


TIME_BUCKETS = [
    ("00〜03時", 0, 3),
    ("03〜06時", 3, 6),
    ("06〜09時", 6, 9),
    ("09〜12時", 9, 12),
    ("12〜15時", 12, 15),
    ("15〜18時", 15, 18),
    ("18〜21時", 18, 21),
    ("21〜24時", 21, 24),
]


def prepare_history():

    df = load_history()

    if df.empty:
        return df

    df = df.copy()

    required_columns = [
        "result",
        "signal",
        "confidence",
    ]

    for column in required_columns:

        if column not in df.columns:
            raise RuntimeError(
                f"history.csv に {column} 列がありません"
            )

    df["confidence"] = pd.to_numeric(
        df["confidence"],
        errors="coerce",
    )

    time_column = None

    if "entry_time_jst" in df.columns:
        time_column = "entry_time_jst"

    elif "entry_time" in df.columns:
        time_column = "entry_time"

    else:
        raise RuntimeError(
            "history.csv に時刻列がありません"
        )

    df["_analysis_time"] = pd.to_datetime(
        df[time_column],
        errors="coerce",
    )

    df = df[
        df["result"].isin(
            ["WIN", "LOSE"]
        )
    ]

    df = df.dropna(
        subset=[
            "confidence",
            "_analysis_time",
        ]
    )

    df["_hour"] = (
        df["_analysis_time"].dt.hour
    )

    return df


def calc_stats(df):

    total = len(df)

    if total == 0:
        return {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
        }

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

    win_rate = (
        wins / total * 100
    )

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
    }


def filter_confidence(
    df,
    minimum,
    maximum,
):

    result = df[
        df["confidence"] >= minimum
    ]

    if maximum is not None:

        result = result[
            result["confidence"] < maximum
        ]

    return result


def filter_time(
    df,
    start_hour,
    end_hour,
):

    return df[
        (df["_hour"] >= start_hour)
        &
        (df["_hour"] < end_hour)
    ]


def analyze():

    df = prepare_history()

    results = []

    if df.empty:
        return results

    for signal in [
        "HIGH",
        "LOW",
    ]:

        signal_df = df[
            df["signal"] == signal
        ]

        for (
            confidence_label,
            minimum,
            maximum,
        ) in CONFIDENCE_BUCKETS:

            confidence_df = (
                filter_confidence(
                    signal_df,
                    minimum,
                    maximum,
                )
            )

            for (
                time_label,
                start_hour,
                end_hour,
            ) in TIME_BUCKETS:

                target_df = filter_time(
                    confidence_df,
                    start_hour,
                    end_hour,
                )

                stats = calc_stats(
                    target_df
                )

                results.append(
                    {
                        "signal": signal,
                        "confidence": confidence_label,
                        "time": time_label,
                        "total": stats["total"],
                        "wins": stats["wins"],
                        "losses": stats["losses"],
                        "win_rate": stats["win_rate"],
                    }
                )

    return results


def find_best_conditions(
    min_trades=30,
):

    results = analyze()

    valid = [
        item
        for item in results
        if item["total"] >= min_trades
    ]

    valid.sort(
        key=lambda x: (
            x["win_rate"],
            x["total"],
        ),
        reverse=True,
    )

    return valid


def make_report():

    best = find_best_conditions(
        min_trades=30
    )

    if not best:

        return (
            "🧪 AI研究所\n\n"
            "深掘り分析できる条件が"
            "まだありません。"
        )

    text = (
        "🧪 AI研究所 深掘り分析\n\n"
        "📈 勝率上位条件\n"
        "※30戦以上のみ\n\n"
    )

    top_results = best[:20]

    for index, item in enumerate(
        top_results,
        start=1,
    ):

        text += (
            f"{index}. "
            f"{item['signal']} / "
            f"{item['confidence']} / "
            f"{item['time']}\n"
            f"   {item['total']}戦 "
            f"{item['wins']}勝 "
            f"{item['losses']}敗 "
            f"勝率{item['win_rate']:.1f}%\n"
        )

    return text


if __name__ == "__main__":

    print(
        make_report()
    )
