"""
BO_AI_5M
pending.py
"""

import json
import os

from config import PENDING_FILE


def load_pending():

    if not os.path.exists(PENDING_FILE):
        return None

    with open(
        PENDING_FILE,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def save_pending(data):

    with open(
        PENDING_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )


def clear_pending():

    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)
