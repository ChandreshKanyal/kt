"""
Package Trained Models into JoblibX
===================================
This script takes your already trained models and packages them into ensemble_model.joblib
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import boto3
from io import StringIO
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# Model Classes (Same as your final_anomaly_ensemble.py)
# ============================================================================

class TimeSeriesAnomalyModel:
    """Time series anomaly detection using IQR method"""
    
    def __init__(self, contamination=0.05):
        self.contamination = contamination
        self.threshold_low = None
        self.threshold_high = None
        
    def fit(self, data):
        Q1 = np.percentile(data, 25)
        Q3 = np.percentile(data, 75)
        IQR = Q3 - Q1
        self.threshold_low = Q1 - 1.5 * IQR
        self.threshold_high = Q3 + 1.5 * IQR
        return self
    
    def predict(self, data):
        return ((data < self.threshold_low) | (data > self.threshold_high)).astype(int)


class AnomalyDetectionEnsemble:
    """Ensemble of 3 models"""
    
    def __init__(self, contamination=0.05):
        self.contamination = contamination
        self.income_model = None
        self.passenger_model = None
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def fit(self, df):
        """Fit all three models"""
        print("Fitting Anomaly Detection Ensemble...")
        
        # Extract temporal features
        df['start_time'] = df['start_time'].astype(str).str.split('.').str[0]
        df['start_time'] = pd.to_datetime(df['start_time'], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df['month'] = df['start_time'].dt.month
        df['year'] = df['start_time'].dt.year
        df['day'] = df['start_time'].dt.day
        df['day_of_week'] = df['start_time'].dt.dayofweek
        
        # 1. Income model
        self.income_model = TimeSeriesAnomalyModel(contamination=self.contamination)
        self.income_model.fit(df['total_income'].values)
        print(f"✓ Income model trained: thresholds [{self.income_model.threshold_low:.2f}, {self.income_model.threshold_high:.2f}]")
        
        # 2. Passenger model
        self.passenger_model = TimeSeriesAnomalyModel(contamination=self.contamination)
        self.passenger_model.fit(df['total_passengers'].values)
        print(f"✓ Passenger model trained: thresholds [{self.passenger_model.threshold_low:.2f}, {self.passenger_model.threshold_high:.2f}]")
        
        # 3. Isolation Forest
        features = ['month', 'year', 'day', 'day_of_week', 'total_income', 'total_passengers']
        X = df[features].fillna(df[features].median())
        X_scaled = self.scaler.fit_transform(X)
        
        self.isolation_forest = IsolationForest(
            contamination=self.contamination, 
            random_state=42, 
            n_estimators=100
        )
        self.isolation_forest.fit(X_scaled)
        print(f"✓ Isolation Forest trained: {self.isolation_forest.n_estimators} estimators")
        
        self.is_fitted = True
        return self
    
    def predict(self, df):
        """Predict anomalies"""
        df = df.copy()
        df['start_time'] = df['start_time'].astype(str).str.split('.').str[0]
        df['start_time'] = pd.to_datetime(df['start_time'], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df['month'] = df['start_time'].dt.month
        df['year'] = df['start_time'].dt.year
        df['day'] = df['start_time'].dt.day
        df['day_of_week'] = df['start_time'].dt.dayofweek
        
        # Get predictions
        income_anomalies = self.income_model.predict(df['total_income'].values)
        passenger_anomalies = self.passenger_model.predict(df['total_passengers'].values)
        
        features = ['month', 'year', 'day', 'day_of_week', 'total_income', 'total_passengers']
        X = df[features].fillna(df[features].median())
        X_scaled = self.scaler.transform(X)
        iso_predictions = self.isolation_forest.predict(X_scaled)
        iso_anomalies = (iso_predictions == -1).astype(int)
        
        # Ensemble voting
        ensemble_scores = income_anomalies + passenger_anomalies + iso_anomalies
        ensemble_anomalies = (ensemble_scores >= 2).astype(int)
        
        df['income_anomaly'] = income_anomalies
        df['passenger_anomaly'] = passenger_anomalies
        df['iso_anomaly'] = iso_anomalies
        df['ensemble_score'] = ensemble_scores
        df['ensemble_anomaly'] = ensemble_anomalies
        
        return df


# ============================================================================
# PACKAGE MODELS INTO JOBLIB
# ============================================================================

def package_models_to_joblib():
    """
    Package trained models into ensemble_model.joblib
    """
    print("\n" + "="*70)
    print("PACKAGING MODELS INTO JOBLIB")
    print("="*70)
    
    # Configuration
    S3_BUCKET = "test-airflow-chan"
    S3_KEY = "data/top_10.csv000"
    OUTPUT_FILE = "ensemble_model.joblib"
    
    # Load data
    print(f"\nLoading training data from S3...")
    print(f"Bucket: {S3_BUCKET}")
    print(f"Key: {S3_KEY}")
    
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    df = pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))
    print(f"✓ Loaded {len(df):,} transactions\n")
    
    # Train ensemble (all 3 models)
    ensemble = AnomalyDetectionEnsemble(contamination=0.05)
    ensemble.fit(df)
    
    # Save to joblib
    print(f"\n{'='*70}")
    print("SAVING TO JOBLIB")
    print("="*70)
    print(f"\nOutput file: {OUTPUT_FILE}")
    joblib.dump(ensemble, OUTPUT_FILE)
    print(f"✓ Saved successfully")
    
    # Verify
    print("\nVerifying...")
    loaded = joblib.load(OUTPUT_FILE)
    print(f"✓ File can be loaded")
    print(f"✓ Is fitted: {loaded.is_fitted}")
    print(f"✓ Contains 3 models:")
    print(f"  - Income model: {loaded.income_model is not None}")
    print(f"  - Passenger model: {loaded.passenger_model is not None}")
    print(f"  - Isolation Forest: {loaded.isolation_forest is not None}")
    
    print("\n" + "="*70)
    print("✓ PACKAGING COMPLETE")
    print("="*70)
    print(f"✓ Output: {OUTPUT_FILE}")
    print("✓ Ready for production use")
    print("="*70 + "\n")


if __name__ == "__main__":
    package_models_to_joblib()