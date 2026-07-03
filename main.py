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


def main():

    data = load_data()
    data = build_features(data)

    pending = load_pending()

    if pending:
        data = grade_pending(data, pending)

    model = get_model(data)
    result = predict_latest(model, data)

    latest = data.iloc[-1]
    latest_time = data.index[-1]

    save_pending({
        "id": latest_time.strftime("%Y%m%d_%H%M"),
        "entry_time": latest_time.isoformat(),
        "entry_time_jst": latest_time.tz_convert("Asia/Tokyo").isoformat(),
        "entry_close": float(latest["Close"]),
        "signal": (
            "HIGH"
            if result["up_prob"] >= 0.70
            else "LOW"
            if result["down_prob"] >= 0.70
            else "SKIP"
        ),
        "up_prob": result["up_prob"],
        "down_prob": result["down_prob"],
        "confidence": result["confidence"],
    })

    report = check_learning(load_history())

    if report:
        send_telegram(report)


if __name__ == "__main__":
    main()
