"""
BO_AI_5M
AI研究所
candidate_lab.py

実戦候補条件の総合評価

・全期間勝率
・直近20%勝率
・ウォークフォワード成績
・期間別最低勝率
・最大連敗
・サンプル数

をまとめて評価する。

※ score は「勝率予測」ではなく
研究所内部の安定度評価点。
"""

from history import load_history

from research.walkforward_lab import (
    CONFIDENCE_BUCKETS,
    TIME_BUCKETS,
    prepare_history,
    calc_stats,
    filter_condition,
    run_walkforward,
)


MIN_TOTAL_TRADES = 30
MIN_RECENT_TRADES = 10

RECENT_RATIO = 0.20

PERIOD_COUNT = 4
MIN_PERIOD_TRADES = 8


def calc_max_losing_streak(df):

    if df.empty:
        return 0

    max_streak = 0
    current_streak = 0

    for result in df["result"]:

        if result == "LOSE":

            current_streak += 1

            if current_streak > max_streak:
                max_streak = current_streak

        else:
            current_streak = 0

    return max_streak


def get_recent_df(df):

    if df.empty:
        return df

    start_index = int(
        len(df)
        * (1.0 - RECENT_RATIO)
    )

    return df.iloc[
        start_index:
    ].copy()


def calc_period_stats(
    condition_df,
):

    if condition_df.empty:
        return []

    total = len(
        condition_df
    )

    results = []

    for i in range(
        PERIOD_COUNT
    ):

        start = int(
            total
            * i
            / PERIOD_COUNT
        )

        end = int(
            total
            * (i + 1)
            / PERIOD_COUNT
        )

        period_df = condition_df.iloc[
            start:end
        ]

        stats = calc_stats(
            period_df
        )

        if (
            stats["total"]
            < MIN_PERIOD_TRADES
        ):
            continue

        results.append(
            {
                "period":
                    i + 1,
                "total":
                    stats["total"],
                "wins":
                    stats["wins"],
                "losses":
                    stats["losses"],
                "win_rate":
                    stats["win_rate"],
            }
        )

    return results


def get_walkforward_map():

    analysis = (
        run_walkforward()
    )

    result = {}

    for item in analysis[
        "summary"
    ]:

        key = (
            item["signal"],
            item[
                "confidence_label"
            ],
            item["time_label"],
        )

        result[key] = item

    return result


def score_rate(
    rate,
    max_points,
):

    if rate < 45:
        return 0.0

    if rate >= 60:
        return float(
            max_points
        )

    ratio = (
        rate - 45
    ) / 15

    return (
        ratio
        * max_points
    )


def score_sample_size(
    total,
):

    if total >= 150:
        return 10.0

    if total >= 100:
        return 8.0

    if total >= 60:
        return 6.0

    if total >= 30:
        return 4.0

    return 0.0


def score_losing_streak(
    streak,
):

    if streak <= 4:
        return 10.0

    if streak == 5:
        return 8.0

    if streak == 6:
        return 6.0

    if streak == 7:
        return 4.0

    if streak == 8:
        return 2.0

    return 0.0


def calculate_score(
    overall_rate,
    recent_rate,
    period_min_rate,
    total,
    max_losing_streak,
    wf_item,
):

    score = 0.0

    # 全期間
    score += score_rate(
        overall_rate,
        15,
    )

    # 直近
    score += score_rate(
        recent_rate,
        25,
    )

    # 期間別最低値
    score += score_rate(
        period_min_rate,
        15,
    )

    # サンプル数
    score += (
        score_sample_size(
            total
        )
    )

    # 最大連敗
    score += (
        score_losing_streak(
            max_losing_streak
        )
    )

    # ウォークフォワード
    if wf_item is not None:

        combined_rate = (
            wf_item[
                "combined_rate"
            ]
        )

        pass_rate = (
            wf_item[
                "pass_rate"
            ]
        )

        appearances = (
            wf_item[
                "appearances"
            ]
        )

        score += score_rate(
            combined_rate,
            15,
        )

        score += (
            pass_rate
            / 100
            * 10
        )

        if appearances >= 4:
            score += 10

        elif appearances == 3:
            score += 8

        elif appearances == 2:
            score += 5

        elif appearances == 1:
            score += 2

    return min(
        round(
            score,
            1,
        ),
        100.0,
    )


def classify_condition(
    overall,
    recent,
    period_stats,
    max_losing_streak,
    wf_item,
):

    if (
        overall["total"]
        < MIN_TOTAL_TRADES
    ):
        return "DATA不足"

    if (
        recent["total"]
        < MIN_RECENT_TRADES
    ):
        return "DATA不足"

    if not period_stats:
        return "DATA不足"

    period_min_rate = min(
        item["win_rate"]
        for item
        in period_stats
    )

    if wf_item is None:

        if (
            overall["win_rate"]
            >= 53
            and
            recent["win_rate"]
            >= 55
        ):
            return "要観察"

        return "過学習疑い"

    appearances = (
        wf_item["appearances"]
    )

    pass_rate = (
        wf_item["pass_rate"]
    )

    combined_rate = (
        wf_item["combined_rate"]
    )

    # 実戦候補
    if (
        overall["win_rate"] >= 53
        and
        recent["win_rate"] >= 55
        and
        period_min_rate >= 50
        and
        appearances >= 2
        and
        pass_rate >= 66
        and
        combined_rate >= 55
        and
        max_losing_streak <= 8
    ):
        return "実戦候補"

    # 要観察
    if (
        overall["win_rate"] >= 50
        and
        recent["win_rate"] >= 52
        and
        combined_rate >= 52
    ):
        return "要観察"

    return "過学習疑い"


def analyze_candidates():

    df = prepare_history()

    if df.empty:
        return []

    recent_df = get_recent_df(
        df
    )

    walkforward_map = (
        get_walkforward_map()
    )

    results = []

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

                full_target = (
                    filter_condition(
                        df,
                        signal,
                        minimum,
                        maximum,
                        start_hour,
                        end_hour,
                    )
                )

                overall = calc_stats(
                    full_target
                )

                if (
                    overall["total"]
                    < MIN_TOTAL_TRADES
                ):
                    continue

                recent_target = (
                    filter_condition(
                        recent_df,
                        signal,
                        minimum,
                        maximum,
                        start_hour,
                        end_hour,
                    )
                )

                recent = calc_stats(
                    recent_target
                )

                period_stats = (
                    calc_period_stats(
                        full_target
                    )
                )

                if period_stats:

                    period_min_rate = min(
                        item["win_rate"]
                        for item
                        in period_stats
                    )

                else:

                    period_min_rate = 0.0

                max_losing_streak = (
                    calc_max_losing_streak(
                        full_target
                    )
                )

                key = (
                    signal,
                    confidence_label,
                    time_label,
                )

                wf_item = (
                    walkforward_map.get(
                        key
                    )
                )

                classification = (
                    classify_condition(
                        overall,
                        recent,
                        period_stats,
                        max_losing_streak,
                        wf_item,
                    )
                )

                score = calculate_score(
                    overall["win_rate"],
                    recent["win_rate"],
                    period_min_rate,
                    overall["total"],
                    max_losing_streak,
                    wf_item,
                )

                result = {
                    "signal":
                        signal,

                    "confidence":
                        confidence_label,

                    "time":
                        time_label,

                    "total":
                        overall["total"],

                    "overall_rate":
                        overall["win_rate"],

                    "recent_total":
                        recent["total"],

                    "recent_rate":
                        recent["win_rate"],

                    "period_min_rate":
                        period_min_rate,

                    "max_losing_streak":
                        max_losing_streak,

                    "classification":
                        classification,

                    "score":
                        score,

                    "wf_appearances":
                        0,

                    "wf_passes":
                        0,

                    "wf_pass_rate":
                        0.0,

                    "wf_combined_rate":
                        0.0,
                }

                if wf_item is not None:

                    result[
                        "wf_appearances"
                    ] = (
                        wf_item[
                            "appearances"
                        ]
                    )

                    result[
                        "wf_passes"
                    ] = (
                        wf_item[
                            "passes"
                        ]
                    )

                    result[
                        "wf_pass_rate"
                    ] = (
                        wf_item[
                            "pass_rate"
                        ]
                    )

                    result[
                        "wf_combined_rate"
                    ] = (
                        wf_item[
                            "combined_rate"
                        ]
                    )

                results.append(
                    result
                )

    results.sort(
        key=lambda x: (
            x["classification"]
            == "実戦候補",
            x["classification"]
            == "要観察",
            x["score"],
            x["total"],
        ),
        reverse=True,
    )

    return results


def make_report():

    results = (
        analyze_candidates()
    )

    if not results:

        return (
            "🧪 AI研究所\n"
            "候補条件を評価できません。"
        )

    live = [
        item
        for item in results
        if (
            item["classification"]
            == "実戦候補"
        )
    ]

    watch = [
        item
        for item in results
        if (
            item["classification"]
            == "要観察"
        )
    ]

    text = (
        "🧪 AI研究所 "
        "実戦候補審査\n\n"
        "※研究スコアは"
        "予測勝率ではありません。\n"
        "複数検証をまとめた"
        "安定度評価です。\n\n"
    )

    text += (
        "🎯 実戦候補\n\n"
    )

    if not live:

        text += (
            "現在、基準を満たす"
            "条件なし。\n"
        )

    else:

        for index, item in enumerate(
            live[:10],
            start=1,
        ):

            text += (
                f"{index}. "
                f"{item['signal']} / "
                f"{item['confidence']} / "
                f"{item['time']}\n"
                f"   研究スコア : "
                f"{item['score']:.1f}/100\n"
                f"   全期間 : "
                f"{item['total']}戦 "
                f"勝率"
                f"{item['overall_rate']:.1f}%\n"
                f"   直近20% : "
                f"{item['recent_total']}戦 "
                f"勝率"
                f"{item['recent_rate']:.1f}%\n"
                f"   期間最低 : "
                f"{item['period_min_rate']:.1f}%\n"
                f"   最大連敗 : "
                f"{item['max_losing_streak']}\n"
                f"   WF : "
                f"{item['wf_passes']}/"
                f"{item['wf_appearances']}成功 "
                f"合算"
                f"{item['wf_combined_rate']:.1f}%\n"
            )

    text += (
        "\n👀 要観察 TOP10\n\n"
    )

    if not watch:

        text += (
            "要観察条件なし。\n"
        )

    else:

        for index, item in enumerate(
            watch[:10],
            start=1,
        ):

            text += (
                f"{index}. "
                f"{item['signal']} / "
                f"{item['confidence']} / "
                f"{item['time']} "
                f"→ "
                f"{item['score']:.1f}点\n"
                f"   全体"
                f"{item['overall_rate']:.1f}% / "
                f"直近"
                f"{item['recent_rate']:.1f}% / "
                f"WF"
                f"{item['wf_combined_rate']:.1f}%\n"
            )

    rejected = len(
        [
            item
            for item in results
            if (
                item[
                    "classification"
                ]
                == "過学習疑い"
            )
        ]
    )

    text += (
        "\n📌 審査結果\n"
        f"実戦候補 : "
        f"{len(live)}条件\n"
        f"要観察 : "
        f"{len(watch)}条件\n"
        f"過学習疑い : "
        f"{rejected}条件\n"
    )

    return text


if __name__ == "__main__":

    print(
        make_report()
    )
