"""Train the fraud model and save fraud_model.pkl + label_encoder.pkl."""
import os
import pickle
import sys

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from config import DATASET_PATH, ENCODER_PATH, FEATURES, MODEL_PATH


def main() -> int:
    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: dataset not found: {DATASET_PATH}")
        print("Download Synthetic_Financial_datasets_log.csv from Kaggle (see HOW_TO_RUN.md)")
        print("and put it in the same folder as this script.")
        return 1

    df = pd.read_csv(DATASET_PATH, usecols=FEATURES + ["isFraud"])
    df = df.dropna()

    le = LabelEncoder()
    df["type"] = le.fit_transform(df["type"])

    X = df[FEATURES]
    y = df["isFraud"]

    # Hold out 20% so the reported accuracy is honest (fraud is very rare, so stratify).
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=50,
        min_samples_leaf=3,          # keeps the pickle file small on the 6M-row dataset
        class_weight="balanced_subsample",  # fraud is <1% of rows
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train, y_train)

    print("Test-set results (20% held out):")
    print(confusion_matrix(y_test, model.predict(X_test)))
    print(classification_report(y_test, model.predict(X_test), digits=4))

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(ENCODER_PATH, "wb") as f:
        pickle.dump(le, f)
    print(f"Saved: {MODEL_PATH}\n       {ENCODER_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
