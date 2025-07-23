from kafka import KafkaConsumer
import json
import pickle
import pandas as pd
import threading
import os

try:
    # Load model and encoder
    with open('fraud_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('label_encoder.pkl', 'rb') as f:
        le = pickle.load(f)
    print("✅ Model and encoder loaded.")

    # Initialize Kafka Consumer
    consumer = KafkaConsumer(
        'fraud_transactions',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='fraud-detection-group'
    )
    print("✅ Kafka consumer is running...")

    # Initialize file lock
    lock = threading.Lock()

    for message in consumer:
        transaction = message.value
        print(f"📥 Received: {transaction}")
        
        # Prepare data for prediction
        data = pd.DataFrame([transaction])
        data['type'] = le.transform(data['type'])
        X = data[['type', 'amount', 'oldbalanceOrg', 'newbalanceOrig']]
        
        # Predict fraud
        prediction = model.predict(X)[0]
        probability = model.predict_proba(X)[0][1]
        
        # Save results
        transaction_record = transaction.copy()
        transaction_record['isFraud'] = int(prediction)
        transaction_record['fraud_probability'] = float(probability)
        
        with lock:
            dashboard_data = []
            if os.path.exists('dashboard_data.json'):
                with open('dashboard_data.json', 'r') as f:
                    dashboard_data = json.load(f)
            dashboard_data.append(transaction_record)
            dashboard_data = dashboard_data[-50:]  # Keep last 50
            with open('dashboard_data.json', 'w') as f:
                json.dump(dashboard_data, f, indent=2)
            print("📊 Saved to dashboard_data.json")
except Exception as e:
    print(f"❌ Error in consumer: {e}")