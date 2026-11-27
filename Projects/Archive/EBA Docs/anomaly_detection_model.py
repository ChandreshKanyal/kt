import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)

print("Building comprehensive anomaly detection model for bus trip fraud detection...")
print("=" * 80)

# Load the data
print("\n1. Loading data...")
df = pd.read_csv('Transit Data/data_1.csv')
print(f"   Loaded {len(df):,} records")

# Convert datetime columns
print("\n2. Converting datetime columns...")
df['start_time'] = pd.to_datetime(df['start_time'], format='mixed')
df['end_time'] = pd.to_datetime(df['end_time'], format='mixed')

# Feature Engineering
print("\n3. Engineering features...")
# Calculate trip duration
df['trip_duration_minutes'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 60

# Calculate income per passenger
df['income_per_passenger'] = df['total_income'] / (df['total_passengers'] + 1)

# Extract time-based features
df['hour_of_day'] = df['start_time'].dt.hour
df['day_of_week'] = df['start_time'].dt.dayofweek
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
df['month'] = df['start_time'].dt.month
df['day_of_month'] = df['start_time'].dt.day

# Calculate route-level statistics
print("\n4. Calculating route-level statistics...")
route_stats = df.groupby('route_id').agg({
    'total_income': ['mean', 'std', 'median', 'min', 'max'],
    'total_passengers': ['mean', 'std', 'median', 'min', 'max'],
    'trip_duration_minutes': ['mean', 'std', 'median'],
    'income_per_passenger': ['mean', 'std', 'median'],
    'trip_id': 'count'
}).reset_index()

# Flatten column names
route_stats.columns = ['_'.join(col).strip() if col[1] else col[0] for col in route_stats.columns.values]
route_stats.rename(columns={'trip_id_count': 'trip_count'}, inplace=True)

# Merge route statistics back
df = df.merge(route_stats, on='route_id', how='left')

# Calculate z-scores within each route
df['income_zscore'] = (df['total_income'] - df['total_income_mean']) / (df['total_income_std'] + 1e-6)
df['passengers_zscore'] = (df['total_passengers'] - df['total_passengers_mean']) / (df['total_passengers_std'] + 1e-6)
df['duration_zscore'] = (df['trip_duration_minutes'] - df['trip_duration_minutes_mean']) / (df['trip_duration_minutes_std'] + 1e-6)
df['income_per_passenger_zscore'] = (df['income_per_passenger'] - df['income_per_passenger_mean']) / (df['income_per_passenger_std'] + 1e-6)

# Calculate percentage deviations
df['income_deviation_pct'] = ((df['total_income'] - df['total_income_median']) / (df['total_income_median'] + 1e-6)) * 100
df['passengers_deviation_pct'] = ((df['total_passengers'] - df['total_passengers_median']) / (df['total_passengers_median'] + 1e-6)) * 100

# Conductor and driver analysis
print("\n5. Analyzing conductor and driver patterns...")
conductor_stats = df.groupby('conductor_id').agg({
    'total_income': ['mean', 'std'],
    'total_passengers': ['mean', 'std'],
    'trip_id': 'count'
}).reset_index()
conductor_stats.columns = ['conductor_id', 'conductor_income_mean', 'conductor_income_std', 
                          'conductor_passengers_mean', 'conductor_passengers_std', 'conductor_trip_count']

driver_stats = df.groupby('driver_id').agg({
    'total_income': ['mean', 'std'],
    'total_passengers': ['mean', 'std'],
    'trip_id': 'count'
}).reset_index()
driver_stats.columns = ['driver_id', 'driver_income_mean', 'driver_income_std',
                       'driver_passengers_mean', 'driver_passengers_std', 'driver_trip_count']

df = df.merge(conductor_stats, on='conductor_id', how='left')
df = df.merge(driver_stats, on='driver_id', how='left')

# Anomaly Detection Methods
print("\n6. Applying anomaly detection methods...")

# Method 1: Statistical Outliers (IQR method)
print("\n   Method 1: Statistical Outliers (IQR)")
Q1_income = df.groupby('route_id')['total_income'].quantile(0.25)
Q3_income = df.groupby('route_id')['total_income'].quantile(0.75)
IQR_income = Q3_income - Q1_income

Q1_passengers = df.groupby('route_id')['total_passengers'].quantile(0.25)
Q3_passengers = df.groupby('route_id')['total_passengers'].quantile(0.75)
IQR_passengers = Q3_passengers - Q1_passengers

# Mark outliers
df['is_income_outlier_iqr'] = False
df['is_passenger_outlier_iqr'] = False

for route_id in df['route_id'].unique():
    route_mask = df['route_id'] == route_id
    
    # Income outliers
    lower_bound_income = Q1_income[route_id] - 1.5 * IQR_income[route_id]
    upper_bound_income = Q3_income[route_id] + 1.5 * IQR_income[route_id]
    df.loc[route_mask & ((df['total_income'] < lower_bound_income) | 
                         (df['total_income'] > upper_bound_income)), 'is_income_outlier_iqr'] = True
    
    # Passenger outliers
    lower_bound_passengers = Q1_passengers[route_id] - 1.5 * IQR_passengers[route_id]
    upper_bound_passengers = Q3_passengers[route_id] + 1.5 * IQR_passengers[route_id]
    df.loc[route_mask & ((df['total_passengers'] < lower_bound_passengers) | 
                         (df['total_passengers'] > upper_bound_passengers)), 'is_passenger_outlier_iqr'] = True

# Method 2: Z-score based anomalies
print("   Method 2: Z-score based anomalies")
df['is_anomaly_zscore'] = ((abs(df['income_zscore']) > 3) | 
                           (abs(df['passengers_zscore']) > 3) |
                           (abs(df['income_per_passenger_zscore']) > 3))

# Method 3: Isolation Forest
print("   Method 3: Isolation Forest")
# Prepare features for Isolation Forest

features_for_if = ['total_income', 'total_passengers', 'income_per_passenger', 
                   'trip_duration_minutes', 'hour_of_day', 'day_of_week']

# Run Isolation Forest by route (to detect route-specific anomalies)
df['isolation_forest_anomaly'] = 0
df['isolation_forest_score'] = 0

for route_id in df['route_id'].unique()[:100]:  # Limit to first 100 routes for speed
    route_mask = df['route_id'] == route_id
    route_data = df[route_mask]
    
    if len(route_data) > 20:  # Need minimum samples
        # Prepare features
        X = route_data[features_for_if].fillna(0)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Fit Isolation Forest
        iso_forest = IsolationForest(contamination=0.05, random_state=42)
        predictions = iso_forest.fit_predict(X_scaled)
        scores = iso_forest.score_samples(X_scaled)
        
        # Store results
        df.loc[route_mask, 'isolation_forest_anomaly'] = predictions
        df.loc[route_mask, 'isolation_forest_score'] = scores

# Method 4: Combined anomaly score
print("   Method 4: Combined anomaly detection")
df['anomaly_score'] = 0

# Add points for each type of anomaly
df.loc[df['is_income_outlier_iqr'], 'anomaly_score'] += 2
df.loc[df['is_passenger_outlier_iqr'], 'anomaly_score'] += 2
df.loc[df['is_anomaly_zscore'], 'anomaly_score'] += 3
df.loc[df['isolation_forest_anomaly'] == -1, 'anomaly_score'] += 3

# Suspicious patterns
# Low income despite high passengers
df['suspicious_income_ratio'] = (df['income_per_passenger'] < df['income_per_passenger_mean'] * 0.5) & \
                                (df['total_passengers'] > df['total_passengers_mean'])
df.loc[df['suspicious_income_ratio'], 'anomaly_score'] += 2

# Mark final anomalies (score >= 3)
df['is_anomaly'] = df['anomaly_score'] >= 3

# Save results
print("\n7. Saving results...")
# Save full dataset with anomaly flags
df.to_csv('bus_trips_with_anomalies.csv', index=False)

# Save only anomalies
anomalies = df[df['is_anomaly']].copy()
anomalies = anomalies.sort_values('anomaly_score', ascending=False)

# Select relevant columns for the anomaly report
anomaly_report_columns = [
    'trip_id', 'route_id', 'conductor_id', 'driver_id', 
    'start_time', 'end_time', 'total_income', 'total_passengers',
    'income_per_passenger', 'trip_duration_minutes',
    'income_zscore', 'passengers_zscore', 'anomaly_score',
    'is_income_outlier_iqr', 'is_passenger_outlier_iqr', 
    'is_anomaly_zscore', 'suspicious_income_ratio'
]

anomaly_report = anomalies[anomaly_report_columns]
anomaly_report.to_csv('anomaly_report.csv', index=False)

# Generate summary statistics
print("\n" + "=" * 80)
print("ANOMALY DETECTION SUMMARY")
print("=" * 80)
print(f"\nTotal trips analyzed: {len(df):,}")
print(f"Total anomalies detected: {len(anomalies):,} ({len(anomalies)/len(df)*100:.2f}%)")
print(f"\nAnomaly breakdown:")
print(f"  - Income outliers (IQR): {df['is_income_outlier_iqr'].sum():,}")
print(f"  - Passenger outliers (IQR): {df['is_passenger_outlier_iqr'].sum():,}")
print(f"  - Z-score anomalies: {df['is_anomaly_zscore'].sum():,}")
print(f"  - Isolation Forest anomalies: {(df['isolation_forest_anomaly'] == -1).sum():,}")
print(f"  - Suspicious income ratios: {df['suspicious_income_ratio'].sum():,}")

# Top suspicious conductors
print("\nTop 10 conductors by anomaly count:")
conductor_anomalies = anomalies.groupby('conductor_id').size().sort_values(ascending=False).head(10)
for conductor_id, count in conductor_anomalies.items():
    pct = count / len(df[df['conductor_id'] == conductor_id]) * 100
    print(f"  Conductor {conductor_id}: {count} anomalies ({pct:.1f}% of their trips)")

# Top suspicious drivers
print("\nTop 10 drivers by anomaly count:")
driver_anomalies = anomalies.groupby('driver_id').size().sort_values(ascending=False).head(10)
for driver_id, count in driver_anomalies.items():
    pct = count / len(df[df['driver_id'] == driver_id]) * 100
    print(f"  Driver {driver_id}: {count} anomalies ({pct:.1f}% of their trips)")

# Routes with most anomalies
print("\nTop 10 routes by anomaly count:")
route_anomalies = anomalies.groupby('route_id').size().sort_values(ascending=False).head(10)
for route_id, count in route_anomalies.items():
    pct = count / len(df[df['route_id'] == route_id]) * 100
    print(f"  Route {route_id}: {count} anomalies ({pct:.1f}% of trips on this route)")

print("\n" + "=" * 80)
print("Files saved:")
print("  - bus_trips_with_anomalies.csv (full dataset with anomaly flags)")
print("  - anomaly_report.csv (detailed report of detected anomalies)")
print("=" * 80)
