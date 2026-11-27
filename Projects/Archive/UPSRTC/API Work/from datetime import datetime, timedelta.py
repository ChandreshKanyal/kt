import os
import requests
import csv

# Define the API URL
url = f'https://newsdata.io/api/1/latest?apikey={os.environ["NEWSDATA_API_KEY"]}&q=Uttar Pradesh Accident'

# Send a GET request to the API
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()  # Parse the JSON response

    # Get the first 10 articles
    articles = data.get('articles', [])[:10]

    # Define the CSV file name
    csv_file = 'pizza_articles.csv'

    # Write to the CSV file
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the header row
        writer.writerow(['Title', 'Description', 'URL', 'Published At'])

        # Write the article data
        for article in articles:
            title = article.get('title', 'No title')
            description = article.get('description', 'No description')
            url = article.get('link', 'No URL')
            published_at = article.get('pubDate', 'No publish date')
            writer.writerow([title, description, url, published_at])

    print(f"Successfully saved the first 10 articles to {csv_file}.")
else:
    print(f"Error: {response.status_code} - {response.text}")
