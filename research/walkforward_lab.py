"""
BO_AI_5M
AI研究所
walkforward_lab.py

ウォークフォワード検証

過去で見つけた条件が、
その後の期間でも繰り返し通用するか検証する。
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


# 研究期間で最低30戦
MIN_TRAIN_TRADES = 30

# 試験期間で最低8戦
MIN_TEST_TRADES = 8

# 研究期間で最低52%以上だった条件だけ検証対象
MIN_TRAIN_WIN_RATE = 52.0

# 試験期間で「成功」とみなす最低勝率
PASS_WIN_RATE = 55.0


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
                f"history.csv に "
                f"{column} 列がありません"
            )

    df["confidence"] = pd.to_numeric(
        df["confidence"],
        errors="coerce",
    )

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
            [
                "WIN",
                "LOSE",
            ]
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

    win_rate = (
        wins
        / total
        * 100
    )

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
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
        (
            result["_hour"]
            >= start_hour
        )
        &
        (
            result["_hour"]
            < end_hour
        )
    ]

    return result


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

                if (
                    stats["win_rate"]
                    < MIN_TRAIN_WIN_RATE
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
                        "train_rate":
                            stats["win_rate"],
                    }
                )

    return conditions


def condition_key(
    condition,
):

    return (
        condition["signal"],
        condition["confidence_label"],
        condition["time_label"],
    )


def make_folds(df):

    total = len(df)

    if total < 100:

        return []

    folds = []

    # 50%で研究 → 次の10%で試験
    folds.append(
        (
            "50→60%",
            0.00,
            0.50,
            0.50,
            0.60,
        )
    )

    # 60%で研究 → 次の10%で試験
    folds.append(
        (
            "60→70%",
            0.00,
            0.60,
            0.60,
            0.70,
        )
    )

    # 70%で研究 → 次の10%で試験
    folds.append(
        (
            "70→80%",
            0.00,
            0.70,
            0.70,
            0.80,
        )
    )

    # 80%で研究 → 最後の20%で試験
    folds.append(
        (
            "80→100%",
            0.00,
            0.80,
            0.80,
            1.00,
        )
    )

    result = []

    for (
        label,
        train_start_ratio,
        train_end_ratio,
        test_start_ratio,
        test_end_ratio,
    ) in folds:

        train_start = int(
            total
            * train_start_ratio
        )

        train_end = int(
            total
            * train_end_ratio
        )

        test_start = int(
            total
            * test_start_ratio
        )

        test_end = int(
            total
            * test_end_ratio
        )

        train_df = df.iloc[
            train_start:train_end
        ].copy()

        test_df = df.iloc[
            test_start:test_end
        ].copy()

        result.append(
            {
                "label": label,
                "train": train_df,
                "test": test_df,
            }
        )

    return result


def run_walkforward():

    df = prepare_history()

    if df.empty:

        return {
            "total": 0,
            "folds": [],
            "summary": [],
        }

    folds = make_folds(
        df
    )

    summary = {}

    fold_results = []

    for fold in folds:

        train_df = fold["train"]
        test_df = fold["test"]

        conditions = discover_conditions(
            train_df
        )

        current_results = []

        for condition in conditions:

            test_target = (
                filter_condition(
                    test_df,
                    condition["signal"],
                    condition["minimum"],
                    condition["maximum"],
                    condition["start_hour"],
                    condition["end_hour"],
                )
            )

            test_stats = calc_stats(
                test_target
            )

            if (
                test_stats["total"]
                < MIN_TEST_TRADES
            ):
                continue

            passed = (
                test_stats["win_rate"]
                >= PASS_WIN_RATE
            )

            result = {
                "signal":
                    condition["signal"],
                "confidence_label":
                    condition[
                        "confidence_label"
                    ],
                "time_label":
                    condition["time_label"],
                "train_total":
                    condition["train_total"],
                "train_rate":
                    condition["train_rate"],
                "test_total":
                    test_stats["total"],
                "test_wins":
                    test_stats["wins"],
                "test_losses":
                    test_stats["losses"],
                "test_rate":
                    test_stats["win_rate"],
                "passed":
                    passed,
            }

            current_results.append(
                result
            )

            key = condition_key(
                condition
            )

            if key not in summary:

                summary[key] = {
                    "signal":
                        condition["signal"],
                    "confidence_label":
                        condition[
                            "confidence_label"
                        ],
                    "time_label":
                        condition["time_label"],
                    "appearances": 0,
                    "passes": 0,
                    "test_total": 0,
                    "test_wins": 0,
                    "test_losses": 0,
                }

            summary[key][
                "appearances"
            ] += 1

            if passed:

                summary[key][
                    "passes"
                ] += 1

            summary[key][
                "test_total"
            ] += test_stats["total"]

            summary[key][
                "test_wins"
            ] += test_stats["wins"]

            summary[key][
                "test_losses"
            ] += test_stats["losses"]

        current_results.sort(
            key=lambda x: (
                x["test_rate"],
                x["test_total"],
            ),
            reverse=True,
        )

        fold_results.append(
            {
                "label": fold["label"],
                "train_size":
                    len(train_df),
                "test_size":
                    len(test_df),
                "results":
                    current_results,
            }
        )

    summary_list = []

    for item in summary.values():

        if item["test_total"] == 0:
            continue

        item["combined_rate"] = (
            item["test_wins"]
            / item["test_total"]
            * 100
        )

        item["pass_rate"] = (
            item["passes"]
            / item["appearances"]
            * 100
        )

        summary_list.append(
            item
        )

    summary_list.sort(
        key=lambda x: (
            x["passes"],
            x["appearances"],
            x["combined_rate"],
            x["test_total"],
        ),
        reverse=True,
    )

    return {
        "total": len(df),
        "folds": fold_results,
        "summary": summary_list,
    }


def make_report():

    analysis = run_walkforward()

    if analysis["total"] == 0:

        return (
            "🧪 AI研究所\n"
            "ウォークフォワード検証"
            "できるデータがありません。"
        )

    text = (
        "🧪 AI研究所 "
        "ウォークフォワード検証\n\n"
        f"分析対象 : "
        f"{analysis['total']}戦\n\n"
        "過去だけ強い条件ではなく\n"
        "その後の期間でも"
        "勝てた条件を検証します。\n\n"
    )

    text += (
        "🏆 再現性ランキング\n"
        "試験勝率55%以上を"
        "1回成功として集計\n\n"
    )

    reliable = [
        item
        for item
        in analysis["summary"]
        if item["appearances"] >= 2
    ]

    if not reliable:

        text += (
            "複数期間で検証できた"
            "条件はありません。\n"
        )

    else:

        for index, item in enumerate(
            reliable[:20],
            start=1,
        ):

            text += (
                f"{index}. "
                f"{item['signal']} / "
                f"{item['confidence_label']} / "
                f"{item['time_label']}\n"
                f"   検証 : "
                f"{item['appearances']}回\n"
                f"   55%以上 : "
                f"{item['passes']}回\n"
                f"   成功率 : "
                f"{item['pass_rate']:.0f}%\n"
                f"   試験合計 : "
                f"{item['test_total']}戦 "
                f"{item['test_wins']}勝 "
                f"{item['test_losses']}敗\n"
                f"   合算勝率 : "
                f"{item['combined_rate']:.1f}%\n"
            )

    text += (
        "\n📊 各期間TOP5\n"
    )

    for fold in analysis["folds"]:

        text += (
            f"\n【{fold['label']}】\n"
            f"研究 : "
            f"{fold['train_size']}戦 / "
            f"試験 : "
            f"{fold['test_size']}戦\n"
        )

        if not fold["results"]:

            text += (
                "検証可能条件なし\n"
            )

            continue

        for item in (
            fold["results"][:5]
        ):

            mark = (
                "✅"
                if item["passed"]
                else "・"
            )

            text += (
                f"{mark} "
                f"{item['signal']} / "
                f"{item['confidence_label']} / "
                f"{item['time_label']} "
                f"→ "
                f"{item['test_total']}戦 "
                f"勝率"
                f"{item['test_rate']:.1f}%\n"
            )

    return text


if __name__ == "__main__":

    print(
        make_report()
    )
