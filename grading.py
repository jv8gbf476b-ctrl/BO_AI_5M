"""
BO_AI_5M
grading.py
"""

from zoneinfo import ZoneInfo
import pandas as pd

from history import append_history
from pending import clear_pending


def grade_pending(data, pending):

    print("grading start")
    print("pending id:", pending.get("id"))

    entry_time = pd.Timestamp(pending["entry_time"])

    future = data[
        data.index > entry_time
    ]

    print("future rows:", len(future))

    if future.empty:
        print("まだ採点できない")
        return data

    result_time = future.index[0]
    result_close = float(future.iloc[0]["Close"])
    entry_close = float(pending["entry_close"])
    signal = pending["signal"]

    if result_close > entry_close:
        actual = "HIGH"
    elif result_close < entry_close:
        actual = "LOW"
    else:
        actual = "FLAT"

    if signal == actual:
        result = "WIN"
    else:
        result = "LOSE"

    row = {
        "id": pending["id"],
        "entry_time": pending["entry_time_jst"],
        "judge_time": result_time.tz_convert(
            ZoneInfo("Asia/Tokyo")
        ).isoformat(),
        "signal": signal,
        "actual_direction": actual,
        "entry_close": entry_close,
        "result_close": result_close,
        "price_diff": round(result_close - entry_close, 6),
        "up_prob": pending["up_prob"],
        "down_prob": pending["down_prob"],
        "confidence": pending["confidence"],
        "result": result,
    }

    append_history(row)

    print("history appended")
    print("result:", result)
    print("actual:", actual)

    clear_pending()
    print("pending cleared")

    return data
