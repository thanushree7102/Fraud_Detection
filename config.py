"""Shared settings for the fraud detection pipeline.

All paths are relative to this folder, so the scripts work no matter which
directory you launch them from.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_PATH = os.environ.get(
    "FRAUD_DATASET", os.path.join(BASE_DIR, "Synthetic_Financial_datasets_log.csv")
)
MODEL_PATH = os.path.join(BASE_DIR, "fraud_model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "label_encoder.pkl")
DASHBOARD_DATA_PATH = os.path.join(BASE_DIR, "dashboard_data.json")

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "fraud_transactions")

FEATURES = ["type", "amount", "oldbalanceOrg", "newbalanceOrig"]
MAX_DASHBOARD_ROWS = 50
