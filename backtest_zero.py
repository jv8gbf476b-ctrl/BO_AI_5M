"""
ZERO v0.1
backtest_zero.py

過去5分足を使った
未学習期間バックテスト

目的：
・AI全体の実力
・HIGH / LOW別
・相場状態別
・時間帯別
・信頼度別
・SKIP別
・条件組み合わせ別

を未来側30%だけで検証する
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


TRAIN_RATIO = 0.70

# 組み合わせ条件を表示する最低件数
MIN_COMBO_COUNT = 30

# 注目する最低勝率
TARGET_WIN_RATE = 55.0


def train_backtest_model(data):

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

    total = len(labeled)

    split_index = int(
        total * TRAIN_RATIO
    )

    train_data = (
        labeled
        .iloc[:split_index]
        .copy()
    )

    test_data = (
        labeled
        .iloc[split_index:]
        .copy()
    )

    if len(train_data) < 1000:
        raise RuntimeError(
            "学習データが少なすぎます"
        )

    if len(test_data) < 300:
        raise RuntimeError(
            "検証データが少なすぎます"
        )

    model = create_model()

    model.fit(
        train_data[FEATURES],
        train_data["Target"].astype(int),
    )

    test_start_time = (
        test_data.index[0]
    )

    return (
        model,
        train_data,
        test_data,
        test_start_time,
    )


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


def calculate_summary(
    df,
    group_column,
):

    rows = []

    for value, group in df.groupby(
        group_column,
        dropna=False,
    ):

        trade = group[
            group["signal"] != "SKIP"
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

        total = (
            wins
            + losses
        )

        if total == 0:
            rate = 0.0

        else:
            rate = (
                wins
                / total
                * 100
            )

        rows.append({
            group_column: value,
            "件数": total,
            "勝ち": wins,
            "負け": losses,
            "勝率": rate,
        })

    result = pd.DataFrame(
        rows
    )

    if not result.empty:
        result = result.sort_values(
            [
                "勝率",
                "件数",
            ],
            ascending=[
                False,
                False,
            ],
        )

    return result


def calculate_raw_skip_summary(df):

    skip_data = df[
        df["signal"]
        == "SKIP"
    ].copy()

    if skip_data.empty:
        return pd.DataFrame()

    rows = []

    for reason, group in (
        skip_data.groupby(
            "skip_reason"
        )
    ):

        wins_if_entered = (
            group[
                "raw_correct"
            ]
            .sum()
        )

        total = len(group)

        rate = (
            wins_if_entered
            / total
            * 100
            if total
            else 0.0
        )

        rows.append({
            "SKIP理由": reason,
            "件数": total,
            "入っていた場合の勝ち": (
                int(
                    wins_if_entered
                )
            ),
            "入っていた場合の勝率": (
                rate
            ),
        })

    result = pd.DataFrame(
        rows
    )

    return result.sort_values(
        "入っていた場合の勝率"
    )


def show_table(
    title,
    df,
    max_rows=30,
):

    print()
    print(
        "=" * 70
    )

    print(title)

    print(
        "=" * 70
    )

    if df.empty:
        print(
            "データなし"
        )
        return

    display = (
        df
        .head(max_rows)
        .copy()
    )

    for column in display.columns:

        if (
            "勝率" in column
        ):
            display[column] = (
                display[column]
                .map(
                    lambda x:
                    f"{x:.2f}%"
                )
            )

    print(
        display
        .to_string(
            index=False
        )
    )


def main():

    print(
        "START ZERO BACKTEST"
    )

    # =========================
    # データ取得
    # =========================

    data = load_data()

    print(
        "raw data:",
        len(data),
    )

    data = build_features(
        data
    )

    print(
        "feature data:",
        len(data),
    )

    # =========================
    # 学習期間 / 試験期間
    # =========================

    (
        model,
        train_data,
        test_data,
        test_start_time,
    ) = train_backtest_model(
        data
    )

    print()
    print(
        "学習データ:",
        len(train_data),
    )

    print(
        "未来側テスト:",
        len(test_data),
    )

    print(
        "テスト開始:",
        test_start_time,
    )

    # =========================
    # 過去再現
    # =========================

    results = []

    test_indices = set(
        test_data.index
    )

    for position in range(
        len(data)
    ):

        current_time = (
            data.index[position]
        )

        if (
            current_time
            not in test_indices
        ):
            continue

        current_row = (
            data
            .iloc[[position]]
        )

        target_value = (
            data
            .iloc[position][
                "Target"
            ]
        )

        if pd.isna(
            target_value
        ):
            continue

        # この時点までのデータだけ渡す
        # 未来情報は一切入れない
        historical_data = (
            data
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
            if int(
                target_value
            ) == 1
            else "LOW"
        )

        raw_correct = (
            raw_signal
            == actual
        )

        if signal == "SKIP":

            result = (
                "NO_TRADE"
            )

        elif signal == actual:

            result = "WIN"

        else:

            result = "LOSE"

        edge = abs(
            prediction["up_prob"]
            - prediction["down_prob"]
        )

        latest = (
            historical_data
            .iloc[-1]
        )

        results.append({

            "time": (
                current_time
            ),

            "hour": int(
                latest["Hour"]
            ),

            "weekday": int(
                latest[
                    "DayOfWeek"
                ]
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

    result_df = pd.DataFrame(
        results
    )

    if result_df.empty:
        raise RuntimeError(
            "バックテスト結果がありません"
        )

    # =========================
    # 全体成績
    # =========================

    trades = result_df[
        result_df["signal"]
        != "SKIP"
    ]

    wins = int(
        (
            trades["result"]
            == "WIN"
        ).sum()
    )

    losses = int(
        (
            trades["result"]
            == "LOSE"
        ).sum()
    )

    total_trades = (
        wins
        + losses
    )

    win_rate = (
        wins
        / total_trades
        * 100
        if total_trades
        else 0.0
    )

    skip_count = int(
        (
            result_df["signal"]
            == "SKIP"
        ).sum()
    )

    print()
    print(
        "=" * 70
    )

    print(
        "ZERO 未学習期間バックテスト"
    )

    print(
        "=" * 70
    )

    print(
        "全判定数:",
        len(result_df),
    )

    print(
        "取引対象:",
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
        f"{win_rate:.2f}%",
    )

    # =========================
    # 各条件
    # =========================

    show_table(
        "HIGH / LOW別",
        calculate_summary(
            result_df,
            "raw_signal",
        ),
    )

    show_table(
        "相場トレンド別",
        calculate_summary(
            result_df,
            "trend",
        ),
    )

    show_table(
        "ボラティリティ別",
        calculate_summary(
            result_df,
            "volatility",
        ),
    )

    show_table(
        "時間帯別",
        calculate_summary(
            result_df,
            "hour",
        ),
        max_rows=24,
    )

    show_table(
        "AI信頼度別",
        calculate_summary(
            result_df,
            "confidence_band",
        ),
    )

    show_table(
        "予測差別",
        calculate_summary(
            result_df,
            "edge_band",
        ),
    )

    show_table(
        "SKIPの検証",
        calculate_raw_skip_summary(
            result_df
        ),
    )

    # =========================
    # 組み合わせ探索
    # =========================

    combo_rows = []

    trade_only = result_df[
        result_df["signal"]
        != "SKIP"
    ].copy()

    grouped = (
        trade_only
        .groupby(
            [
                "trend",
                "volatility",
                "raw_signal",
                "hour",
            ]
        )
    )

    for (
        trend,
        volatility,
        raw_signal,
        hour,
    ), group in grouped:

        total = len(group)

        if (
            total
            < MIN_COMBO_COUNT
        ):
            continue

        wins_combo = int(
            (
                group["result"]
                == "WIN"
            ).sum()
        )

        rate = (
            wins_combo
            / total
            * 100
        )

        combo_rows.append({

            "トレンド": (
                trend
            ),

            "ボラ": (
                volatility
            ),

            "方向": (
                raw_signal
            ),

            "時間": (
                hour
            ),

            "件数": (
                total
            ),

            "勝ち": (
                wins_combo
            ),

            "勝率": (
                rate
            ),
        })

    combo_df = pd.DataFrame(
        combo_rows
    )

    if not combo_df.empty:

        combo_df = (
            combo_df
            .sort_values(
                [
                    "勝率",
                    "件数",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
        )

        strong_combo = (
            combo_df[
                combo_df["勝率"]
                >= TARGET_WIN_RATE
            ]
        )

    else:

        strong_combo = (
            pd.DataFrame()
        )

    show_table(
        (
            f"勝率{TARGET_WIN_RATE:.0f}%以上 "
            f"かつ{MIN_COMBO_COUNT}件以上の条件"
        ),
        strong_combo,
        max_rows=50,
    )

    # =========================
    # CSV保存
    # =========================

    result_df.to_csv(
        "zero_backtest_results.csv",
        index=False,
    )

    combo_df.to_csv(
        "zero_backtest_combos.csv",
        index=False,
    )

    print()
    print(
        "zero_backtest_results.csv 保存"
    )

    print(
        "zero_backtest_combos.csv 保存"
    )

    print()
    print(
        "END ZERO BACKTEST"
    )


if __name__ == "__main__":
    main()
