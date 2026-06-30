import os
import json
import requests
import yfinance as yf
import pandas as pd
from zoneinfo import ZoneInfo
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

THRESHOLD = 0.70
TICKER = "JPY=X"
HISTORY_FILE = "history.csv"
PENDING_FILE = "pending_signal.json"


def send_telegram(text):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=20
    )
    response.raise_for_status()


def make_confidence_text(confidence):
    if confidence >= 0.85:
        return "★★★★★"
    if confidence >= 0.80:
        return "★★★★☆"
    if confidence >= 0.75:
        return "★★★☆☆"
    if confidence >= 0.70:
        return "★★☆☆☆"
    return "★☆☆☆☆"


def load_pending():
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_pending(data):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clear_pending():
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)


def append_history(row):
    df = pd.DataFrame([row])
    if os.path.exists(HISTORY_FILE):
        df.to_csv(HISTORY_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(HISTORY_FILE, index=False)


def make_report_text():
    if not os.path.exists(HISTORY_FILE):
        return "📊 成績: まだ記録なし"

    df = pd.read_csv(HISTORY_FILE)

    if df.empty or "result" not in df.columns:
        return "📊 成績: まだ記録なし"

    total = len(df)
    wins = len(df[df["result"] == "WIN"])
    losses = len(df[df["result"] == "LOSE"])
    win_rate = wins / total * 100 if total else 0

    report = f"""
📊 BO_AI 成績レポート

累計: {total}戦 {wins}勝 {losses}敗
勝率: {win_rate:.1f}%
"""

    for sig in ["HIGH", "LOW", "SKIP"]:
        if "signal" not in df.columns:
            continue

        sub = df[df["signal"] == sig]
        if len(sub) > 0:
            sub_wins = len(sub[sub["result"] == "WIN"])
            sub_rate = sub_wins / len(sub) * 100
            label = "見送り" if sig == "SKIP" else sig
            report += f"{label}: {len(sub)}戦 {sub_wins}勝 勝率{sub_rate:.1f}%\n"

    return report


def fetch_data():
    data = yf.download(
        TICKER,
        period="180d",
        interval="1h",
        auto_adjust=False,
        progress=False
    )

    if data.empty:
        raise RuntimeError("yfinanceからデータを取得できませんでした")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data[["Open", "High", "Low", "Close"]].dropna()

    data["MA5"] = data["Close"].rolling(5).mean()
    data["MA10"] = data["Close"].rolling(10).mean()
    data["EMA20"] = data["Close"].ewm(span=20).mean()
    data["Return"] = data["Close"].pct_change()

    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))

    data["Hour"] = data.index.hour
    data["DayOfWeek"] = data.index.dayofweek

    tr1 = data["High"] - data["Low"]
    tr2 = (data["High"] - data["Close"].shift()).abs()
    tr3 = (data["Low"] - data["Close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    data["ATR"] = tr.rolling(14).mean()

    data["Target"] = (data["Close"].shift(-1) > data["Close"]).astype(int)
    data = data.dropna()

    return data


def train_model(data):
    features = [
        "Open", "High", "Low", "Close",
        "MA5", "MA10", "EMA20",
        "Return", "RSI", "Hour", "DayOfWeek", "ATR"
    ]

    X = data[features]
    y = data["Target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        shuffle=False
    )

    model = LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        random_state=42,
        verbose=-1
    )

    model.fit(X_train, y_train)
    return model, features


def grade_pending(data):
    pending = load_pending()

    if not pending:
        print("前回シグナルなし")
        return

    entry_time = pd.Timestamp(pending["entry_time"])
    future = data[data.index > entry_time]

    if future.empty:
        print("前回シグナルはまだ判定できません")
        return

    result_time = future.index[0]
    result_close = float(future.iloc[0]["Close"])
    entry_close = float(pending["entry_close"])
    signal = pending["signal"]

    if result_close > entry_close:
        actual_direction = "HIGH"
    elif result_close < entry_close:
        actual_direction = "LOW"
    else:
        actual_direction = "FLAT"

    if signal == "HIGH":
        win = actual_direction == "HIGH"
        reason = "予測HIGHと実際HIGHが一致"
    elif signal == "LOW":
        win = actual_direction == "LOW"
        reason = "予測LOWと実際LOWが一致"
    else:
        win = actual_direction == "FLAT"
        reason = "値動きが小さく見送り正解" if win else f"見送り中に{actual_direction}方向へ動いたためチャンス逃し"

    result = "WIN" if win else "LOSE"
    price_diff = result_close - entry_close

    append_history({
        "id": pending["id"],
        "entry_time": pending["entry_time_jst"],
        "judge_time": result_time.tz_convert(ZoneInfo("Asia/Tokyo")).isoformat(),
        "signal": signal,
        "actual_direction": actual_direction,
        "entry_close": entry_close,
        "result_close": result_close,
        "price_diff": round(price_diff, 6),
        "up_prob": pending["up_prob"],
        "down_prob": pending["down_prob"],
        "confidence": pending["confidence"],
        "delay_minutes": pending.get("delay_minutes", ""),
        "result": result
    })

    report = make_report_text()

    message = f"""
📊 BO_AI 採点結果

ID: {pending["id"]}

AI判断: {signal}
実際の方向: {actual_direction}

エントリー価格: {entry_close:.3f}
判定価格: {result_close:.3f}
価格差: {price_diff:+.3f}

結果: {"✅ 勝ち" if win else "❌ 負け"}
理由: {reason}

{report}
"""

    send_telegram(message)
    print(message)
    clear_pending()


def predict_new(data, model, features):
    latest_time = data.index[-1]
    latest = data.iloc[[-1]][features]
    prob = model.predict_proba(latest)[0]

    down_prob = float(prob[0])
    up_prob = float(prob[1])
    confidence = max(up_prob, down_prob)

    if down_prob >= THRESHOLD:
        signal = "LOW"
        signal_text = "📉 LOW エントリー"
    elif up_prob >= THRESHOLD:
        signal = "HIGH"
        signal_text = "📈 HIGH エントリー"
    else:
        signal = "SKIP"
        signal_text = "⚪ 見送り"

    jst_time = latest_time.tz_convert(ZoneInfo("Asia/Tokyo"))
    now_jst = datetime.now(ZoneInfo("Asia/Tokyo"))
    delay_minutes = int((now_jst - jst_time.to_pydatetime()).total_seconds() / 60)

    signal_id = jst_time.strftime("%Y%m%d_%H%M")
    confidence_text = make_confidence_text(confidence)

    pending = load_pending()
    already_saved = pending and pending.get("id") == signal_id

    if not already_saved:
        save_pending({
            "id": signal_id,
            "entry_time": latest_time.isoformat(),
            "entry_time_jst": jst_time.isoformat(),
            "entry_close": float(data["Close"].iloc[-1]),
            "signal": signal,
            "up_prob": round(up_prob, 6),
            "down_prob": round(down_prob, 6),
            "confidence": round(confidence, 6),
            "delay_minutes": delay_minutes
        })
    else:
        print("同じ足のシグナルは保存済みですが、通知は送ります")

    message = f"""
🤖 BO_AI_RUN

ID: {signal_id}

足時刻: {jst_time}
通知時刻: {now_jst.strftime("%Y-%m-%d %H:%M:%S")}
遅延: {delay_minutes}分

現在価格: {data["Close"].iloc[-1]:.3f}

📈 上昇確率: {up_prob*100:.2f}%
📉 下降確率: {down_prob*100:.2f}%

信頼度: {confidence_text}

判定: {signal_text}
"""

    print(message)

    if signal == "SKIP":
        print("⚪ 見送りも記録しました。Telegramにも通知します")

    send_telegram(message)
    print("✅ Telegramへ送信しました")


def main():
    data = fetch_data()
    grade_pending(data)
    model, features = train_model(data)
    predict_new(data, model, features)


if __name__ == "__main__":
    main()
