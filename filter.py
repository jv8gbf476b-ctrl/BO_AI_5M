"""
Market Assistant
filter.py
転換期SKIPフィルター
"""


def get_raw_signal(up_prob, down_prob):

    if up_prob >= down_prob:
        return "HIGH"

    return "LOW"


def detect_skip_filter(data, result):

    up_prob = result["up_prob"]
    down_prob = result["down_prob"]

    confidence = result["confidence"]
    edge = abs(up_prob - down_prob)

    raw_signal = get_raw_signal(
        up_prob,
        down_prob,
    )

    latest = data.iloc[-1]

    # 期待値差がかなり小さい時だけSKIP
    if edge < 0.05:
        return True, "SKIP_WEAK_EDGE", raw_signal

    # 直近の方向転換を検知
    if len(data) >= 20:

        close_now = float(data["Close"].iloc[-1])
        close_5 = float(data["Close"].iloc[-6])
        close_15 = float(data["Close"].iloc[-16])

        recent_move = close_now - close_5
        previous_move = close_5 - close_15

        if recent_move > 0 and previous_move < 0:
            if raw_signal == "LOW":
                return True, "SKIP_TREND_CHANGE", raw_signal

        if recent_move < 0 and previous_move > 0:
            if raw_signal == "HIGH":
                return True, "SKIP_TREND_CHANGE", raw_signal

    # 移動平均がかなり接近している時だけSKIP
    ma_gap = abs(
        float(latest["MA5"])
        - float(latest["MA20"])
    )

    atr = float(latest["ATR"])

    if atr > 0 and ma_gap < atr * 0.08:
        return True, "SKIP_MA_FLAT", raw_signal

    # ボラ急変時は見送り
    if "ATR" in data.columns and len(data) >= 30:

        atr_mean = float(
            data["ATR"]
            .tail(30)
            .mean()
        )

        if atr_mean > 0 and atr > atr_mean * 1.8:
            if confidence < 0.75:
                return True, "SKIP_VOLATILITY", raw_signal

    return False, "", raw_signal
