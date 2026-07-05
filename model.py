"""
Market Assistant
model_store.py
モデル管理
"""

import os
import pickle
from datetime import datetime
from zoneinfo import ZoneInfo

MODEL_DIR = "models"
ARCHIVE_DIR = "models/archive"

CURRENT_MODEL = "models/current.pkl"
CANDIDATE_MODEL = "models/candidate.pkl"
BACKUP_MODEL = "models/backup.pkl"


def ensure_model_dirs():

    os.makedirs(
        MODEL_DIR,
        exist_ok=True,
    )

    os.makedirs(
        ARCHIVE_DIR,
        exist_ok=True,
    )


def save_pickle(path, obj):

    ensure_model_dirs()

    with open(
        path,
        "wb",
    ) as f:

        pickle.dump(
            obj,
            f,
        )


def load_pickle(path):

    if not os.path.exists(
        path
    ):
        return None

    with open(
        path,
        "rb",
    ) as f:

        return pickle.load(f)


def save_current_model(model):

    save_pickle(
        CURRENT_MODEL,
        model,
    )


def load_current_model():

    return load_pickle(
        CURRENT_MODEL
    )


def save_candidate_model(model):

    save_pickle(
        CANDIDATE_MODEL,
        model,
    )


def load_candidate_model():

    return load_pickle(
        CANDIDATE_MODEL
    )


def backup_current_model():

    current = load_current_model()

    if current is not None:

        save_pickle(
            BACKUP_MODEL,
            current,
        )


def promote_candidate_model():

    candidate = load_candidate_model()

    if candidate is None:
        return False

    backup_current_model()

    save_current_model(
        candidate
    )

    archive_current_model()

    return True


def archive_current_model():

    current = load_current_model()

    if current is None:
        return

    now = datetime.now(
        ZoneInfo("Asia/Tokyo")
    )

    filename = now.strftime(
        "model_%Y%m%d_%H%M%S.pkl"
    )

    path = os.path.join(
        ARCHIVE_DIR,
        filename,
    )

    save_pickle(
        path,
        current,
    )


def has_current_model():

    return os.path.exists(
        CURRENT_MODEL
    )
