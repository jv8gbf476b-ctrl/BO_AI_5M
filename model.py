"""
BO_AI_5M
model.py
"""

from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split

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


def train_model(data):

    X = data[FEATURES]
    y = data["Target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        shuffle=False,
    )

    model = LGBMClassifier(
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=63,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbose=-1,
    )

    model.fit(
        X_train,
        y_train,
    )

    return model


def predict_latest(model, data):

    latest = data.iloc[[-1]][FEATURES]

    down_prob, up_prob = model.predict_proba(
        latest
    )[0]

    confidence = max(
        up_prob,
        down_prob,
    )

    return {
        "up_prob": float(up_prob),
        "down_prob": float(down_prob),
        "confidence": float(confidence),
    }
