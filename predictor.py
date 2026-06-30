"""
BO_AI_5M
predictor.py
"""

from features import build_features
from model import train_model
from model import predict_signal


def run_prediction(data):

    data = build_features(data)

    model = train_model(data)

    result = predict_signal(
        model,
        data,
    )

    return result
