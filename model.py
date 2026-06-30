"""
BO_AI_5M v6
model.py
"""

from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split

FEATURES = [
    "Open","High","Low","Close",
    "MA5","MA10","MA20","EMA20","EMA50",
    "Return","Return3","Return5",
    "RSI","ATR","ATR_Ratio",
    "PLUS_DI","MINUS_DI","ADX","ADX_Slope",
    "Hour","DayOfWeek",
    "BB_Middle","BB_Upper","BB_Lower","BB_Width","BB_Position",
    "MACD","MACD_Signal","MACD_Hist","MACD_Slope",
    "MA5_Gap","MA10_Gap","EMA20_Gap",
    "Momentum3","Momentum5","Momentum10",
    "Body","BodyAbs","Range",
    "UpperWick","LowerWick",
    "BodyRatio","UpperWickRatio","LowerWickRatio",
    "Volatility10",
    "TrendUp","EMA_Cross","CloseAboveMA20",
    "High20","Low20","DonchianWidth",
    "Stoch_K","Stoch_D",
    "ROC10",
]

def prepare_dataset(data):
    data = data.copy()
    data["Target"] = (data["Close"].shift(-1) > data["Close"]).astype(int)
    data = data.dropna()
    return data[FEATURES], data["Target"], data

def train_model(data):
    X, y, _ = prepare_dataset(data)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
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

    model.fit(X_train, y_train)
    return model

def get_feature_importance(model):
    return sorted(
        zip(FEATURES, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )

def predict_signal(model, data):
    latest = data.iloc[[-1]][FEATURES]
    down_prob, up_prob = model.predict_proba(latest)[0]
    confidence = max(up_prob, down_prob)

    return {
        "up_prob": float(up_prob),
        "down_prob": float(down_prob),
        "confidence": float(confidence),
        "importance": get_feature_importance(model)[:5],
    }
