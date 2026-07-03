"""
Market Assistant
model_store.py
モデル管理
"""

import os
import pickle

MODEL_DIR = "models"
CURRENT_MODEL = "models/current.pkl"


def ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)


def save_current_model(model):
    ensure_model_dir()

    with open(CURRENT_MODEL, "wb") as f:
        pickle.dump(model, f)


def load_current_model():
    if not os.path.exists(CURRENT_MODEL):
        return None

    with open(CURRENT_MODEL, "rb") as f:
        return pickle.load(f)


def has_current_model():
    return os.path.exists(CURRENT_MODEL)
