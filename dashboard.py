import streamlit as st
import pandas as pd
import json
import time
import altair as alt

st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide")
st.title("Real-Time Fraud Detection Dashboard")

placeholder = st.empty()

while True:
    try:
        with open('dashboard_data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
        st.info("No transactions yet...")

    if data:
        df = pd.DataFrame(data)
        
        with placeholder.container():
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Transactions", len(df))
            col2.metric("Fraudulent Transactions", df['isFraud'].sum())
            col3.metric("Avg Fraud Probability", f"{df['fraud_probability'].mean():.2%}")
            
            st.subheader("Recent Transactions")
            st.dataframe(df[['step', 'type', 'amount', 'isFraud', 'fraud_probability']][::-1].head(10))
            
            # Bar chart for fraud counts
            fraud_counts = df.groupby('isFraud').size().reset_index(name='Count')
            chart = alt.Chart(fraud_counts).mark_bar().encode(
                x=alt.X('isFraud:N', title='Fraud Status (0 = No, 1 = Yes)'),
                y=alt.Y('Count:Q', title='Number of Transactions'),
                color=alt.Color('isFraud:N', title='Fraud Status')
            ).properties(title="Fraud vs Non-Fraud Transactions")
            st.altair_chart(chart, use_container_width=True)
    
    time.sleep(3)  # Refresh every 3 seconds