"""Send sample transactions to Kafka.

Usage:  python producer.py [--count 50] [--delay 0.5]

The original script sent the first 50 rows of the CSV, which are almost all
legitimate, so the dashboard never showed any fraud. This one samples a mix
(about 20% fraud) so you can see the model working.
"""
import argparse
import json
import os
import sys
import time

import pandas as pd

from config import DATASET_PATH, KAFKA_BOOTSTRAP, KAFKA_TOPIC

COLUMNS = ["step", "type", "amount", "nameOrig", "oldbalanceOrg", "newbalanceOrig", "nameDest"]


def pick_transactions(count: int, fraud_share: float = 0.2) -> list:
    """Read the CSV in chunks and collect a mix of fraud / legit rows."""
    want_fraud = max(1, int(count * fraud_share))
    want_legit = count - want_fraud
    fraud_rows, legit_rows = [], []

    for chunk in pd.read_csv(DATASET_PATH, usecols=COLUMNS + ["isFraud"], chunksize=200_000):
        f = chunk[chunk["isFraud"] == 1]
        l = chunk[chunk["isFraud"] == 0]
        fraud_rows.append(f.sample(min(len(f), want_fraud), random_state=1))
        legit_rows.append(l.sample(min(len(l), want_legit), random_state=1))
        if sum(map(len, fraud_rows)) >= want_fraud and sum(map(len, legit_rows)) >= want_legit:
            break

    mixed = pd.concat(
        [pd.concat(fraud_rows).head(want_fraud), pd.concat(legit_rows).head(want_legit)]
    ).sample(frac=1, random_state=7)
    return mixed[COLUMNS].to_dict("records")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--delay", type=float, default=0.5, help="seconds between messages")
    args = parser.parse_args()

    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: dataset not found: {DATASET_PATH}")
        print("Download it from Kaggle (see HOW_TO_RUN.md) and put it in this folder.")
        return 1

    from kafka import KafkaProducer
    from kafka.errors import NoBrokersAvailable

    transactions = pick_transactions(args.count)

    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    except NoBrokersAvailable:
        print(f"ERROR: cannot reach Kafka at {KAFKA_BOOTSTRAP}.")
        print("Start it first:  docker compose up -d")
        return 1

    for i, tx in enumerate(transactions, 1):
        producer.send(KAFKA_TOPIC, tx)
        producer.flush()
        print(f"[{i}/{len(transactions)}] sent: {tx}")
        time.sleep(args.delay)
    print("All transactions sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
