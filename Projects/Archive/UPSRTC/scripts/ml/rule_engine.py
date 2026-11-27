import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Load all datasets
ensemble_output = pd.read_csv('ensemble_output.csv')
incidents = pd.read_csv('incidents.csv')
up_calendar = pd.read_csv('up_calendar.csv')
weather_alerts = pd.read_csv('weather_alerts.csv')

# Function to parse dates - trying multiple formats
def parse_date(date_str):
    """Parse date string - handles multiple formats"""
    if pd.isna(date_str):
        return pd.NaT
    
    date_str = str(date_str).strip()
    
    # Try dd/mm/yyyy format first
    try:
        return pd.to_datetime(date_str, format='%d/%m/%Y')
    except:
        pass
    
    # Try other common formats
    try:
        return pd.to_datetime(date_str, dayfirst=True)
    except:
        return pd.NaT

# Extract date from start_time
def extract_date_from_start_time(start_time_str):
    """Extract just the date portion from start_time"""
    if pd.isna(start_time_str):
        return pd.NaT
    
    date_part = str(start_time_str).split()[0]
    return parse_date(date_part)

# Parse dates in all dataframes
print("Parsing dates...")
ensemble_output['trip_date'] = ensemble_output['start_time'].apply(extract_date_from_start_time)
incidents['event_date_parsed'] = incidents['event_date'].apply(parse_date)
up_calendar['date_parsed'] = up_calendar['date'].apply(parse_date)
weather_alerts['alert_date_parsed'] = weather_alerts['alert_date'].apply(parse_date)

# IMPROVEMENT 1: Create temporal window for incidents (±1 day impact)
incident_dict = {}
for _, row in incidents.iterrows():
    date = row['event_date_parsed']
    if pd.notna(date):
        # Include incident day and next day (residual effects)
        for offset in [0, 1]:
            date_key = (date + timedelta(days=offset)).normalize()
            if date_key not in incident_dict:
                incident_dict[date_key] = []
            incident_dict[date_key].append({
                'name': row['event_name'],
                'type': row['event_type'],
                'location': row.get('location', 'N/A')
            })

# Holiday dictionary
holiday_dict = {}
for _, row in up_calendar[up_calendar['is_holiday'] == True].iterrows():
    date = row['date_parsed']
    if pd.notna(date):
        date_normalized = date.normalize()
        holiday_dict[date_normalized] = row['holiday_name']

# IMPROVEMENT 2: Weather alerts with temporal window (day before, day of, day after)
weather_dict = {}
for _, row in weather_alerts.iterrows():
    date = row['alert_date_parsed']
    if pd.notna(date):
        # Weather effects can span multiple days
        for offset in [-1, 0, 1]:
            date_key = (date + timedelta(days=offset)).normalize()
            if date_key not in weather_dict:
                weather_dict[date_key] = []
            weather_dict[date_key].append({
                'alert': row['alert'],
                'severity': row['severity'],
                'region': row.get('region_affected', 'N/A')
            })

# IMPROVEMENT 3: Enhanced route statistics with more context
route_stats = ensemble_output.groupby('route_id').agg({
    'total_income': ['median', 'mean', 'std'],
    'total_passengers': ['median', 'mean', 'std']
}).round(1)

route_stats.columns = ['income_median', 'income_mean', 'income_std', 
                        'passengers_median', 'passengers_mean', 'passengers_std']
route_stats = route_stats.to_dict('index')

def generate_insight_summary(row, route_stats):
    """Generate detailed insight summary for Alerts with enhanced context"""
    route_id = row['route_id']
    
    # Use the typical ranges from the dataset itself
    income_low = int(row.get('income_typical_low', 0))
    income_high = int(row.get('income_typical_high', 0))
    passengers_low = int(row.get('passengers_typical_low', 0))
    passengers_high = int(row.get('passengers_typical_high', 0))
    
    income_range = f"{income_low}–{income_high}"
    passengers_range = f"{passengers_low}–{passengers_high}"
    
    # Get route statistics for median
    if route_id in route_stats:
        stats = route_stats[route_id]
        income_median = stats['income_median']
        passengers_median = stats['passengers_median']
    else:
        income_median = row['total_income']
        passengers_median = row['total_passengers']
    
    # Calculate deviations
    income_deviation = ((row['total_income'] - income_median) / income_median * 100) if income_median > 0 else 0
    passengers_deviation = ((row['total_passengers'] - passengers_median) / passengers_median * 100) if passengers_median > 0 else 0
    
    # IMPROVEMENT 4: Determine severity based on deviation magnitude
    severity_indicators = []
    if abs(income_deviation) > 100:
        severity_indicators.append("extreme income deviation")
    elif abs(income_deviation) > 50:
        severity_indicators.append("high income deviation")
    
    if abs(passengers_deviation) > 100:
        severity_indicators.append("extreme passenger deviation")
    elif abs(passengers_deviation) > 50:
        severity_indicators.append("high passenger deviation")
    
    # Determine which models triggered
    models_triggered = []
    if row.get('income_anomaly', 0) == 1:
        models_triggered.append('income')
    if row.get('passenger_anomaly', 0) == 1:
        models_triggered.append('passengers')
    if row.get('iso_anomaly', 0) == 1:
        models_triggered.append('isolation forest')
    
    models_str = ', '.join(models_triggered) if models_triggered else 'ensemble model'
    
    # IMPROVEMENT 5: Add context about day of week and time
    trip_date = row['trip_date']
    day_name = trip_date.strftime('%A') if pd.notna(trip_date) else 'Unknown'
    
    # Generate insight with enhanced details
    insight = (f"Trip on {row['start_time']} ({day_name}) for route {route_id} was flagged as anomalous. "
               f"Total income {row['total_income']:.1f} is {income_deviation:+.1f}% vs median {income_median:.1f} "
               f"(typical range: {income_range}), "
               f"total passengers {row['total_passengers']} is {passengers_deviation:+.1f}% vs median {passengers_median:.1f} "
               f"(typical range: {passengers_range}). "
               f"Models triggered: {models_str}.")
    
    # Add severity note if applicable
    if severity_indicators:
        insight += f" Note: {', '.join(severity_indicators)}."
    
    return insight

def classify_anomaly_with_insights(row, route_stats):
    """
    Classify anomalous trips and generate appropriate insights
    
    LOGIC:
    - WARNING = Anomaly explained by external factors (holiday/weekend/incident/weather)
    - ALERT = Anomaly with NO external factors (needs investigation)
    """
    trip_date = row['trip_date']
    
    # If date is invalid, classify as Alert with no special conditions
    if pd.isna(trip_date):
        return {
            'is_explained': False,
            'remarks': 'No special conditions',
            'insight_summary': generate_insight_summary(row, route_stats),
            'is_explain_status': 'Alert'
        }
    
    # Normalize trip date
    trip_date_normalized = trip_date.normalize()
    
    # Check for matching conditions
    matching_conditions = []
    
    # Check incidents (with temporal context)
    if trip_date_normalized in incident_dict:
        incidents_list = incident_dict[trip_date_normalized]
        for inc in incidents_list:
            incident_info = f"Incident: {inc['name']}"
            if inc.get('location') and inc['location'] != 'N/A':
                incident_info += f" at {inc['location']}"
            matching_conditions.append(incident_info)
    
    # Check holidays
    if trip_date_normalized in holiday_dict:
        holiday_name = holiday_dict[trip_date_normalized]
        matching_conditions.append(f"Holiday: {holiday_name}")
    
    # Check weather alerts (with severity and region context)
    if trip_date_normalized in weather_dict:
        weather_list = weather_dict[trip_date_normalized]
        for weather in weather_list:
            weather_info = f"Weather Alert: {weather['alert']} ({weather['severity']})"
            if weather.get('region') and weather['region'] != 'N/A':
                weather_info += f" in {weather['region']}"
            matching_conditions.append(weather_info)
    
    # IMPROVEMENT 6: Check if it's a weekend
    day_of_week = trip_date_normalized.dayofweek
    if day_of_week >= 5:  # Saturday = 5, Sunday = 6
        matching_conditions.append("Weekend")
    
    # IMPROVEMENT 7: Check if it's a day before/after holiday (bridge days)
    day_before = (trip_date_normalized - timedelta(days=1))
    day_after = (trip_date_normalized + timedelta(days=1))
    
    if day_before in holiday_dict:
        matching_conditions.append(f"Day after {holiday_dict[day_before]}")
    elif day_after in holiday_dict:
        matching_conditions.append(f"Day before {holiday_dict[day_after]}")
    
    # If any condition matches, it's a WARNING (explained by external factors)
    if matching_conditions:
        remarks = ', '.join(matching_conditions)
        return {
            'is_explained': True,
            'remarks': remarks,
            'insight_summary': '',
            'is_explain_status': 'Warning'
        }
    else:
        # No external factors - it's an ALERT (needs investigation)
        return {
            'is_explained': False,
            'remarks': 'No special conditions',
            'insight_summary': generate_insight_summary(row, route_stats),
            'is_explain_status': 'Alert'
        }

# Filter only anomalous trips (ensemble_anomaly == 1)
anomalous_trips = ensemble_output[ensemble_output['ensemble_anomaly'] == 1].copy()

print(f"\n{'='*60}")
print(f"Processing {len(anomalous_trips)} anomalous trips...")
print(f"{'='*60}")

# Apply classification with insights
results = anomalous_trips.apply(lambda row: classify_anomaly_with_insights(row, route_stats), axis=1)

# Extract results into separate columns
anomalous_trips['is_explained'] = results.apply(lambda x: x['is_explained'])
anomalous_trips['remarks'] = results.apply(lambda x: x['remarks'])
anomalous_trips['insight_summary'] = results.apply(lambda x: x['insight_summary'])
anomalous_trips['is_explain_status'] = results.apply(lambda x: x['is_explain_status'])

# Drop the temporary trip_date column
anomalous_trips_output = anomalous_trips.drop('trip_date', axis=1)





# --- FORCE FINAL.csv COLUMN ORDER (NO LOGIC CHANGE) ---

final_columns = [
    'dwh_rid',
    'dwh_crddt',
    'dwh_upddt',
    'dwh_active',
    'dwh_upddby',
    'region_id',
    'region_name',
    'route_id',
    'route_name',
    'waybill_number',
    'trip_id',
    'start_time',
    'end_time',
    'total_income',
    'total_passengers',
    'trip_status',
    'conductor_id',
    'driver_id',
    'support_driver_id',
    'schedule_id',
    'etim_device_id',
    'duty_type',
    'bus_id',
    'bus_number_plate',
    'time_valid',
    'income_typical_low',
    'income_typical_high',
    'passengers_typical_low',
    'passengers_typical_high',
    'income_anomaly',
    'passenger_anomaly',
    'iso_anomaly',
    'ensemble_score',
    'ensemble_anomaly',
    'is_explained',
    'remarks',
    'insight_summary',
    'is_explain_status'
]

# Ensure all expected columns exist (safety)
for col in final_columns:
    if col not in anomalous_trips_output.columns:
        anomalous_trips_output[col] = ''

# Reorder exactly like Final.csv
anomalous_trips_output = anomalous_trips_output[final_columns]

# Save
anomalous_trips_output.to_csv(
    'classified_anomalies_with_insights.csv',
    index=False
)

# Save to new CSV matching Final.csv column order
anomalous_trips_output.to_csv('classified_anomalies_with_insights.csv', index=False)

# IMPROVEMENT 8: Enhanced summary statistics
print("\n" + "="*60)
print("ANOMALY CLASSIFICATION SUMMARY")
print("="*60)
print(f"\nTotal anomalous trips processed: {len(anomalous_trips)}")
print(f"\nClassification breakdown:")
print(anomalous_trips['is_explain_status'].value_counts())

print(f"\n{'='*60}")
print("WARNING REASONS BREAKDOWN")
print("="*60)
warnings = anomalous_trips[anomalous_trips['is_explain_status'] == 'Warning']
if len(warnings) > 0:
    print(warnings['remarks'].value_counts())
    print(f"\nTotal Warnings: {len(warnings)} ({len(warnings)/len(anomalous_trips)*100:.1f}%)")
else:
    print("No warnings found")

print(f"\n{'='*60}")
print("ALERTS (NEED INVESTIGATION)")
print("="*60)
alerts = anomalous_trips[anomalous_trips['is_explain_status'] == 'Alert']
print(f"Total Alerts: {len(alerts)} ({len(alerts)/len(anomalous_trips)*100:.1f}%)")

if len(alerts) > 0:
    print("\nTop 5 routes with most unexplained alerts:")
    print(alerts['route_name'].value_counts().head())
    
    print("\nTop 5 regions with most unexplained alerts:")
    print(alerts['region_name'].value_counts().head())

print(f"\n{'='*60}")
print(f"Output saved to: classified_anomalies_with_insights.csv")
print("="*60)