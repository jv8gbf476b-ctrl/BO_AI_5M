"""
BO_AI_5M v6
grading.py
"""

from zoneinfo import ZoneInfo

from history import append_history
from report import make_report_text
from telegram_bot import send_telegram
from pending import clear_pending


def judge_signal(pending, result_time, result_close):

    entry_close = float(pending["entry_close"])
    signal = pending["signal"]

    if result_close > entry_close:
        actual = "HIGH"
    elif result_close < entry_close:
        actual = "LOW"
    else:
        actual = "FLAT"

    price_diff = result_close - entry_close

    if signal == "SKIP":
        result = "NO_TRADE"
        win = None
        reason = "見送り"
    else:
        if signal == actual:
            result = "WIN"
            win = True
            reason = "AI予測成功"
        else:
            result = "LOSE"
            win = False
            reason = "AI予測失敗"

    append_history({
        "id": pending["id"],
        "entry_time": pending["entry_time_jst"],
        "judge_time": result_time.tz_convert(
            ZoneInfo("Asia/Tokyo")
        ).isoformat(),
        "signal": signal,
        "actual_direction": actual,
        "entry_close": entry_close,
        "result_close": result_close,
        "price_diff": round(price_diff, 6),
        "up_prob": pending["up_prob"],
        "down_prob": pending["down_prob"],
        "confidence": pending["confidence"],
        "delay_minutes": pending.get("delay_minutes", ""),
        "result": result,
    })

    report = make_report_text()

    if result == "NO_TRADE":
        result_text = "⚪ 見送り"
    elif result == "WIN":
        result_text = "✅ 勝ち"
    else:
        result_text = "❌ 負け"

    message = f"""
📊 BO_AI_5M 採点結果

ID: {pending['id']}

AI判断 : {signal}
実際 : {actual}

エントリー : {entry_close:.3f}
判定 : {result_close:.3f}

価格差 : {price_diff:+.3f}

結果 : {result_text}

理由 : {reason}

{report}
"""

    send_telegram(message)
    clear_pending()

    return win
