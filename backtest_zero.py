"""
ZERO v0.2
backtest_zero.py

ウォークフォワード検証版

過去で学習
↓
次の期間だけでテスト
↓
学習期間を前へ進める
↓
また次の期間をテスト

これを繰り返して、
期間を変えても強い条件だけ探す
"""

import pandas as pd
import numpy as np

from data import load_data
from features import build_features

from model import (
    FEATURES,
    create_model,
)

from filter import (
    detect_skip_filter,
)


# =========================
# 設定
# =========================

INITIAL_TRAIN_RATIO = 0.50

# 1回ごとの未来テスト期間
TEST_BLOCK_SIZE = 1000

# 条件判定に必要な最低総件数
MIN_TOTAL_COUNT = 50

# 1期間あたり最低件数
MIN_BLOCK_COUNT = 8

# 採用候補の最低平均勝率
TARGET_WIN_RATE = 55.0

# 最低何期間で出現したか
MIN_BLOCKS = 3

# 期間ごとの最低勝率
MIN_BLOCK_WIN_RATE = 50.0


def confidence_band(value):

    percent = value * 100

    if percent < 55:
        return "50-55"

    if percent < 60:
        return "55-60"

    if percent < 65:
        return "60-65"

    if percent < 70:
        return "65-70"

    if percent < 75:
        return "70-75"

    if percent < 80:
        return "75-80"

    return "80+"


def edge_band(value):

    percent = value * 100

    if percent < 5:
        return "0-5"

    if percent < 10:
        return "5-10"

    if percent < 20:
        return "10-20"

    if percent < 30:
        return "20-30"

    return "30+"


def make_prediction(
    model,
    row,
):

    probabilities = (
        model
        .predict_proba(
            row[FEATURES]
        )[0]
    )

    down_prob = float(
        probabilities[0]
    )

    up_prob = float(
        probabilities[1]
    )

    confidence = max(
        up_prob,
        down_prob,
    )

    return {
        "up_prob": up_prob,
        "down_prob": down_prob,
        "confidence": confidence,
    }


def run_single_block(
    full_data,
    train_end,
    test_end,
    block_id,
):

    train_data = (
        full_data
        .iloc[:train_end]
        .copy()
    )

    test_data = (
        full_data
        .iloc[
            train_end:test_end
        ]
        .copy()
    )

    if len(test_data) == 0:
        return []

    model = create_model()

    model.fit(
        train_data[FEATURES],
        train_data["Target"].astype(int),
    )

    results = []

    start_position = train_end

    end_position = test_end

    for position in range(
        start_position,
        end_position,
    ):

        current_row = (
            full_data
            .iloc[[position]]
        )

        target_value = (
            full_data
            .iloc[position]["Target"]
        )

        if pd.isna(
            target_value
        ):
            continue

        historical_data = (
            full_data
            .iloc[
                :position + 1
            ]
        )

        prediction = (
            make_prediction(
                model,
                current_row,
            )
        )

        (
            skip,
            skip_reason,
            raw_signal,
            market,
        ) = detect_skip_filter(
            historical_data,
            prediction,
        )

        signal = (
            "SKIP"
            if skip
            else raw_signal
        )

        actual = (
            "HIGH"
            if int(target_value) == 1
            else "LOW"
        )

        raw_correct = (
            raw_signal
            == actual
        )

        if signal == "SKIP":

            result = "NO_TRADE"

        elif signal == actual:

            result = "WIN"

        else:

            result = "LOSE"

        latest = (
            historical_data
            .iloc[-1]
        )

        edge = abs(
            prediction["up_prob"]
            - prediction["down_prob"]
        )

        results.append({

            "block_id": block_id,

            "time": (
                full_data
                .index[position]
            ),

            "hour": int(
                latest["Hour"]
            ),

            "weekday": int(
                latest["DayOfWeek"]
            ),

            "signal": signal,

            "raw_signal": (
                raw_signal
            ),

            "actual": actual,

            "result": result,

            "raw_correct": (
                raw_correct
            ),

            "skip_reason": (
                skip_reason
            ),

            "trend": (
                market["trend"]
            ),

            "volatility": (
                market[
                    "volatility"
                ]
            ),

            "up_prob": (
                prediction[
                    "up_prob"
                ]
            ),

            "down_prob": (
                prediction[
                    "down_prob"
                ]
            ),

            "confidence": (
                prediction[
                    "confidence"
                ]
            ),

            "edge": edge,

            "confidence_band": (
                confidence_band(
                    prediction[
                        "confidence"
                    ]
                )
            ),

            "edge_band": (
                edge_band(
                    edge
                )
            ),

            "RSI": float(
                latest["RSI"]
            ),

            "ATR": float(
                latest["ATR"]
            ),
        })

    return results


def summarize_overall(df):

    trade = df[
        df["signal"]
        != "SKIP"
    ]

    wins = int(
        (
            trade["result"]
            == "WIN"
        ).sum()
    )

    losses = int(
        (
            trade["result"]
            == "LOSE"
        ).sum()
    )

    total = wins + losses

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


def build_combo_summary(
    df,
):

    trade = (
        df[
            df["signal"]
            != "SKIP"
        ]
        .copy()
    )

    combo_columns = [
        "trend",
        "volatility",
        "raw_signal",
        "hour",
    ]

    rows = []

    grouped = (
        trade
        .groupby(
            combo_columns
        )
    )

    for combo, group in grouped:

        trend = combo[0]
        volatility = combo[1]
        raw_signal = combo[2]
        hour = combo[3]

        total = len(group)

        if total < MIN_TOTAL_COUNT:
            continue

        wins = int(
            (
                group["result"]
                == "WIN"
            ).sum()
        )

        overall_rate = (
            wins
            / total
            * 100
        )

        block_rates = []

        valid_blocks = 0

        profitable_blocks = 0

        for block_id, block_group in (
            group.groupby(
                "block_id"
            )
        ):

            block_total = len(
                block_group
            )

            if (
                block_total
                < MIN_BLOCK_COUNT
            ):
                continue

            block_wins = int(
                (
                    block_group["result"]
                    == "WIN"
                ).sum()
            )

            block_rate = (
                block_wins
                / block_total
                * 100
            )

            block_rates.append(
                block_rate
            )

            valid_blocks += 1

            if (
                block_rate
                >= MIN_BLOCK_WIN_RATE
            ):
                profitable_blocks += 1

        if valid_blocks == 0:
            continue

        block_average = float(
            np.mean(
                block_rates
            )
        )

        block_min = float(
            np.min(
                block_rates
            )
        )

        block_max = float(
            np.max(
                block_rates
            )
        )

        stable_ratio = (
            profitable_blocks
            / valid_blocks
            * 100
        )

        rows.append({

            "trend": trend,

            "volatility": volatility,

            "direction": raw_signal,

            "hour": int(hour),

            "total_count": total,

            "wins": wins,

            "overall_rate": (
                overall_rate
            ),

            "valid_blocks": (
                valid_blocks
            ),

            "profitable_blocks": (
                profitable_blocks
            ),

            "stable_ratio": (
                stable_ratio
            ),

            "block_average": (
                block_average
            ),

            "block_min": (
                block_min
            ),

            "block_max": (
                block_max
            ),
        })

    summary = pd.DataFrame(
        rows
    )

    if summary.empty:
        return summary

    summary = (
        summary
        .sort_values(
            [
                "overall_rate",
                "stable_ratio",
                "total_count",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
    )

    return summary


def show_combo_table(
    df,
):

    print()
    print(
        "=" * 90
    )

    print(
        "ウォークフォワード安定条件"
    )

    print(
        "=" * 90
    )

    if df.empty:

        print(
            "条件なし"
        )

        return

    candidate = df[

        (
            df["overall_rate"]
            >= TARGET_WIN_RATE
        )

        &

        (
            df["valid_blocks"]
            >= MIN_BLOCKS
        )

    ].copy()

    if candidate.empty:

        print(
            "合格条件なし"
        )

        return

    candidate = (
        candidate
        .sort_values(
            [
                "stable_ratio",
                "overall_rate",
                "total_count",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
    )

    display = (
        candidate
        .head(30)
        .copy()
    )

    display[
        "overall_rate"
    ] = (
        display[
            "overall_rate"
        ]
        .map(
            lambda x:
            f"{x:.2f}%"
        )
    )

    display[
        "stable_ratio"
    ] = (
        display[
            "stable_ratio"
        ]
        .map(
            lambda x:
            f"{x:.1f}%"
        )
    )

    display[
        "block_average"
    ] = (
        display[
            "block_average"
        ]
        .map(
            lambda x:
            f"{x:.2f}%"
        )
    )

    display[
        "block_min"
    ] = (
        display[
            "block_min"
        ]
        .map(
            lambda x:
            f"{x:.2f}%"
        )
    )

    display[
        "block_max"
    ] = (
        display[
            "block_max"
        ]
        .map(
            lambda x:
            f"{x:.2f}%"
        )
    )

    print(
        display[
            [
                "trend",
                "volatility",
                "direction",
                "hour",
                "total_count",
                "overall_rate",
                "valid_blocks",
                "profitable_blocks",
                "stable_ratio",
                "block_average",
                "block_min",
                "block_max",
            ]
        ]
        .to_string(
            index=False
        )
    )


def main():

    print(
        "START ZERO WALK FORWARD"
    )

    data = load_data()

    print(
        "raw data:",
        len(data),
    )

    data = build_features(
        data
    )

    labeled = (
        data
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .dropna(
            subset=FEATURES + ["Target"]
        )
        .copy()
    )

    total = len(
        labeled
    )

    initial_train_size = int(
        total
        * INITIAL_TRAIN_RATIO
    )

    print(
        "usable data:",
        total,
    )

    print(
        "initial train:",
        initial_train_size,
    )

    all_results = []

    block_id = 1

    train_end = (
        initial_train_size
    )

    while (
        train_end
        < total
    ):

        test_end = min(
            train_end
            + TEST_BLOCK_SIZE,
            total,
        )

        print()
        print(
            "-" * 70
        )

        print(
            "BLOCK:",
            block_id,
        )

        print(
            "train:",
            train_end,
        )

        print(
            "test:",
            (
                test_end
                - train_end
            ),
        )

        results = (
            run_single_block(
                labeled,
                train_end,
                test_end,
                block_id,
            )
        )

        block_df = (
            pd.DataFrame(
                results
            )
        )

        if not block_df.empty:

            (
                total_trades,
                wins,
                losses,
                rate,
            ) = summarize_overall(
                block_df
            )

            print(
                "trade:",
                total_trades,
            )

            print(
                "WIN:",
                wins,
            )

            print(
                "LOSE:",
                losses,
            )

            print(
                "rate:",
                f"{rate:.2f}%",
            )

            all_results.extend(
                results
            )

        train_end = (
            test_end
        )

        block_id += 1

    result_df = (
        pd.DataFrame(
            all_results
        )
    )

    if result_df.empty:

        raise RuntimeError(
            "ウォークフォワード結果なし"
        )

    print()
    print(
        "=" * 90
    )

    print(
        "ZERO WALK FORWARD 全体"
    )

    print(
        "=" * 90
    )

    (
        total_trades,
        wins,
        losses,
        overall_rate,
    ) = summarize_overall(
        result_df
    )

    skip_count = int(
        (
            result_df["signal"]
            == "SKIP"
        ).sum()
    )

    print(
        "全判定:",
        len(result_df),
    )

    print(
        "取引:",
        total_trades,
    )

    print(
        "SKIP:",
        skip_count,
    )

    print(
        "WIN:",
        wins,
    )

    print(
        "LOSE:",
        losses,
    )

    print(
        "勝率:",
        f"{overall_rate:.2f}%",
    )

    combo_summary = (
        build_combo_summary(
            result_df
        )
    )

    show_combo_table(
        combo_summary
    )

    result_df.to_csv(
        "zero_walk_forward_results.csv",
        index=False,
    )

    combo_summary.to_csv(
        "zero_walk_forward_combos.csv",
        index=False,
    )

    print()
    print(
        "zero_walk_forward_results.csv 保存"
    )

    print(
        "zero_walk_forward_combos.csv 保存"
    )

    print()
    print(
        "END ZERO WALK FORWARD"
    )


if __name__ == "__main__":
    main()
