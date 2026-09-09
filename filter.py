"""
Market Assistant
filter.py

ZERO v0.1
相場状態判定
SKIPフィルター
"""


def get_raw_signal(
    up_prob,
    down_prob,
):

    if up_prob >= down_prob:
        return "HIGH"

    return "LOW"


def detect_market_state(data):

    latest = data.iloc[-1]

    close = float(
        latest["Close"]
    )

    ma5 = float(
        latest["MA5"]
    )

    ma20 = float(
        latest["MA20"]
    )

    ema20 = float(
        latest["EMA20"]
    )

    ema50 = float(
        latest["EMA50"]
    )

    atr = float(
        latest["ATR"]
    )

    # =========================
    # ボラティリティ
    # =========================

    if len(data) >= 30:

        atr_mean = float(
            data["ATR"]
            .tail(30)
            .mean()
        )

    else:
        atr_mean = atr

    if (
        atr_mean > 0
        and atr > atr_mean * 1.5
    ):
        volatility = "HIGH"

    elif (
        atr_mean > 0
        and atr < atr_mean * 0.7
    ):
        volatility = "LOW"

    else:
        volatility = "NORMAL"

    # =========================
    # トレンド
    # =========================

    if (
        close > ema20
        and ema20 > ema50
        and ma5 > ma20
    ):
        trend = "UP"

    elif (
        close < ema20
        and ema20 < ema50
        and ma5 < ma20
    ):
        trend = "DOWN"

    else:
        trend = "RANGE"

    return {
        "trend": trend,
        "volatility": volatility,
        "atr_mean": atr_mean,
    }


def detect_skip_filter(
    data,
    result,
):

    up_prob = result[
        "up_prob"
    ]

    down_prob = result[
        "down_prob"
    ]

    confidence = result[
        "confidence"
    ]

    edge = abs(
        up_prob
        - down_prob
    )

    raw_signal = (
        get_raw_signal(
            up_prob,
            down_prob,
        )
    )

    latest = data.iloc[-1]

    market = (
        detect_market_state(
            data
        )
    )

    # =========================
    # 弱い判定
    # =========================

    if edge < 0.05:

        return (
            True,
            "SKIP_WEAK_EDGE",
            raw_signal,
            market,
        )

    # =========================
    # 方向転換
    # =========================

    if len(data) >= 20:

        close_now = float(
            data["Close"]
            .iloc[-1]
        )

        close_5 = float(
            data["Close"]
            .iloc[-6]
        )

        close_15 = float(
            data["Close"]
            .iloc[-16]
        )

        recent_move = (
            close_now
            - close_5
        )

        previous_move = (
            close_5
            - close_15
        )

        if (
            recent_move > 0
            and previous_move < 0
            and raw_signal == "LOW"
        ):

            return (
                True,
                "SKIP_TREND_CHANGE",
                raw_signal,
                market,
            )

        if (
            recent_move < 0
            and previous_move > 0
            and raw_signal == "HIGH"
        ):

            return (
                True,
                "SKIP_TREND_CHANGE",
                raw_signal,
                market,
            )

    # =========================
    # MA接近
    # =========================

    ma_gap = abs(
        float(
            latest["MA5"]
        )
        - float(
            latest["MA20"]
        )
    )

    atr = float(
        latest["ATR"]
    )

    if (
        atr > 0
        and ma_gap
        < atr * 0.08
    ):

        return (
            True,
            "SKIP_MA_FLAT",
            raw_signal,
            market,
        )

    # =========================
    # 急激なボラ上昇
    # =========================

    atr_mean = market[
        "atr_mean"
    ]

    if (
        atr_mean > 0
        and atr
        > atr_mean * 1.8
        and confidence < 0.75
    ):

        return (
            True,
            "SKIP_VOLATILITY",
            raw_signal,
            market,
        )

    return (
        False,
        "",
        raw_signal,
        market,
    )
