"""
BO_AI_5M
grading.py
"""

from zoneinfo import ZoneInfo

from history import append_history
from report import make_report_text
from telegram_bot import send_telegram
from pending import clear_pending


def grade_pending(data, pending):

    entry_time = pending["entry_time"]

    future = data[
        data.index > entry_time
    ]

    if future.empty:
        return data

    result_time = future.index[0]

    result_close = float(
        future.iloc[0]["Close"]
    )

    entry_close = float(
        pending["entry_close"]
    )

    signal = pending["signal"]

    if result_close > entry_close:
        actual = "HIGH"

    elif result_close < entry_close:
        actual = "LOW"

    else:
        actual = "FLAT"

    if signal == "SKIP":

        result = "NO_TRADE"

    elif signal == actual:

        result = "WIN"

    else:

        result = "LOSE"

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

        "price_diff": round(
            result_close - entry_close,
            6,
        ),

        "up_prob": pending["up_prob"],

        "down_prob": pending["down_prob"],

        "confidence": pending["confidence"],

        "result": result,

    })

    report = make_report_text()

    send_telegram(f"""
📊 BO_AI_5M 採点結果

AI : {signal}
実際 : {actual}

結果 : {result}

{report}
""")

    clear_pending()

    return data
