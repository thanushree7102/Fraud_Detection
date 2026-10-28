"""Read transactions from Kafka, predict fraud, write results for the dashboard.

Optional email alerts: set these environment variables before starting.
    ALERT_SMTP_HOST   e.g. smtp.gmail.com
    ALERT_SMTP_PORT   default 587
    ALERT_SMTP_USER   login (for Gmail use an App Password, not your normal one)
    ALERT_SMTP_PASS
    ALERT_TO          recipient address
Without them, fraud is only printed to the console.
"""
import json
import os
import pickle
import smtplib
import sys
from collections import deque
from email.message import EmailMessage

import pandas as pd

from config import (
    DASHBOARD_DATA_PATH,
    ENCODER_PATH,
    FEATURES,
    KAFKA_BOOTSTRAP,
    KAFKA_TOPIC,
    MAX_DASHBOARD_ROWS,
    MODEL_PATH,
)


def predict_transaction(transaction: dict, model, le) -> dict:
    """Return the transaction plus isFraud and fraud_probability."""
    data = pd.DataFrame([transaction])
    data["type"] = le.transform(data["type"])
    X = data[FEATURES]
    record = dict(transaction)
    record["isFraud"] = int(model.predict(X)[0])
    record["fraud_probability"] = float(model.predict_proba(X)[0][1])
    return record


def save_dashboard_data(records, path: str = DASHBOARD_DATA_PATH) -> None:
    """Write atomically so the dashboard never reads a half-written file."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(list(records), f, indent=2)
    os.replace(tmp, path)


def load_existing(path: str = DASHBOARD_DATA_PATH) -> deque:
    try:
        with open(path) as f:
            return deque(json.load(f), maxlen=MAX_DASHBOARD_ROWS)
    except (FileNotFoundError, json.JSONDecodeError):
        return deque(maxlen=MAX_DASHBOARD_ROWS)


def send_email_alert(record: dict) -> None:
    host = os.environ.get("ALERT_SMTP_HOST")
    to = os.environ.get("ALERT_TO")
    if not host or not to:
        return
    msg = EmailMessage()
    msg["Subject"] = f"FRAUD ALERT: {record['type']} of {record['amount']:,.2f}"
    msg["From"] = os.environ.get("ALERT_SMTP_USER", "fraud-alerts@localhost")
    msg["To"] = to
    msg.set_content(
        "A transaction was predicted as fraudulent.\n\n"
        + "\n".join(f"{k}: {v}" for k, v in record.items())
    )
    try:
        with smtplib.SMTP(host, int(os.environ.get("ALERT_SMTP_PORT", "587")), timeout=15) as s:
            s.starttls()
            if os.environ.get("ALERT_SMTP_USER"):
                s.login(os.environ["ALERT_SMTP_USER"], os.environ.get("ALERT_SMTP_PASS", ""))
            s.send_message(msg)
        print("  email alert sent")
    except Exception as e:  # never let a mail problem stop the consumer
        print(f"  email alert failed: {e}")


def main() -> int:
    for p in (MODEL_PATH, ENCODER_PATH):
        if not os.path.exists(p):
            print(f"ERROR: {p} not found. Run `python train_model.py` first.")
            return 1
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(ENCODER_PATH, "rb") as f:
        le = pickle.load(f)
    print("Model and encoder loaded.")

    from kafka import KafkaConsumer
    from kafka.errors import NoBrokersAvailable

    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            group_id="fraud-detection-group",
        )
    except NoBrokersAvailable:
        print(f"ERROR: cannot reach Kafka at {KAFKA_BOOTSTRAP}.")
        print("Start it first:  docker compose up -d")
        return 1
    print(f"Listening on topic '{KAFKA_TOPIC}' (Ctrl+C to stop)...")

    records = load_existing()
    try:
        for message in consumer:
            try:
                record = predict_transaction(message.value, model, le)
            except Exception as e:  # one bad message must not kill the consumer
                print(f"Skipping bad message {message.value!r}: {e}")
                continue
            records.append(record)
            save_dashboard_data(records)
            flag = "FRAUD" if record["isFraud"] else "ok"
            print(f"{flag:5} p={record['fraud_probability']:.2f} {record['type']} {record['amount']:,.2f}")
            if record["isFraud"]:
                send_email_alert(record)
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
