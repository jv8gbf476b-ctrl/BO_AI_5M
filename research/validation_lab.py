"""
BO_AI_5M
AI研究所
validation_lab.py

過去データで見つけた条件が、
後半の未知データでも通用するか検証する
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


TRAIN_RATIO = 0.70
MIN_TRAIN_TRADES = 30
MIN_TEST_TRADES = 10


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

    df = df.sort_values(
        "_analysis_time"
    ).reset_index(
        drop=True
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

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / total * 100,
    }


def filter_condition(
    df,
    signal,
    minimum,
    maximum,
    start_hour,
    end_hour,
):

    result = df[
        df["signal"] == signal
    ]

    result = result[
        result["confidence"] >= minimum
    ]

    if maximum is not None:

        result = result[
            result["confidence"] < maximum
        ]

    result = result[
        (result["_hour"] >= start_hour)
        &
        (result["_hour"] < end_hour)
    ]

    return result


def split_history(df):

    split_index = int(
        len(df) * TRAIN_RATIO
    )

    train_df = df.iloc[
        :split_index
    ].copy()

    test_df = df.iloc[
        split_index:
    ].copy()

    return (
        train_df,
        test_df,
    )


def discover_conditions(
    train_df,
):

    conditions = []

    for signal in [
        "HIGH",
        "LOW",
    ]:

        for (
            confidence_label,
            minimum,
            maximum,
        ) in CONFIDENCE_BUCKETS:

            for (
                time_label,
                start_hour,
                end_hour,
            ) in TIME_BUCKETS:

                target = filter_condition(
                    train_df,
                    signal,
                    minimum,
                    maximum,
                    start_hour,
                    end_hour,
                )

                stats = calc_stats(
                    target
                )

                if (
                    stats["total"]
                    < MIN_TRAIN_TRADES
                ):
                    continue

                conditions.append(
                    {
                        "signal": signal,
                        "confidence_label":
                            confidence_label,
                        "minimum": minimum,
                        "maximum": maximum,
                        "time_label":
                            time_label,
                        "start_hour":
                            start_hour,
                        "end_hour":
                            end_hour,
                        "train_total":
                            stats["total"],
                        "train_wins":
                            stats["wins"],
                        "train_losses":
                            stats["losses"],
                        "train_rate":
                            stats["win_rate"],
                    }
                )

    conditions.sort(
        key=lambda x: (
            x["train_rate"],
            x["train_total"],
        ),
        reverse=True,
    )

    return conditions


def validate_conditions(
    test_df,
    conditions,
):

    results = []

    for condition in conditions:

        target = filter_condition(
            test_df,
            condition["signal"],
            condition["minimum"],
            condition["maximum"],
            condition["start_hour"],
            condition["end_hour"],
        )

        stats = calc_stats(
            target
        )

        if (
            stats["total"]
            < MIN_TEST_TRADES
        ):
            continue

        item = dict(
            condition
        )

        item["test_total"] = (
            stats["total"]
        )

        item["test_wins"] = (
            stats["wins"]
        )

        item["test_losses"] = (
            stats["losses"]
        )

        item["test_rate"] = (
            stats["win_rate"]
        )

        item["rate_diff"] = (
            item["test_rate"]
            - item["train_rate"]
        )

        results.append(
            item
        )

    return results


def make_report():

    df = prepare_history()

    if df.empty:

        return (
            "🧪 AI研究所\n"
            "検証データがありません。"
        )

    train_df, test_df = (
        split_history(
            df
        )
    )

    conditions = (
        discover_conditions(
            train_df
        )
    )

    validated = (
        validate_conditions(
            test_df,
            conditions,
        )
    )

    if not validated:

        return (
            "🧪 AI研究所 再現性検証\n\n"
            "検証可能な条件が"
            "ありませんでした。"
        )

    validated.sort(
        key=lambda x: (
            x["test_rate"],
            x["test_total"],
        ),
        reverse=True,
    )

    text = (
        "🧪 AI研究所 再現性検証\n\n"
        f"研究データ : {len(train_df)}戦\n"
        f"試験データ : {len(test_df)}戦\n"
        "古い70%で条件発見\n"
        "新しい30%で再検証\n\n"
        "📌 試験データ勝率 上位\n"
        "※研究30戦以上 / 試験10戦以上\n\n"
    )

    top_results = validated[
        :20
    ]

    for index, item in enumerate(
        top_results,
        start=1,
    ):

        text += (
            f"{index}. "
            f"{item['signal']} / "
            f"{item['confidence_label']} / "
            f"{item['time_label']}\n"
            f"   研究 : "
            f"{item['train_total']}戦 "
            f"勝率"
            f"{item['train_rate']:.1f}%\n"
            f"   試験 : "
            f"{item['test_total']}戦 "
            f"{item['test_wins']}勝 "
            f"{item['test_losses']}敗 "
            f"勝率"
            f"{item['test_rate']:.1f}%\n"
            f"   差 : "
            f"{item['rate_diff']:+.1f}pt\n"
        )

    return text


if __name__ == "__main__":

    print(
        make_report()
    )
