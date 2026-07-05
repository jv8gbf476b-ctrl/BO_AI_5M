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


def confidence_band(confidence):
    confidence = float(confidence)

    if confidence >= 0.90:
        return "90%以上"
    if confidence >= 0.80:
        return "80〜90%"
    if confidence >= 0.70:
        return "70〜80%"
    if confidence >= 0.60:
        return "60〜70%"

    return "60%未満"


def confidence_analysis(df):
    if df.empty or "confidence" not in df.columns:
        return ""

    data = df.copy()
    data["band"] = data["confidence"].apply(confidence_band)

    text = "\n⭐ 信頼度別\n"

    for band in ["90%以上", "80〜90%", "70〜80%", "60〜70%", "
