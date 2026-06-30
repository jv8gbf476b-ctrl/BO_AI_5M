"""
BO_AI_5M
history.py
"""

import os
import pandas as pd

from config import HISTORY_FILE


def load_history():

    if not os.path.exists(
        HISTORY_FILE
    ):
        return pd.DataFrame()

    return pd.read_csv(
        HISTORY_FILE
    )


def append_history(row):

    df = load_history()

    df = pd.concat(
        [
            df,
            pd.DataFrame([row]),
        ],
        ignore_index=True,
    )

    df.to_csv(
        HISTORY_FILE,
        index=False,
    )
