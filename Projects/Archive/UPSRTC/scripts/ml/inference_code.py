import pandas as pd
import numpy as np
import joblib
import boto3
from io import StringIO
import warnings
warnings.filterwarnings('ignore')

# 🔴 THIS IMPORT IS MANDATORY
from ensemble_model import AnomalyDetectionEnsemble, TimeSeriesAnomalyModel


def run_inference():
    print("\n" + "=" * 70)
    print("RUNNING PRODUCTION INFERENCE (NO TRAINING)")
    print("=" * 70)

    MODEL_PATH = "ensemble_model.joblib"

    S3_BUCKET = "test-airflow-chan"
    S3_KEY = "data/trial.csv"

    # Load model
    print("\nLoading trained model...")
    model = joblib.load(MODEL_PATH)
    print("✓ Model loaded")
    print(f"✓ Is fitted: {model.is_fitted}")

    # Load inference data
    print("\nLoading inference data from S3...")
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    df = pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))
    print(f"✓ Loaded {len(df):,} rows")

    # Run inference
    print("\nRunning anomaly detection...")
    results = model.predict(df)

    # Summary
    total = len(results)
    anomalies = results['ensemble_anomaly'].sum()

    print("\n" + "=" * 70)
    print("INFERENCE RESULTS")
    print("=" * 70)
    print(f"Total records:        {total:,}")
    print(f"Anomalies detected:   {anomalies:,} ({anomalies/total*100:.2f}%)")
    print(f"Income anomalies:     {results['income_anomaly'].sum():,}")
    print(f"Passenger anomalies:  {results['passenger_anomaly'].sum():,}")
    print(f"Isolation anomalies:  {results['iso_anomaly'].sum():,}")
    print("=" * 70)

    results.to_csv("inference_output.csv", index=False)
    print("\n✓ Results saved to inference_output.csv")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_inference()
