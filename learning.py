"""
Market Assistant
learning.py
学習レポート
"""

import json
import os

STATE_FILE = "learning_state.json"
MILESTONES = [30, 100, 300, 600, 1000, 1500, 2000]


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"notified": [], "model_version": 1}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def calc_rate(df):
    if df.empty:
        return 0, 0, 0, 0.0

    total = len(df)
    wins = len(df[df["result"] == "WIN"])
    losses = len(df[df["result"] == "LOSE"])
    rate = wins / total * 100 if total else 0.0

    return total, wins, losses, rate


def make_learning_report(df, milestone):
    trade_df = df[df["result"] != "NO_TRADE"]

    total, wins, losses, rate = calc_rate(trade_df)

    text = f"""
🤖 Market Assistant 学習レポート

{milestone}戦 到達

累計 : {total}戦
勝ち : {wins}
負け : {losses}
勝率 : {rate:.1f}%
"""

    text += "\n📌 HIGH / LOW\n"

    for signal in ["HIGH", "LOW"]:
        sub = trade_df[trade_df["signal"] == signal]
        s_total, s_wins, s_losses, s_rate = calc_rate(sub)

        if s_total > 0:
            text += (
                f"{signal} : "
                f"{s_total}戦 "
                f"{s_wins}勝 "
                f"{s_losses}敗 "
                f"勝率{s_rate:.1f}%\n"
            )

    text += "\n次の節目まで学習を継続します。"

    return text


def check_learning(df):
    if df.empty:
        return None

    trade_df = df[df["result"] != "NO_TRADE"]
    trade_count = len(trade_df)

    state = load_state()
    notified = state.get("notified", [])

    for milestone in MILESTONES:
        if trade_count >= milestone and milestone not in notified:
            report = make_learning_report(df, milestone)

            notified.append(milestone)
            state["notified"] = notified
            save_state(state)

            return report

    return None
