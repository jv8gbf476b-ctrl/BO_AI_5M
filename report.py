"""
BO_AI_5M
report.py
"""

from history import load_history


def make_report_text():

    df = load_history()

    if df.empty:
        return "📊 成績: まだ記録なし"

    trade_df = df[
        df["result"] != "NO_TRADE"
    ]

    total = len(trade_df)

    wins = len(
        trade_df[
            trade_df["result"] == "WIN"
        ]
    )

    losses = len(
        trade_df[
            trade_df["result"] == "LOSE"
        ]
    )

    skips = len(
        df[
            df["result"] == "NO_TRADE"
        ]
    )

    if total == 0:
        win_rate = 0

    else:
        win_rate = wins / total * 100

    text = f"""
📊 BO_AI_5M 成績

エントリー : {total}戦

勝ち : {wins}

負け : {losses}

勝率 : {win_rate:.1f}%

見送り : {skips}回
"""

    for signal in ["HIGH", "LOW"]:

        sub = trade_df[
            trade_df["signal"] == signal
        ]

        if sub.empty:
            continue

        s_total = len(sub)

        s_win = len(
            sub[
                sub["result"] == "WIN"
            ]
        )

        s_rate = s_win / s_total * 100

        text += (
            f"\n{signal} : "
            f"{s_total}戦 "
            f"{s_win}勝 "
            f"勝率{s_rate:.1f}%"
        )

    return text
