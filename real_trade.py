"""
BO_AI_5M
real_trade.py
実トレード採点モード
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yfinance as yf

TICKER = "JPY=X"
PENDING_FILE = "real_pending.json"
HISTORY_FILE = "real_history.csv"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=20,
    ).raise_for_status()


def get_price():
    df = yf.download(
        TICKER,
        period="1d",
        interval="1m",
        auto_adjust=False,
        progress=False,
    )

    if df.empty:
        raise RuntimeError("価格取得失敗")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    latest = df.dropna().iloc[-1]
    return float(latest["Close"])


def load_pending():
    if not os.path.exists(PENDING_FILE):
        return None

    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_pending(data):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clear_pending():
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)


def append_history(row):
    df = pd.DataFrame([row])

    if os.path.exists(HISTORY_FILE):
        df.to_csv(HISTORY_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(HISTORY_FILE, index=False)


def make_report():
    if not os.path.exists(HISTORY_FILE):
        return "📊 実トレ成績: まだ記録なし"

    df = pd.read_csv(HISTORY_FILE)

    total = len(df)
    wins = len(df[df["result"] == "WIN"])
    losses = len(df[df["result"] == "LOSE"])
    rate = wins / total * 100 if total else 0

    text = f"""
📊 BO_AI_5M 実トレ成績

累計 : {total}戦
勝ち : {wins}
負け : {losses}
勝率 : {rate:.1f}%
"""

    for direction in ["HIGH", "LOW"]:
        sub = df[df["direction"] == direction]

        if sub.empty:
            continue

        s_total = len(sub)
        s_wins = len(sub[sub["result"] == "WIN"])
        s_rate = s_wins / s_total * 100

        text += f"\n{direction} : {s_total}戦 {s_wins}勝 勝率{s_rate:.1f}%"

    return text


def start_trade(direction):
    direction = direction.upper()

    if direction not in ["HIGH", "LOW"]:
        raise ValueError("direction は HIGH または LOW")

    if load_pending():
        send_telegram("⚠️ まだ判定待ちの実トレがあります")
        return

    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    price = get_price()

    trade_id = now.strftime("%Y%m%d_%H%M%S")

    save_pending({
        "id": trade_id,
        "direction": direction,
        "entry_time": now.isoformat(),
        "entry_price": price,
    })

    send_telegram(f"""
🎯 BO_AI_5M 実トレ開始

ID : {trade_id}

方向 : {direction}
開始時刻 : {now.strftime("%Y-%m-%d %H:%M:%S")}
開始価格 : {price:.3f}

5分後に判定
""")


def check_trade():
    pending = load_pending()

    if not pending:
        print("判定待ちなし")
        return

    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    entry_time = datetime.fromisoformat(pending["entry_time"])

    elapsed = (now - entry_time).total_seconds()

    if elapsed < 300:
        print("まだ5分経過していません")
        return

    entry_price = float(pending["entry_price"])
    result_price = get_price()
    direction = pending["direction"]

    if result_price > entry_price:
        actual = "HIGH"
    elif result_price < entry_price:
        actual = "LOW"
    else:
        actual = "FLAT"

    win = direction == actual
    result = "WIN" if win else "LOSE"

    append_history({
        "id": pending["id"],
        "direction": direction,
        "actual": actual,
        "entry_time": pending["entry_time"],
        "judge_time": now.isoformat(),
        "entry_price": entry_price,
        "result_price": result_price,
        "price_diff": round(result_price - entry_price, 6),
        "result": result,
    })

    report = make_report()

    send_telegram(f"""
📊 BO_AI_5M 実トレ判定

ID : {pending["id"]}

方向 : {direction}
実際 : {actual}

開始価格 : {entry_price:.3f}
判定価格 : {result_price:.3f}
価格差 : {result_price - entry_price:+.3f}

結果 : {"✅ 勝ち" if win else "❌ 負け"}

{report}
""")

    clear_pending()


def main():
    direction = os.getenv("REAL_DIRECTION", "").upper()

    if direction in ["HIGH", "LOW"]:
        start_trade(direction)
    else:
        check_trade()


if __name__ == "__main__":
    main()
