"""
Market Assistant
model.py

ZERO v0.1
時間順学習
未来側検証対応
"""

import numpy as np

from lightgbm import LGBMClassifier

from model_store import (
    load_current_model,
    save_current_model,
)


FEATURES = [
    "Open",
    "High",
    "Low",
    "Close",
    "MA5",
    "MA10",
    "MA20",
    "EMA20",
    "EMA50",
    "Return",
    "Return3",
    "Return5",
    "RSI",
    "ATR",
    "Hour",
    "DayOfWeek",
]


VALIDATION_RATIO = 0.20
MIN_VALIDATION_ROWS = 300
MIN_TRAIN_ROWS = 1000


def create_model():

    return LGBMClassifier(
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=63,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbose=-1,
    )


def get_labeled_data(data):

    required = (
        FEATURES
        + ["Target"]
    )

    clean = (
        data
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .dropna(
            subset=required
        )
        .copy()
    )

    clean["Target"] = (
        clean["Target"]
        .astype(int)
    )

    return clean


def split_train_validation(data):

    labeled = get_labeled_data(
        data
    )

    total = len(labeled)

    if total < (
        MIN_TRAIN_ROWS
        + MIN_VALIDATION_ROWS
    ):
        raise RuntimeError(
            "学習データ不足: "
            f"{total}件"
        )

    validation_size = max(
        MIN_VALIDATION_ROWS,
        int(
            total
            * VALIDATION_RATIO
        ),
    )

    if (
        total
        - validation_size
        < MIN_TRAIN_ROWS
    ):
        validation_size = (
            total
            - MIN_TRAIN_ROWS
        )

    train_data = (
        labeled
        .iloc[:-validation_size]
        .copy()
    )

    validation_data = (
        labeled
        .iloc[-validation_size:]
        .copy()
    )

    return (
        train_data,
        validation_data,
    )


def fit_model(data):

    model = create_model()

    X = data[FEATURES]
    y = data["Target"]

    model.fit(
        X,
        y,
    )

    return model


def train_fresh_model(data):

    """
    候補モデル用。

    古い80%程度だけで学習し、
    新しい20%程度には触れない。
    """

    train_data, _ = (
        split_train_validation(
            data
        )
    )

    model = fit_model(
        train_data
    )

    return model


def train_full_model(data):

    """
    採用決定後の本番モデル。

    正解が確定しているデータのみ
    全件使って学習する。
    """

    labeled = get_labeled_data(
        data
    )

    if len(labeled) < MIN_TRAIN_ROWS:

        raise RuntimeError(
            "学習データ不足: "
            f"{len(labeled)}件"
        )

    model = fit_model(
        labeled
    )

    return model


def train_model(data):

    model = train_full_model(
        data
    )

    save_current_model(
        model
    )

    return model


def get_model(data):

    model = load_current_model()

    if model is not None:
        return model

    return train_model(
        data
    )


def predict_latest(
    model,
    data,
):

    latest = (
        data
        .iloc[[-1]][FEATURES]
    )

    probabilities = (
        model
        .predict_proba(
            latest
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
        "confidence": float(
            confidence
        ),
    }


def predict_with_model(
    model,
    row,
):

    latest = row[FEATURES]

    probabilities = (
        model
        .predict_proba(
            latest
        )[0]
    )

    down_prob = float(
        probabilities[0]
    )

    up_prob = float(
        probabilities[1]
    )

    return (
        up_prob,
        down_prob,
    )
