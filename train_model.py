import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pickle
import warnings
warnings.filterwarnings("ignore")

try:
    # Load dataset
    df = pd.read_csv("Synthetic_Financial_datasets_log.csv")
    
    # Preprocess data
    df = df[['type', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'isFraud']]
    le = LabelEncoder()
    df['type'] = le.fit_transform(df['type'])
    
    # Features and target
    X = df.drop('isFraud', axis=1)
    y = df['isFraud']
    
    # Train Random Forest
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    # Save model and encoder
    with open('fraud_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('label_encoder.pkl', 'wb') as f:
        pickle.dump(le, f)
    
    print("✅ Model and encoder saved: fraud_model.pkl, label_encoder.pkl")
except Exception as e:
    print(f"❌ Error in training: {e}")