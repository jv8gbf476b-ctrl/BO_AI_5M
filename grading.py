"""
BO_AI_5M
grading.py

ZERO v0.4
通常採点
+
ZERO仮想実戦採点
"""

from zoneinfo import (
    ZoneInfo,
)

import pandas as pd

from history import (
    append_history,
)

from pending import (
    clear_pending,
)

from telegram_bot import (
    send_telegram,
)


def grade_pending(
    data,
    pending,
):

    print(
        "grading start"
    )

    print(
        "pending id:",
        pending.get("id"),
    )

    entry_time = (
        pd.Timestamp(
            pending[
                "entry_time"
            ]
        )
    )

    future = data[
        data.index
        > entry_time
    ]

    print(
        "future rows:",
        len(future),
    )

    if future.empty:

        print(
            "まだ採点できない"
        )

        return data

    # =====================================
    # 5分後
    # =====================================

    result_time = (
        future.index[0]
    )

    result_close = float(
        future.iloc[0][
            "Close"
        ]
    )

    entry_close = float(
        pending[
            "entry_close"
        ]
    )

    signal = (
        pending["signal"]
    )

    raw_signal = (
        pending.get(
            "raw_signal",
            signal,
        )
    )

    skip_reason = (
        pending.get(
            "skip_reason",
            "",
        )
    )

    # =====================================
    # 実際の方向
    # =====================================

    if (
        result_close
        > entry_close
    ):

        actual = "HIGH"

    elif (
        result_close
        < entry_close
    ):

        actual = "LOW"

    else:

        actual = "FLAT"

    # =====================================
    # 通常AI採点
    # =====================================

    if signal == "SKIP":

        result = "NO_TRADE"

    elif signal == actual:

        result = "WIN"

    elif actual == "FLAT":

        result = "FLAT"

    else:

        result = "LOSE"

    # =====================================
    # ZERO仮想実戦採点
    # =====================================

    zero_entry = bool(
        pending.get(
            "zero_entry",
            False,
        )
    )

    zero_rule = (
        pending.get(
            "zero_rule",
            "",
        )
    )

    zero_direction = (
        pending.get(
            "zero_direction",
            "",
        )
    )

    if not zero_entry:

        zero_result = (
            "NO_ENTRY"
        )

    elif actual == "FLAT":

        zero_result = (
            "FLAT"
        )

    elif (
        zero_direction
        == actual
    ):

        zero_result = (
            "WIN"
        )

    else:

        zero_result = (
            "LOSE"
        )

    # =====================================
    # 履歴
    # =====================================

    row = {

        "id": (
            pending["id"]
        ),

        "entry_time": (
            pending[
                "entry_time_jst"
            ]
        ),

        "judge_time": (
            result_time
            .tz_convert(
                ZoneInfo(
                    "Asia/Tokyo"
                )
            )
            .isoformat()
        ),

        # 通常AI
        "signal": signal,

        "raw_signal": (
            raw_signal
        ),

        "skip_reason": (
            skip_reason
        ),

        "actual_direction": (
            actual
        ),

        "result": result,

        # ZERO仮想実戦
        "zero_entry": (
            zero_entry
        ),

        "zero_rule": (
            zero_rule
        ),

        "zero_direction": (
            zero_direction
        ),

        "zero_result": (
            zero_result
        ),

        # 価格
        "entry_close": (
            entry_close
        ),

        "result_close": (
            result_close
        ),

        "price_diff": round(
            result_close
            - entry_close,
            6,
        ),

        # AI
        "up_prob": (
            pending.get(
                "up_prob"
            )
        ),

        "down_prob": (
            pending.get(
                "down_prob"
            )
        ),

        "confidence": (
            pending.get(
                "confidence"
            )
        ),

        "edge": (
            pending.get(
                "edge"
            )
        ),

        # 相場
        "market_trend": (
            pending.get(
                "market_trend"
            )
        ),

        "market_volatility": (
            pending.get(
                "market_volatility"
            )
        ),

        # 特徴量
        "Open": (
            pending.get(
                "Open"
            )
        ),

        "High": (
            pending.get(
                "High"
            )
        ),

        "Low": (
            pending.get(
                "Low"
            )
        ),

        "Close": (
            pending.get(
                "Close"
            )
        ),

        "MA5": (
            pending.get(
                "MA5"
            )
        ),

        "MA10": (
            pending.get(
                "MA10"
            )
        ),

        "MA20": (
            pending.get(
                "MA20"
            )
        ),

        "EMA20": (
            pending.get(
                "EMA20"
            )
        ),

        "EMA50": (
            pending.get(
                "EMA50"
            )
        ),

        "Return": (
            pending.get(
                "Return"
            )
        ),

        "Return3": (
            pending.get(
                "Return3"
            )
        ),

        "Return5": (
            pending.get(
                "Return5"
            )
        ),

        "RSI": (
            pending.get(
                "RSI"
            )
        ),

        "ATR": (
            pending.get(
                "ATR"
            )
        ),

        "Hour": (
            pending.get(
                "Hour"
            )
        ),

        "DayOfWeek": (
            pending.get(
                "DayOfWeek"
            )
        ),
    }

    append_history(
        row
    )

    print(
        "history appended"
    )

    print(
        "signal:",
        signal,
    )

    print(
        "actual:",
        actual,
    )

    print(
        "result:",
        result,
    )

    print(
        "ZERO ENTRY:",
        zero_entry,
    )

    print(
        "ZERO RULE:",
        zero_rule
        if zero_rule
        else "NONE",
    )

    print(
        "ZERO RESULT:",
        zero_result,
    )

    # =====================================
    # 仮想実戦結果通知
    # =====================================

    if zero_entry:

        send_telegram(
            f"""
🧪 ZERO 仮想実戦結果

ルール : {zero_rule}

方向 :
{zero_direction}

結果 :
{"✅ WIN" if zero_result == "WIN" else "❌ LOSE" if zero_result == "LOSE" else "➖ FLAT"}

開始価格 :
{entry_close:.5f}

5分後 :
{result_close:.5f}

実際 :
{actual}

※実際のお金は使用していません
"""
        )

    clear_pending()

    print(
        "pending cleared"
    )

    return data
