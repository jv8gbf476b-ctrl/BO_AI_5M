"""
BO_AI_5M
AI研究所
confidence_lab.py

信頼度別勝率を分析する研究モジュール
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


def calc_stats(df):

    if df.empty:
        return {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
        }

    valid = df[
        df["result"].isin(
            ["WIN", "LOSE"]
        )
    ]

    total = len(valid)

    wins = len(
        valid[
            valid["result"] == "WIN"
        ]
    )

    losses = len(
        valid[
            valid["result"] == "LOSE"
        ]
    )

    win_rate = (
        wins / total * 100
        if total > 0
        else 0.0
    )

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
    }


def prepare_history():

    df = load_history()

    if df.empty:
        return df

    if "confidence" not in df.columns:
        raise RuntimeError(
            "history.csv に confidence 列がありません"
        )

    df = df.copy()

    df["confidence"] = pd.to_numeric(
        df["confidence"],
        errors="coerce",
    )

    df = df[
        df["result"].isin(
            ["WIN", "LOSE"]
        )
    ]

    df = df.dropna(
        subset=["confidence"]
    )

    return df


def get_bucket_df(
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


def analyze_confidence():

    df = prepare_history()

    if df.empty:
        return {
            "overall": {},
            "buckets": [],
        }

    overall = calc_stats(df)

    buckets = []

    for (
        label,
        minimum,
        maximum,
    ) in CONFIDENCE_BUCKETS:

        bucket_df = get_bucket_df(
            df,
            minimum,
            maximum,
        )

        stats = calc_stats(
            bucket_df
        )

        stats["label"] = label
        stats["minimum"] = minimum
        stats["maximum"] = maximum

        buckets.append(
            stats
        )

    return {
        "overall": overall,
        "buckets": buckets,
    }


def analyze_direction_confidence():

    df = prepare_history()

    results = {}

    for signal in [
        "HIGH",
        "LOW",
    ]:

        signal_df = df[
            df["signal"] == signal
        ]

        signal_result = []

        for (
            label,
            minimum,
            maximum,
        ) in CONFIDENCE_BUCKETS:

            bucket_df = get_bucket_df(
                signal_df,
                minimum,
                maximum,
            )

            stats = calc_stats(
                bucket_df
            )

            stats["label"] = label
            stats["minimum"] = minimum
            stats["maximum"] = maximum

            signal_result.append(
                stats
            )

        results[signal] = (
            signal_result
        )

    return results


def make_confidence_report():

    analysis = analyze_confidence()

    direction_analysis = (
        analyze_direction_confidence()
    )

    overall = analysis["overall"]

    if not overall:
        return (
            "AI研究所\n"
            "分析できるデータがありません。"
        )

    text = (
        "🧪 AI研究所\n\n"
        "📊 信頼度分析\n\n"
        f"分析対象 : {overall['total']}戦\n"
        f"勝率 : {overall['win_rate']:.1f}%\n"
    )

    text += "\n【信頼度別】\n"

    for item in analysis["buckets"]:

        if item["total"] == 0:

            text += (
                f"{item['label']} : "
                "データなし\n"
            )

            continue

        text += (
            f"{item['label']} : "
            f"{item['total']}戦 "
            f"{item['wins']}勝 "
            f"{item['losses']}敗 "
            f"勝率{item['win_rate']:.1f}%\n"
        )

    for signal in [
        "HIGH",
        "LOW",
    ]:

        text += (
            f"\n【{signal} 信頼度別】\n"
        )

        for item in (
            direction_analysis[signal]
        ):

            if item["total"] == 0:

                text += (
                    f"{item['label']} : "
                    "データなし\n"
                )

                continue

            text += (
                f"{item['label']} : "
                f"{item['total']}戦 "
                f"{item['wins']}勝 "
                f"{item['losses']}敗 "
                f"勝率{item['win_rate']:.1f}%\n"
            )

    return text


if __name__ == "__main__":

    print(
        make_confidence_report()
    )
