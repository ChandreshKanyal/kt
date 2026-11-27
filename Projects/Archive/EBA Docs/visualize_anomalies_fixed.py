import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set matplotlib parameters
plt.rcParams['figure.max_open_warning'] = 0

# Load the anomaly report
print("Loading anomaly detection results...")
anomalies = pd.read_csv('anomaly_report.csv')
anomalies['start_time'] = pd.to_datetime(anomalies['start_time'], format='mixed')
anomalies['end_time'] = pd.to_datetime(anomalies['end_time'], format='mixed')

# Create a large figure with 9 subplots
print("Creating visualizations...")
fig = plt.figure(figsize=(20, 16))

# Add overall title
fig.suptitle('Bus Trip Anomaly Detection - Comprehensive Analysis', fontsize=24, y=0.98)

# 1. Distribution of Anomaly Scores
ax1 = fig.add_subplot(3, 3, 1)
anomalies['anomaly_score'].hist(bins=20, edgecolor='black', alpha=0.7, ax=ax1)
ax1.set_title('Distribution of Anomaly Scores', fontsize=14, pad=10)
ax1.set_xlabel('Anomaly Score')
ax1.set_ylabel('Frequency')
ax1.grid(True, alpha=0.3)

# 2. Income vs Passengers scatter
ax2 = fig.add_subplot(3, 3, 2)
scatter = ax2.scatter(anomalies['total_passengers'], anomalies['total_income'], 
                     c=anomalies['anomaly_score'], cmap='Reds', alpha=0.6, s=30)
cbar = plt.colorbar(scatter, ax=ax2)
cbar.set_label('Anomaly Score')
ax2.set_title('Income vs Passengers (Colored by Anomaly Score)', fontsize=14, pad=10)
ax2.set_xlabel('Total Passengers')
ax2.set_ylabel('Total Income')
ax2.grid(True, alpha=0.3)

# 3. Income per Passenger Distribution
ax3 = fig.add_subplot(3, 3, 3)
anomalies['income_per_passenger'].hist(bins=50, edgecolor='black', alpha=0.7, ax=ax3)
median_val = anomalies['income_per_passenger'].median()
ax3.axvline(median_val, color='red', linestyle='--', linewidth=2,
           label=f'Median: {median_val:.2f}')
ax3.set_title('Income per Passenger Distribution', fontsize=14, pad=10)
ax3.set_xlabel('Income per Passenger')
ax3.set_ylabel('Frequency')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. Z-score distributions
ax4 = fig.add_subplot(3, 3, 4)
z_score_data = [anomalies['income_zscore'].dropna(), anomalies['passengers_zscore'].dropna()]
box_plot = ax4.boxplot(z_score_data, labels=['Income Z-score', 'Passengers Z-score'])
ax4.set_title('Z-score Distributions for Anomalies', fontsize=14, pad=10)
ax4.set_ylabel('Z-score')
ax4.grid(True, alpha=0.3)

# 5. Anomalies by Hour of Day
ax5 = fig.add_subplot(3, 3, 5)
hour_counts = anomalies.groupby(anomalies['start_time'].dt.hour).size()
ax5.bar(hour_counts.index, hour_counts.values, alpha=0.7, color='steelblue')
ax5.set_title('Anomalies by Hour of Day', fontsize=14, pad=10)
ax5.set_xlabel('Hour')
ax5.set_ylabel('Count')
ax5.set_xticks(range(0, 24, 2))
ax5.grid(True, alpha=0.3, axis='y')

# 6. Trip Duration Distribution
ax6 = fig.add_subplot(3, 3, 6)
anomalies['trip_duration_minutes'].hist(bins=50, edgecolor='black', alpha=0.7, ax=ax6)
ax6.set_title('Trip Duration Distribution', fontsize=14, pad=10)
ax6.set_xlabel('Duration (minutes)')
ax6.set_ylabel('Frequency')
ax6.grid(True, alpha=0.3)

# 7. Top 15 Conductors by Anomaly Count
ax7 = fig.add_subplot(3, 3, 7)
top_conductors = anomalies['conductor_id'].value_counts().head(15)
y_pos = np.arange(len(top_conductors))
ax7.barh(y_pos, top_conductors.values, alpha=0.7, color='coral')
ax7.set_yticks(y_pos)
ax7.set_yticklabels([str(x) for x in top_conductors.index])
ax7.set_title('Top 15 Conductors by Anomaly Count', fontsize=14, pad=10)
ax7.set_xlabel('Number of Anomalies')
ax7.set_ylabel('Conductor ID')
ax7.grid(True, alpha=0.3, axis='x')

# 8. Top 15 Drivers by Anomaly Count
ax8 = fig.add_subplot(3, 3, 8)
top_drivers = anomalies['driver_id'].value_counts().head(15)
y_pos = np.arange(len(top_drivers))
ax8.barh(y_pos, top_drivers.values, alpha=0.7, color='lightgreen')
ax8.set_yticks(y_pos)
ax8.set_yticklabels([str(x) for x in top_drivers.index])
ax8.set_title('Top 15 Drivers by Anomaly Count', fontsize=14, pad=10)
ax8.set_xlabel('Number of Anomalies')
ax8.set_ylabel('Driver ID')
ax8.grid(True, alpha=0.3, axis='x')

# 9. Anomaly Types Breakdown
ax9 = fig.add_subplot(3, 3, 9)
anomaly_types = {
    'Income\nOutlier': anomalies['is_income_outlier_iqr'].sum(),
    'Passenger\nOutlier': anomalies['is_passenger_outlier_iqr'].sum(),
    'Z-score\nAnomaly': anomalies['is_anomaly_zscore'].sum(),
    'Suspicious\nRatio': anomalies['suspicious_income_ratio'].sum()
}
x_pos = np.arange(len(anomaly_types))
ax9.bar(x_pos, list(anomaly_types.values()), alpha=0.7, color='mediumpurple')
ax9.set_xticks(x_pos)
ax9.set_xticklabels(list(anomaly_types.keys()))
ax9.set_title('Anomaly Types Breakdown', fontsize=14, pad=10)
ax9.set_xlabel('Anomaly Type')
ax9.set_ylabel('Count')
ax9.grid(True, alpha=0.3, axis='y')

# Adjust spacing between subplots
plt.subplots_adjust(left=0.05, right=0.95, top=0.93, bottom=0.05, wspace=0.3, hspace=0.4)

# Save the figure with high DPI
print("Saving visualization...")
plt.savefig('anomaly_visualizations_fixed.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close('all')
print("Saved visualizations to 'anomaly_visualizations_fixed.png'")

# Also create individual plots as a backup
print("\nCreating individual plots as backup...")
individual_dir = "individual_plots"
import os
if not os.path.exists(individual_dir):
    os.makedirs(individual_dir)

# Create each plot individually
plots_data = [
    ('anomaly_score_distribution', anomalies['anomaly_score'], 'hist', 'Anomaly Score Distribution'),
    ('income_vs_passengers', (anomalies['total_passengers'], anomalies['total_income']), 'scatter', 'Income vs Passengers'),
    ('income_per_passenger', anomalies['income_per_passenger'], 'hist', 'Income per Passenger'),
    ('anomalies_by_hour', hour_counts, 'bar', 'Anomalies by Hour'),
    ('trip_duration', anomalies['trip_duration_minutes'], 'hist', 'Trip Duration Distribution'),
]

for filename, data, plot_type, title in plots_data[:5]:
    plt.figure(figsize=(8, 6))
    
    if plot_type == 'hist':
        plt.hist(data, bins=30, edgecolor='black', alpha=0.7)
    elif plot_type == 'scatter':
        plt.scatter(data[0], data[1], alpha=0.6)
    elif plot_type == 'bar' and hasattr(data, 'index'):
        plt.bar(data.index, data.values)
    
    plt.title(title)
    plt.tight_layout()
    plt.savefig(f'{individual_dir}/{filename}.png', dpi=150)
    plt.close()

print(f"Individual plots saved in '{individual_dir}' directory")

# Create a detailed statistical report (same as before)
print("\nGenerating detailed statistical report...")

# Calculate statistics for suspicious conductors and drivers
conductor_stats = anomalies.groupby('conductor_id').agg({
    'anomaly_score': ['count', 'mean', 'max'],
    'total_income': ['mean', 'std'],
    'total_passengers': ['mean', 'std'],
    'income_per_passenger': 'mean'
}).round(2)

driver_stats = anomalies.groupby('driver_id').agg({
    'anomaly_score': ['count', 'mean', 'max'],
    'total_income': ['mean', 'std'],
    'total_passengers': ['mean', 'std'],
    'income_per_passenger': 'mean'
}).round(2)

# Create text report
report = []
report.append("=" * 80)
report.append("ANOMALY DETECTION DETAILED REPORT")
report.append("=" * 80)
report.append(f"\nReport Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append(f"Total Anomalies Analyzed: {len(anomalies):,}")

# Anomaly Score Statistics
report.append("\n\nANOMALY SCORE STATISTICS:")
report.append(f"  - Mean Score: {anomalies['anomaly_score'].mean():.2f}")
report.append(f"  - Median Score: {anomalies['anomaly_score'].median():.2f}")
report.append(f"  - Max Score: {anomalies['anomaly_score'].max()}")
report.append(f"  - High Severity (score >= 5): {len(anomalies[anomalies['anomaly_score'] >= 5]):,}")

# Financial Impact
report.append("\n\nFINANCIAL IMPACT ANALYSIS:")
mean_income_anomaly = anomalies['total_income'].mean()
mean_income_per_passenger_anomaly = anomalies['income_per_passenger'].mean()
report.append(f"  - Average Income in Anomalous Trips: ${mean_income_anomaly:.2f}")
report.append(f"  - Average Income per Passenger in Anomalies: ${mean_income_per_passenger_anomaly:.2f}")

# Pattern Analysis
report.append("\n\nPATTERN ANALYSIS:")
report.append(f"  - Trips with suspiciously low income ratio: {anomalies['suspicious_income_ratio'].sum():,}")
report.append(f"  - Trips with extreme income deviation: {len(anomalies[abs(anomalies['income_zscore']) > 3]):,}")
report.append(f"  - Trips with extreme passenger deviation: {len(anomalies[abs(anomalies['passengers_zscore']) > 3]):,}")

# Time-based patterns
report.append("\n\nTIME-BASED PATTERNS:")
peak_hour = anomalies.groupby(anomalies['start_time'].dt.hour).size().idxmax()
report.append(f"  - Peak hour for anomalies: {peak_hour}:00")
weekend_anomalies = anomalies[anomalies['start_time'].dt.dayofweek.isin([5, 6])]
report.append(f"  - Weekend anomalies: {len(weekend_anomalies):,} ({len(weekend_anomalies)/len(anomalies)*100:.1f}%)")

# Route Analysis
report.append("\n\nROUTE ANALYSIS:")
route_anomaly_counts = anomalies['route_id'].value_counts()
report.append(f"  - Routes with anomalies: {len(route_anomaly_counts)}")
report.append(f"  - Routes with >50 anomalies: {len(route_anomaly_counts[route_anomaly_counts > 50])}")

# High-risk individuals
report.append("\n\nHIGH-RISK INDIVIDUALS:")
report.append("\nTop 10 Suspicious Conductors:")
for idx, (conductor_id, count) in enumerate(anomalies['conductor_id'].value_counts().head(10).items(), 1):
    avg_score = anomalies[anomalies['conductor_id'] == conductor_id]['anomaly_score'].mean()
    report.append(f"  {idx}. Conductor {conductor_id}: {count} anomalies (avg score: {avg_score:.2f})")

report.append("\nTop 10 Suspicious Drivers:")
for idx, (driver_id, count) in enumerate(anomalies['driver_id'].value_counts().head(10).items(), 1):
    avg_score = anomalies[anomalies['driver_id'] == driver_id]['anomaly_score'].mean()
    report.append(f"  {idx}. Driver {driver_id}: {count} anomalies (avg score: {avg_score:.2f})")

# Save report
with open('anomaly_detection_report_fixed.txt', 'w') as f:
    f.write('\n'.join(report))

print("\nSaved detailed report to 'anomaly_detection_report_fixed.txt'")

# Create a CSV with high-priority cases (anomaly score >= 5)
high_priority = anomalies[anomalies['anomaly_score'] >= 5].sort_values('anomaly_score', ascending=False)
high_priority.to_csv('high_priority_anomalies_fixed.csv', index=False)
print(f"Saved {len(high_priority)} high-priority cases to 'high_priority_anomalies_fixed.csv'")

print("\nAll reports and visualizations have been generated successfully!")
print("\nFiles created:")
print("1. anomaly_visualizations_fixed.png - Main 9-panel visualization")
print("2. individual_plots/ - Directory with individual charts")
print("3. anomaly_detection_report_fixed.txt - Detailed report")
print("4. high_priority_anomalies_fixed.csv - High priority cases")
