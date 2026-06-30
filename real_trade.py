"""
BO_AI_5M
real_trade.py
AI予測リアルトレードモード
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yfinance as yf
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split


TICKER = "JPY=X"
THRESHOLD = 0.70

PENDING_FILE = "real_pending.json"
HISTORY_FILE = "real_history.csv"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

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


def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text,
        },
        timeout=20,
    ).raise_for_status()


def load_market_data():
    data = yf.download(
        TICKER,
        period="60d",
        interval="5m",
        auto_adjust=False,
        progress=False,
    )

    if data.empty:
        raise RuntimeError("データ取得失敗")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data[["Open", "High", "Low", "Close"]].dropna()

    return data


def build_features(data):
    data = data.copy()

    data["MA5"] = data["Close"].rolling(5).mean()
    data["MA10"] = data["Close"].rolling(10).mean()
    data["MA20"] = data["Close"].rolling(20).mean()

    data["EMA20"] = data["Close"].ewm(span=20, adjust=False).mean()
    data["EMA50"] = data["Close"].ewm(span=50, adjust=False).mean()

    data["Return"] = data["Close"].pct_change()
    data["Return3"] = data["Close"].pct_change(3)
    data["Return5"] = data["Close"].pct_change(5)

    delta = data["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))

    tr1 = data["High"] - data["Low"]
    tr2 = (data["High"] - data["Close"].shift()).abs()
    tr3 = (data["Low"] - data["Close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    data["ATR"] = tr.rolling(14).mean()

    data["Hour"] = data.index.hour
    data["DayOfWeek"] = data.index.dayofweek

    data["Target"] = (
        data["Close"].shift(-1) > data["Close"]
    ).astype(int)

    data = data.dropna()

    return data


def train_ai(data):
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

    model.fit(X_train, y_train)

    return model


def predict_ai(model, data):
    latest = data.iloc[[-1]][FEATURES]
    down_prob, up_prob = model.predict_proba(latest)[0]
    confidence = max(up_prob, down_prob)

    if up_prob >= THRESHOLD:
        signal = "HIGH"
    elif down_prob >= THRESHOLD:
        signal = "LOW"
    else:
        signal = "SKIP"

    return {
        "signal": signal,
        "up_prob": float(up_prob),
        "down_prob": float(down_prob),
        "confidence": float(confidence),
    }


def load_pending():
    if not os.path.exists(PENDING_FILE):
        return None

    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_pending(data):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )


def clear_pending():
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)


def append_history(row):
    df = pd.DataFrame([row])

    if os.path.exists(HISTORY_FILE):
        df.to_csv(
            HISTORY_FILE,
            mode="a",
            header=False,
            index=False,
        )
    else:
        df.to_csv(
            HISTORY_FILE,
            index=False,
        )


def make_report():
    if not os.path.exists(HISTORY_FILE):
        return "📊 実トレ成績: まだ記録なし"

    df = pd.read_csv(HISTORY_FILE)

    total = len(df)
    wins = len(df[df["result"] == "WIN"])
    losses = len(df[df["result"] == "LOSE"])
    rate = wins / total * 100 if total else 0

    return f"""
📊 BO_AI_5M 実トレ成績

累計 : {total}戦
勝ち : {wins}
負け : {losses}
勝率 : {rate:.1f}%
"""


def start_ai_trade():
    if load_pending():
        print("判定待ちあり")
        return

    data = load_market_data()
    data = build_features(data)
    model = train_ai(data)
    result = predict_ai(model, data)

    latest = data.iloc[-1]
    latest_time = data.index[-1].tz_convert(
        ZoneInfo("Asia/Tokyo")
    )

    now = datetime.now(ZoneInfo("Asia/Tokyo"))

    signal = result["signal"]

    if signal == "SKIP":
        send_telegram(f"""
🤖 BO_AI_5M 実トレAI判定

判定 : ⚪ SKIP

📈 上昇確率 : {result["up_prob"]*100:.2f}%
📉 下降確率 : {result["down_prob"]*100:.2f}%

信頼度 : {result["confidence"]*100:.2f}%

今回は実トレ開始しません
""")
        return

    trade_id = now.strftime("%Y%m%d_%H%M%S")

    save_pending({
        "id": trade_id,
        "signal": signal,
        "entry_time": now.isoformat(),
        "entry_price": float(latest["Close"]),
        "up_prob": round(result["up_prob"], 6),
        "down_prob": round(result["down_prob"], 6),
        "confidence": round(result["confidence"], 6),
    })

    send_telegram(f"""
🎯 BO_AI_5M 実トレAI開始

ID : {trade_id}

AI判定 : {signal}

足時刻 : {latest_time.strftime("%Y-%m-%d %H:%M")}
開始時刻 : {now.strftime("%Y-%m-%d %H:%M:%S")}

開始価格 : {float(latest["Close"]):.3f}

📈 上昇確率 : {result["up_prob"]*100:.2f}%
📉 下降確率 : {result["down_prob"]*100:.2f}%

5分後に判定
""")


def check_trade():
    pending = load_pending()

    if not pending:
        start_ai_trade()
        return

    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    entry_time = datetime.fromisoformat(pending["entry_time"])

    elapsed = (now - entry_time).total_seconds()

    if elapsed < 300:
        print("まだ5分経過していません")
        return

    data = load_market_data()
    result_price = float(data.iloc[-1]["Close"])

    entry_price = float(pending["entry_price"])
    signal = pending["signal"]

    if result_price > entry_price:
        actual = "HIGH"
    elif result_price < entry_price:
        actual = "LOW"
    else:
        actual = "FLAT"

    if signal == actual:
        result = "WIN"
    else:
        result = "LOSE"

    append_history({
        "id": pending["id"],
        "signal": signal,
        "actual": actual,
        "entry_time": pending["entry_time"],
        "judge_time": now.isoformat(),
        "entry_price": entry_price,
        "result_price": result_price,
        "price_diff": round(result_price - entry_price, 6),
        "up_prob": pending["up_prob"],
        "down_prob": pending["down_prob"],
        "confidence": pending["confidence"],
        "result": result,
    })

    report = make_report()

    send_telegram(f"""
📊 BO_AI_5M 実トレAI判定結果

ID : {pending["id"]}

AI判定 : {signal}
実際 : {actual}

開始価格 : {entry_price:.3f}
判定価格 : {result_price:.3f}

価格差 : {result_price - entry_price:+.3f}

結果 : {"✅ 勝ち" if result == "WIN" else "❌ 負け"}

{report}
""")

    clear_pending()


def main():
    check_trade()


if __name__ == "__main__":
    main()
