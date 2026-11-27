import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

class AnomalyDetectionEnsemble:
    """
    Ensemble anomaly detection system with:
    1. Time series anomaly model for total_income
    2. Time series anomaly model for total_passengers  
    3. Isolation Forest for all features (month, year, day, day_of_week, total_income, total_passengers)
    """
    
    def __init__(self, contamination=0.05):
        self.contamination = contamination
        self.income_model = None
        self.passenger_model = None
        self.isolation_forest = None
        self.scaler = StandardScaler()
        
    def fit(self, df):
        """Fit all three models"""
        print("Fitting Anomaly Detection Ensemble...")
        
        # Extract temporal features
        #df['start_time'] = pd.to_datetime(df['start_time'])
        # Remove fractional seconds if they exist
        df['start_time'] = df['start_time'].astype(str).str.split('.').str[0]
        # Now parse safely
        df['start_time'] = pd.to_datetime(df['start_time'], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df['month'] = df['start_time'].dt.month
        df['year'] = df['start_time'].dt.year
        df['day'] = df['start_time'].dt.day
        df['day_of_week'] = df['start_time'].dt.dayofweek
        
        # 1. Time Series Model for total_income
        self.income_model = TimeSeriesAnomalyModel(contamination=self.contamination)
        self.income_model.fit(df['total_income'].values)
        
        # 2. Time Series Model for total_passengers
        self.passenger_model = TimeSeriesAnomalyModel(contamination=self.contamination)
        self.passenger_mode l.fit(df['total_passengers'].values)
        
        # 3. Isolation Forest for all features
        features = ['month', 'year', 'day', 'day_of_week', 'total_income', 'total_passengers']
        X = df[features].fillna(df[features].median())
        X_scaled = self.scaler.fit_transform(X)
        
        self.isolation_forest = IsolationForest(
            contamination=self.contamination, 
            random_state=42, 
            n_estimators=100
        )
        self.isolation_forest.fit(X_scaled)
        
        return self
    
    def predict(self, df):
        """Predict anomalies using ensemble voting"""
        # Extract temporal features
        df = df.copy()
        #df['start_time'] = pd.to_datetime(df['start_time'])
        # Remove fractional seconds if they exist
        df['start_time'] = df['start_time'].astype(str).str.split('.').str[0]
        # Now parse safely
        df['start_time'] = pd.to_datetime(df['start_time'], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df['month'] = df['start_time'].dt.month
        df['year'] = df['start_time'].dt.year
        df['day'] = df['start_time'].dt.day
        df['day_of_week'] = df['start_time'].dt.dayofweek
        
        # Get predictions from each model
        income_anomalies = self.income_model.predict(df['total_income'].values)
        passenger_anomalies = self.passenger_model.predict(df['total_passengers'].values)
        
        features = ['month', 'year', 'day', 'day_of_week', 'total_income', 'total_passengers']
        X = df[features].fillna(df[features].median())
        X_scaled = self.scaler.transform(X)
        iso_predictions = self.isolation_forest.predict(X_scaled)
        iso_anomalies = (iso_predictions == -1).astype(int)
        
        # Ensemble voting (majority vote)
        ensemble_scores = income_anomalies + passenger_anomalies + iso_anomalies
        ensemble_anomalies = (ensemble_scores >= 2).astype(int)
        
        return {
            'income_anomalies': income_anomalies,
            'passenger_anomalies': passenger_anomalies,
            'isolation_forest_anomalies': iso_anomalies,
            'ensemble_anomalies': ensemble_anomalies,
            'ensemble_scores': ensemble_scores
        }

class TimeSeriesAnomalyModel:
    """Time series anomaly detection using statistical methods"""
    
    def __init__(self, contamination=0.05):
        self.contamination = contamination
        self.threshold_low = None
        self.threshold_high = None
        
    def fit(self, data):
        """Fit using IQR method for robust anomaly detection"""
        Q1 = np.percentile(data, 25)
        Q3 = np.percentile(data, 75)
        IQR = Q3 - Q1
        
        # Use IQR method with 1.5 * IQR as threshold
        self.threshold_low = Q1 - 1.5 * IQR
        self.threshold_high = Q3 + 1.5 * IQR
        
        return self
    
    def predict(self, data):
        """Predict anomalies"""
        return ((data < self.threshold_low) | (data > self.threshold_high)).astype(int)

# Load and process data
import boto3
import pandas as pd
from io import StringIO

# S3 details
bucket = "test-airflow-chan"
key = "data/top_10.csv000"

# Create S3 client
s3 = boto3.client("s3")

# Download file object
obj = s3.get_object(Bucket=bucket, Key=key)

# Download file object
print("Loading data...")
df = pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))

# Initialize and fit ensemble
ensemble = AnomalyDetectionEnsemble(contamination=0.05)
ensemble.fit(df)

# Get predictions
predictions = ensemble.predict(df)

# Create results dataframe
results_df = df.copy()
results_df['start_time'] = pd.to_datetime(results_df['start_time'])
# Remove fractional seconds if they exist
results_df['start_time'] = df['start_time'].astype(str).str.split('.').str[0]
        # Now parse safely
results_df['start_time'] = pd.to_datetime(df['start_time'], format="%Y-%m-%d %H:%M:%S", errors="coerce")
results_df['month'] = results_df['start_time'].dt.month
results_df['year'] = results_df['start_time'].dt.year
results_df['day'] = results_df['start_time'].dt.day
results_df['day_of_week'] = results_df['start_time'].dt.dayofweek

# Add predictions
results_df['income_anomaly'] = predictions['income_anomalies']
results_df['passenger_anomaly'] = predictions['passenger_anomalies']
results_df['isolation_forest_anomaly'] = predictions['isolation_forest_anomalies']
results_df['ensemble_anomaly'] = predictions['ensemble_anomalies']
results_df['anomaly_score'] = predictions['ensemble_scores']

# Print results
print(f"\n{'='*60}")
print("ANOMALY DETECTION ENSEMBLE RESULTS")
print(f"{'='*60}")
print(f"Total trips analyzed: {len(df):,}")
print(f"\nIndividual Model Results:")
print(f"├── Time Series Model (Income): {sum(predictions['income_anomalies']):,} anomalies ({sum(predictions['income_anomalies'])/len(df)*100:.2f}%)")
print(f"├── Time Series Model (Passengers): {sum(predictions['passenger_anomalies']):,} anomalies ({sum(predictions['passenger_anomalies'])/len(df)*100:.2f}%)")
print(f"└── Isolation Forest (All Features): {sum(predictions['isolation_forest_anomalies']):,} anomalies ({sum(predictions['isolation_forest_anomalies'])/len(df)*100:.2f}%)")
print(f"\nEnsemble Results:")
print(f"└── Final Anomalous Trips (≥2 models agree): {sum(predictions['ensemble_anomalies']):,} trips ({sum(predictions['ensemble_anomalies'])/len(df)*100:.2f}%)")

# Show most anomalous trips
anomalous_trips = results_df[results_df['ensemble_anomaly'] == 1].sort_values('anomaly_score', ascending=False)

print(f"\n{'='*60}")
print("TOP 10 MOST ANOMALOUS TRIPS")
print(f"{'='*60}")
if len(anomalous_trips) > 0:
    display_cols = ['trip_id', 'total_income', 'total_passengers', 'month', 'day_of_week', 'anomaly_score']
    print(anomalous_trips[display_cols].head(10).to_string(index=False))
else:
    print("No trips flagged as anomalous by ensemble (≥2 models)")
    print("\nTop 10 most suspicious trips:")
    top_suspicious = results_df.sort_values('anomaly_score', ascending=False).head(10)
    display_cols = ['trip_id', 'total_income', 'total_passengers', 'month', 'day_of_week', 'anomaly_score']
    print(top_suspicious[display_cols].to_string(index=False))

# Detailed analysis of anomalies
print(f"\n{'='*60}")
print("ANOMALY SCORE DISTRIBUTION")
print(f"{'='*60}")
for score in range(int(predictions['ensemble_scores'].max()) + 1):
    count = sum(predictions['ensemble_scores'] == score)
    percentage = count/len(df)*100
    bar = '█' * int(percentage)
    print(f"Score {score}: {count:,} trips ({percentage:.2f}%) {bar}")

# Feature statistics for anomalous trips
if len(anomalous_trips) > 0:
    print(f"\n{'='*60}")
    print("ANOMALOUS TRIPS CHARACTERISTICS")
    print(f"{'='*60}")
    print(f"Income - Mean: ${anomalous_trips['total_income'].mean():.2f}, Median: ${anomalous_trips['total_income'].median():.2f}")
    print(f"Passengers - Mean: {anomalous_trips['total_passengers'].mean():.1f}, Median: {anomalous_trips['total_passengers'].median():.1f}")
    print(f"Most common month: {anomalous_trips['month'].mode().iloc[0]}")
    print(f"Most common day of week: {anomalous_trips['day_of_week'].mode().iloc[0]} (0=Monday, 6=Sunday)")

# Save results
output_file = 'final_anomaly_detection_results.csv'
results_df.to_csv(output_file, index=False)
print(f"\n{'='*60}")
print(f"Results saved to: {output_file}")
print(f"{'='*60}")

# Model summary
print(f"\nMODEL SUMMARY:")
print(f"1. Time Series Anomaly Model (Income): IQR-based detection")
print(f"2. Time Series Anomaly Model (Passengers): IQR-based detection") 
print(f"3. Isolation Forest: Multi-dimelsnsional anomaly detection")
print(f"4. Ensemble: Majority voting (≥2 models must agree)")