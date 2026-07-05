"""
Market Assistant
main.py
学習実行
"""

from data import load_data
from features import build_features
from model import get_model
from model import predict_latest
from pending import load_pending
from pending import save_pending
from grading import grade_pending
from history import load_history
from learning import check_learning
from telegram_bot import send_telegram

from config import THRESHOLD
from config import ENABLE_SIGNAL_NOTIFICATION
from config import ENABLE_LEARNING_NOTIFICATION


def decide_signal(up_prob, down_prob):

    if up_prob >= THRESHOLD:
        return "HIGH"

    if down_prob >= THRESHOLD:
        return "LOW"

    return "SKIP"


def save_signal(data, result):

    latest = data.iloc[-1]
    latest_time = data.index[-1]

    signal = decide_signal(
        result["up_prob"],
        result["down_prob"],
    )

    save_pending({
        "id": latest_time.strftime("%Y%m%d_%H%M"),
        "entry_time": latest_time.isoformat(),
        "entry_time_jst": latest_time.tz_convert("Asia/Tokyo").isoformat(),
        "entry_close": float(latest["Close"]),
        "signal": signal,
        "up_prob": result["up_prob"],
        "down_prob": result["down_prob"],
        "confidence": result["confidence"],
    })

    if ENABLE_SIGNAL_NOTIFICATION:
        send_telegram(f"""
🤖 Market Assistant

AI : {signal}

上昇確率 : {result["up_prob"]*100:.2f}%
下降確率 : {result["down_prob"]*100:.2f}%
信頼度 : {result["confidence"]*100:.2f}%
""")


def main():

    data = load_data()
    data = build_features(data)

    pending = load_pending()

    if pending:
        data = grade_pending(data, pending)

    model = get_model(data)
    result = predict_latest(model, data)

    save_signal(data, result)

    if ENABLE_LEARNING_NOTIFICATION:
        history = load_history()
        learning_report = check_learning(history)

        if learning_report:
            send_telegram(learning_report)


if __name__ == "__main__":
    main()
