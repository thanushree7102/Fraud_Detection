from kafka import KafkaProducer
import json
import time
import pandas as pd

try:
    # Load dataset
    df = pd.read_csv("Synthetic_Financial_datasets_log.csv")
    transactions = df[['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig', 'nameDest']].to_dict('records')
    
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    # Send transactions
    for transaction in transactions[:50]:  # Limit to 50 for quick testing
        print(f"Sending: {transaction}")
        producer.send('fraud_transactions', transaction)
        producer.flush()
        time.sleep(0.5)  # Faster for testing
    print("✅ All transactions sent.")
except Exception as e:
    print(f"❌ Error in producer: {e}")