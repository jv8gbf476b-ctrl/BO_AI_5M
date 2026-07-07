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
from improver import improve_model
from telegram_bot import send_telegram
from filter import detect_skip_filter

from config import ENABLE_SIGNAL_NOTIFICATION
from config import ENABLE_LEARNING_NOTIFICATION


def save_signal(data, result):

    latest = data.iloc[-1]
    latest_time = data.index[-1]

    skip, skip_reason, raw_signal = detect_skip_filter(
        data,
        result,
    )

    signal = "SKIP" if skip else raw_signal

    payload = {
        "id": latest_time.strftime("%Y%m%d_%H%M"),
        "entry_time": latest_time.isoformat(),
        "entry_time_jst": latest_time.tz_convert("Asia/Tokyo").isoformat(),
        "entry_close": float(latest["Close"]),
        "signal": signal,
        "raw_signal": raw_signal,
        "skip_reason": skip_reason,
        "up_prob": result["up_prob"],
        "down_prob": result["down_prob"],
        "confidence": result["confidence"],
    }

    save_pending(payload)

    print("saved pending_signal.json")
    print("id:", payload["id"])
    print("signal:", signal)
    print("raw_signal:", raw_signal)
    print("skip_reason:", skip_reason)
    print("close:", payload["entry_close"])

    if ENABLE_SIGNAL_NOTIFICATION:
        send_telegram(f"""
🤖 Market Assistant

AI : {signal}
元判定 : {raw_signal}
SKIP理由 : {skip_reason}

上昇確率 : {result["up_prob"]*100:.2f}%
下降確率 : {result["down_prob"]*100:.2f}%
信頼度 : {result["confidence"]*100:.2f}%
""")


def main():

    print("START Market Assistant")

    data = load_data()
    print("data loaded:", len(data))

    data = build_features(data)
    print("features built:", len(data))

    latest_time = data.index[-1]
    print("latest time:", latest_time)

    pending = load_pending()
    print("pending:", pending["id"] if pending else "none")

    if pending:
        data = grade_pending(data, pending)
        print("grading checked")

    improved = improve_model(data)
    print("improved:", improved)

    model = get_model(data)
    print("model ready")

    result = predict_latest(model, data)
    print("prediction:", result)

    save_signal(data, result)

    if improved:
        send_telegram("""
🤖 Market Assistant

自己改善モデルを更新しました。
新しいモデルで学習を継続します。
""")

    if ENABLE_LEARNING_NOTIFICATION:
        history = load_history()
        print("history rows:", len(history))

        learning_report = check_learning(history)

        if learning_report:
            send_telegram(learning_report)
            print("learning report sent")

    print("END Market Assistant")


if __name__ == "__main__":
    main()
