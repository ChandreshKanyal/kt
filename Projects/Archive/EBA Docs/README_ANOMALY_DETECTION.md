# Bus Trip Anomaly Detection System

## Overview
This system detects potentially fraudulent bus trips where drivers and conductors might be embezzling money by misrepresenting passenger counts or income. The model uses multiple statistical and machine learning techniques to identify anomalies within each route.

## Detection Methods

### 1. **Statistical Outliers (IQR Method)**
- Identifies trips with income or passenger counts outside 1.5 × IQR range
- Route-specific thresholds to account for different route characteristics

### 2. **Z-Score Analysis**
- Flags trips with extreme deviations (|z-score| > 3)
- Analyzes: income, passengers, income per passenger, trip duration

### 3. **Isolation Forest**
- Machine learning algorithm that isolates anomalies
- Considers multiple features: income, passengers, time patterns, duration
- Applied per route for route-specific anomaly detection

### 4. **Suspicious Pattern Detection**
- Low income despite high passenger count
- Unusual income-to-passenger ratios
- Significant deviations from conductor/driver averages

### 5. **Combined Anomaly Scoring**
- Aggregates all detection methods
- Score range: 0-10 (higher = more suspicious)
- Trips with score ≥ 3 marked as anomalies
- Score ≥ 5 considered high priority

## Results Summary

- **Total Trips Analyzed**: 2,080,312
- **Anomalies Detected**: 47,099 (2.26%)
- **High Priority Cases**: 18,084

### Top Suspicious Personnel
**Conductors:**
- Conductor <id redacted>: 112 anomalies (24.2% of trips)
- Conductor <id redacted>: 69 anomalies (48.3% of trips)
- Conductor <id redacted>: 62 anomalies (43.4% of trips)

**Drivers:**
- Driver <id redacted>: 138 anomalies (40.7% of trips)
- Driver <id redacted>: 110 anomalies (17.3% of trips)
- Driver <id redacted>: 98 anomalies (24.7% of trips)

## Output Files

1. **bus_trips_with_anomalies.csv**
   - Complete dataset with anomaly flags and scores
   - All engineered features included

2. **anomaly_report.csv**
   - Detailed report of 47,099 detected anomalies
   - Key metrics and anomaly indicators

3. **high_priority_anomalies.csv**
   - 18,084 most suspicious trips (score ≥ 5)
   - Ready for immediate field investigation

4. **anomaly_detection_report.txt**
   - Comprehensive statistical analysis
   - Recommendations for field team
   - Pattern insights

5. **anomaly_visualizations.png**
   - 9 visualizations showing:
     - Anomaly score distribution
     - Income vs passenger patterns
     - Time-based patterns
     - Top suspicious personnel

## Key Insights

1. **Financial Impact**: Anomalous trips show significantly lower income per passenger
2. **Time Patterns**: Certain hours show higher anomaly rates
3. **Personnel Patterns**: Some conductors/drivers have anomaly rates exceeding 40% of their trips
4. **Route Patterns**: Specific routes consistently show higher anomaly rates

## Recommendations for Field Team

### Immediate Actions:
1. Investigate all trips with anomaly score ≥ 5
2. Conduct surprise audits on flagged conductors and drivers
3. Focus on routes with highest anomaly counts

### Systematic Approach:
1. Cross-verify reported income with actual ticket sales
2. Interview passengers on suspicious trips
3. Monitor real-time during peak anomaly hours
4. Compare cash collections with system records

### Long-term Measures:
1. Implement digital ticketing to reduce cash handling
2. Regular rotation of conductor-driver pairs
3. Install GPS tracking for route verification
4. Automated alerts for suspicious patterns

## Technical Implementation

The system uses:
- **Python** with pandas, scikit-learn, matplotlib
- **Multiple anomaly detection algorithms** for robustness
- **Route-specific analysis** to account for different route characteristics
- **Comprehensive feature engineering** including temporal patterns
- **Scalable design** capable of processing millions of records

## Usage

To run the analysis on new data:
```bash
python anomaly_detection_model.py
python visualize_anomalies.py
```

The system automatically generates all reports and visualizations.
