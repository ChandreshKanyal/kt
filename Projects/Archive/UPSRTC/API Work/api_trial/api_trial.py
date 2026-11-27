import os
"""import requests


api_url = "http://api.weatherapi.com/v1/alerts.json?key=<WEATHERAPI_KEY>&q=hopedale"

response = requests.get(api_url)

if response.status_code == 200:
    data = response.json() 
    print("Data fetched successfully:")
    print(data)  # Print the data to the console
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")

import csv

# Assuming 'data' is a list of dictionaries
with open('api_data.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    
    # Write headers (column names)
    writer.writerow(data[0].keys())  
    
    # Write row values
    for row in data:
        writer.writerow(row.values())

"""


import requests
import csv

# Replace this with your actual API URL
api_url = f"http://api.weatherapi.com/v1/alerts.json?key={os.environ['WEATHERAPI_KEY']}&q=hopedale"

# Fetch the JSON data from the API
response = requests.get(api_url)
data = response.json()

# Define the CSV filename
csv_filename = "api_weather_data.csv"

# Open the CSV file for writing
with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)

    # Write the header for the location
    location_keys = data['location'].keys()
    writer.writerow(location_keys)

    # Write the location data
    location_values = data['location'].values()
    writer.writerow(location_values)

    # Write a header for alerts
    alert_keys = data['alerts']['alert'][0].keys()
    writer.writerow([""] * len(location_keys) + list(alert_keys))  # Offset by location data

    # Write each alert
    for alert in data['alerts']['alert']:
        alert_values = alert.values()
        writer.writerow([""] * len(location_keys) + list(alert_values))  # Offset by location data

print(f"Data has been written to {csv_filename}")
