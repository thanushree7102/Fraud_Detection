"""Streamlit dashboard.  Run with:  streamlit run dashboard.py"""
import json

import altair as alt
import pandas as pd
import streamlit as st

from config import DASHBOARD_DATA_PATH

st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide")
st.title("Real-Time Fraud Detection Dashboard")


def load_data() -> list:
    try:
        with open(DASHBOARD_DATA_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# A fragment re-runs on its own every 3 seconds, without blocking the app
# in a `while True` loop like the original did.
@st.fragment(run_every=3)
def live_view() -> None:
    data = load_data()
    if not data:
        st.info("No transactions yet. Start consumer.py and producer.py.")
        return

    df = pd.DataFrame(data)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Transactions", len(df))
    c2.metric("Fraudulent Transactions", int(df["isFraud"].sum()))
    c3.metric("Avg Fraud Probability", f"{df['fraud_probability'].mean():.2%}")

    st.subheader("Recent Transactions")
    st.dataframe(
        df[["step", "type", "amount", "isFraud", "fraud_probability"]][::-1].head(10)
    )

    counts = (
        df.assign(status=df["isFraud"].map({0: "Legit", 1: "Fraud"}))
        .groupby("status")
        .size()
        .reset_index(name="Count")
    )
    chart = (
        alt.Chart(counts)
        .mark_bar()
        .encode(
            x=alt.X("status:N", title="Status"),
            y=alt.Y("Count:Q", title="Number of Transactions"),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(domain=["Legit", "Fraud"], range=["#4c78a8", "#e45756"]),
                legend=None,
            ),
        )
        .properties(title="Fraud vs Non-Fraud Transactions", width="container")
    )
    st.altair_chart(chart)


live_view()
