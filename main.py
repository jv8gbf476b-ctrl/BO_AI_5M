"""
BO_AI_5M
main.py
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from config import THRESHOLD
from data import load_data
from features import build_features
from model import train_model
from model import predict_latest
from pending import load_pending
from pending import save_pending
from grading import grade_pending
from telegram_bot import send_telegram


def confidence_rank(confidence):

    if confidence >= 0.90:
        return "★★★★★"

    if confidence >= 0.80:
        return "★★★★☆"

    if confidence >= 0.75:
        return "★★★☆☆"

    if confidence >= 0.70:
        return "★★☆☆☆"

    return "★☆☆☆☆"


def decide_signal(up_prob, down_prob):

    if up_prob >= THRESHOLD:
        return "HIGH"

    if down_prob >= THRESHOLD:
        return "LOW"

    return "SKIP"


def notify_signal(data, result):

    latest = data.iloc[-1]
    latest_time = data.index[-1]

    up_prob = result["up_prob"]
    down_prob = result["down_prob"]
    confidence = result["confidence"]

    signal = decide_signal(
        up_prob,
        down_prob,
    )

    jst = latest_time.tz_convert(
        ZoneInfo("Asia/Tokyo")
    )

    now = datetime.now(
        ZoneInfo("Asia/Tokyo")
    )

    signal_id = jst.strftime(
        "%Y%m%d_%H%M"
    )

    save_pending({

        "id": signal_id,

        "entry_time": latest_time.isoformat(),

        "entry_time_jst": jst.isoformat(),

        "entry_close": float(
            latest["Close"]
        ),

        "signal": signal,

        "up_prob": up_prob,

        "down_prob": down_prob,

        "confidence": confidence,

    })

    if signal == "HIGH":
        signal_text = "📈 HIGH"

    elif signal == "LOW":
        signal_text = "📉 LOW"

    else:
        signal_text = "⚪ SKIP"

    message = f"""
🤖 BO_AI_5M

ID : {signal_id}

足時刻 : {jst.strftime("%Y-%m-%d %H:%M")}

通知 : {now.strftime("%Y-%m-%d %H:%M:%S")}

現在価格 : {latest["Close"]:.3f}

📈 上昇確率 : {up_prob*100:.2f}%

📉 下降確率 : {down_prob*100:.2f}%

信頼度 : {confidence_rank(confidence)}

判定 : {signal_text}
"""

    send_telegram(message)
    
    def main():

    data = load_data()

    data = build_features(
        data
    )

    pending = load_pending()

    if pending:

        data = grade_pending(
            data,
            pending,
        )

    model = train_model(
        data
    )

    result = predict_latest(
        model,
        data,
    )

    notify_signal(
        data,
        result,
    )


if __name__ == "__main__":
    main()
