"""
Market Assistant
improver.py

ZERO v0.1
未来側データ検証型
自己改善エンジン
"""

import json
import os

from history import load_history

from model import (
    FEATURES,
    split_train_validation,
    train_fresh_model,
    train_full_model,
    predict_with_model,
)

from model_store import (
    load_current_model,
    save_candidate_model,
    promote_candidate_model,
)


STATE_FILE = "learning_state.json"

IMPROVE_INTERVAL = 300
FIRST_IMPROVE = 300

# 候補モデルが最低限超えるべき
# 未来側データでの方向正解率
MIN_VALIDATION_RATE = 50.5

# 前回採用モデルより
# 最低どれだけ改善してほしいか
MIN_IMPROVEMENT = 0.10


def load_state():

    if not os.path.exists(
        STATE_FILE
    ):
        return {
            "notified": [],
            "model_version": 1,
            "last_check": 0,
            "last_improve": 0,
            "best_validation_rate": 0.0,
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
        "last_check",
        state.get(
            "last_improve",
            0,
        ),
    )

    state.setdefault(
        "last_improve",
        0,
    )

    state.setdefault(
        "best_validation_rate",
        0.0,
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


def calc_model_win_rate(
    model,
    data,
):

    total = 0
    wins = 0

    for i in range(
        len(data)
    ):

        row = (
            data
            .iloc[[i]]
        )

        actual_target = int(
            data
            .iloc[i]["Target"]
        )

        up_prob, down_prob = (
            predict_with_model(
                model,
                row,
            )
        )

        predicted_target = (
            1
            if up_prob >= down_prob
            else 0
        )

        total += 1

        if (
            predicted_target
            == actual_target
        ):
            wins += 1

    if total == 0:
        return 0.0

    return (
        wins
        / total
        * 100
    )


def should_improve():

    df = load_history()

    if df.empty:

        print(
            "improver: "
            "history empty"
        )

        return None

    history_count = len(df)

    state = load_state()

    last_check = int(
        state.get(
            "last_check",
            0,
        )
    )

    print(
        "history:",
        history_count,
    )

    print(
        "last check:",
        last_check,
    )

    if (
        history_count
        < FIRST_IMPROVE
    ):
        return None

    milestone = (
        history_count
        // IMPROVE_INTERVAL
    ) * IMPROVE_INTERVAL

    if (
        milestone
        <= last_check
    ):
        return None

    # チェックした事実と
    # 採用した事実を分離
    state["last_check"] = (
        milestone
    )

    save_state(
        state
    )

    print(
        "improve check:",
        milestone,
    )

    return milestone


def improve_model(data):

    milestone = (
        should_improve()
    )

    if milestone is None:
        return False

    current_model = (
        load_current_model()
    )

    if current_model is None:

        print(
            "current model "
            "not found"
        )

        return False

    print(
        "ZERO validation start"
    )

    try:

        train_data, validation_data = (
            split_train_validation(
                data
            )
        )

    except Exception as e:

        print(
            "split error:",
            e,
        )

        return False

    print(
        "train rows:",
        len(train_data),
    )

    print(
        "validation rows:",
        len(validation_data),
    )

    # =========================
    # 候補モデル
    #
    # validation_dataには
    # 一切触れずに学習
    # =========================

    candidate_model = (
        train_fresh_model(
            data
        )
    )

    candidate_rate = (
        calc_model_win_rate(
            candidate_model,
            validation_data,
        )
    )

    print(
        "candidate "
        "validation:",
        round(
            candidate_rate,
            2,
        ),
    )

    # =========================
    # 状態取得
    # =========================

    state = load_state()

    best_rate = float(
        state.get(
            "best_validation_rate",
            0.0,
        )
    )

    print(
        "best validation:",
        round(
            best_rate,
            2,
        ),
    )

    # =========================
    # 最低ライン
    # =========================

    if (
        candidate_rate
        < MIN_VALIDATION_RATE
    ):

        print(
            "candidate rejected: "
            "validation too low"
        )

        return False

    # =========================
    # 改善判定
    #
    # 初回は最低ラインを
    # 超えていれば候補
    # =========================

    if (
        best_rate > 0
        and candidate_rate
        < (
            best_rate
            + MIN_IMPROVEMENT
        )
    ):

        print(
            "candidate rejected: "
            "no improvement"
        )

        return False

    # =========================
    # 採用決定
    #
    # validation合格後に
    # 正解確定済み全データで
    # 本番モデルを作り直す
    # =========================

    print(
        "candidate passed"
    )

    final_model = (
        train_full_model(
            data
        )
    )

    save_candidate_model(
        final_model
    )

    promote_candidate_model()

    # =========================
    # 学習状態更新
    # =========================

    state = load_state()

    state["model_version"] = (
        int(
            state.get(
                "model_version",
                1,
            )
        )
        + 1
    )

    state["last_improve"] = (
        milestone
    )

    state[
        "best_validation_rate"
    ] = float(
        candidate_rate
    )

    save_state(
        state
    )

    print(
        "candidate promoted"
    )

    print(
        "new model version:",
        state["model_version"],
    )

    print(
        "validation rate:",
        round(
            candidate_rate,
            2,
        ),
    )

    return True
