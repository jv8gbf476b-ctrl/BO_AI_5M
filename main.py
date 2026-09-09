"""
Market Assistant
main.py

ZERO v0.1
学習・予測・相場情報保存
"""

from data import load_data

from features import (
    build_features,
)

from model import (
    get_model,
    predict_latest,
)

from pending import (
    load_pending,
    save_pending,
)

from grading import (
    grade_pending,
)

from history import (
    load_history,
)

from learning import (
    check_learning,
)

from improver import (
    improve_model,
)

from telegram_bot import (
    send_telegram,
)

from filter import (
    detect_skip_filter,
)

from config import (
    ENABLE_SIGNAL_NOTIFICATION,
    ENABLE_LEARNING_NOTIFICATION,
)


def save_signal(
    data,
    result,
):

    latest = data.iloc[-1]

    latest_time = (
        data.index[-1]
    )

    (
        skip,
        skip_reason,
        raw_signal,
        market,
    ) = detect_skip_filter(
        data,
        result,
    )

    signal = (
        "SKIP"
        if skip
        else raw_signal
    )

    edge = abs(
        result["up_prob"]
        - result["down_prob"]
    )

    payload = {

        # =====================
        # 基本
        # =====================

        "id": (
            latest_time
            .strftime(
                "%Y%m%d_%H%M"
            )
        ),

        "entry_time": (
            latest_time
            .isoformat()
        ),

        "entry_time_jst": (
            latest_time
            .tz_convert(
                "Asia/Tokyo"
            )
            .isoformat()
        ),

        "entry_close": float(
            latest["Close"]
        ),

        # =====================
        # 判定
        # =====================

        "signal": signal,

        "raw_signal": (
            raw_signal
        ),

        "skip_reason": (
            skip_reason
        ),

        "up_prob": float(
            result["up_prob"]
        ),

        "down_prob": float(
            result["down_prob"]
        ),

        "confidence": float(
            result["confidence"]
        ),

        "edge": float(
            edge
        ),

        # =====================
        # ZERO相場状態
        # =====================

        "market_trend": (
            market["trend"]
        ),

        "market_volatility": (
            market[
                "volatility"
            ]
        ),

        # =====================
        # 特徴量
        # =====================

        "Open": float(
            latest["Open"]
        ),

        "High": float(
            latest["High"]
        ),

        "Low": float(
            latest["Low"]
        ),

        "Close": float(
            latest["Close"]
        ),

        "MA5": float(
            latest["MA5"]
        ),

        "MA10": float(
            latest["MA10"]
        ),

        "MA20": float(
            latest["MA20"]
        ),

        "EMA20": float(
            latest["EMA20"]
        ),

        "EMA50": float(
            latest["EMA50"]
        ),

        "Return": float(
            latest["Return"]
        ),

        "Return3": float(
            latest["Return3"]
        ),

        "Return5": float(
            latest["Return5"]
        ),

        "RSI": float(
            latest["RSI"]
        ),

        "ATR": float(
            latest["ATR"]
        ),

        "Hour": int(
            latest["Hour"]
        ),

        "DayOfWeek": int(
            latest[
                "DayOfWeek"
            ]
        ),
    }

    save_pending(
        payload
    )

    print(
        "saved "
        "pending_signal.json"
    )

    print(
        "id:",
        payload["id"],
    )

    print(
        "signal:",
        signal,
    )

    print(
        "raw_signal:",
        raw_signal,
    )

    print(
        "skip_reason:",
        skip_reason,
    )

    print(
        "trend:",
        market["trend"],
    )

    print(
        "volatility:",
        market["volatility"],
    )

    print(
        "close:",
        payload[
            "entry_close"
        ],
    )

    if ENABLE_SIGNAL_NOTIFICATION:

        send_telegram(
            f"""
🤖 ZERO Market Assistant

判定 : {signal}
元判定 : {raw_signal}

相場 : {market["trend"]}
ボラ : {market["volatility"]}

SKIP理由 :
{skip_reason if skip_reason else "なし"}

HIGH : {result["up_prob"]*100:.2f}%
LOW : {result["down_prob"]*100:.2f}%

AI信頼度 :
{result["confidence"]*100:.2f}%

判定差 :
{edge*100:.2f}pt

RSI :
{float(latest["RSI"]):.2f}
"""
        )


def main():

    print(
        "START ZERO "
        "Market Assistant"
    )

    # =========================
    # データ取得
    # =========================

    data = load_data()

    print(
        "data loaded:",
        len(data),
    )

    # =========================
    # 特徴量
    # =========================

    data = build_features(
        data
    )

    print(
        "features built:",
        len(data),
    )

    latest_time = (
        data.index[-1]
    )

    print(
        "latest time:",
        latest_time,
    )

    # =========================
    # 前回判定の採点
    # =========================

    pending = (
        load_pending()
    )

    print(
        "pending:",
        pending["id"]
        if pending
        else "none",
    )

    if pending:

        data = grade_pending(
            data,
            pending,
        )

        print(
            "grading checked"
        )

    # =========================
    # 自己改善
    # =========================

    improved = (
        improve_model(
            data
        )
    )

    print(
        "improved:",
        improved,
    )

    # =========================
    # モデル
    # =========================

    model = get_model(
        data
    )

    print(
        "model ready"
    )

    # =========================
    # 最新予測
    # =========================

    result = (
        predict_latest(
            model,
            data,
        )
    )

    print(
        "prediction:",
        result,
    )

    # =========================
    # 保存
    # =========================

    save_signal(
        data,
        result,
    )

    # =========================
    # 改善通知
    # =========================

    if improved:

        send_telegram(
            """
🤖 ZERO Market Assistant

自己改善モデルを更新しました。

未来側データで検証を通過した
モデルを採用しました。
"""
        )

    # =========================
    # 学習レポート
    # =========================

    if ENABLE_LEARNING_NOTIFICATION:

        history = (
            load_history()
        )

        print(
            "history rows:",
            len(history),
        )

        learning_report = (
            check_learning(
                history
            )
        )

        if learning_report:

            send_telegram(
                learning_report
            )

            print(
                "learning "
                "report sent"
            )

    print(
        "END ZERO "
        "Market Assistant"
    )


if __name__ == "__main__":
    main()
