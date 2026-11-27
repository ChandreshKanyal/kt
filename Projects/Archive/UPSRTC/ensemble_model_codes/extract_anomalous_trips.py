import pandas as pd

# Load the final results
df = pd.read_csv('final_anomaly_detection_results.csv')

# Filter only anomalous trips (majority voting result)
anomalous_trips = df[df['ensemble_anomaly'] == 1]

# Save to separate CSV
anomalous_trips.to_csv('anomalous_trips_majority_voting.csv', index=False)

print(f"Extracted {len(anomalous_trips)} anomalous trips to 'anomalous_trips_majority_voting.csv'")