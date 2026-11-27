import pandas as pd
import re

def extract_log_values(file_path, keywords):
    log_data = []

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            log_entry = {}

            # Always extract Date and Time (ignoring Session ID)
            date_match = re.search(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}\.\d{3}) IST", line)
            if date_match:
                log_entry["Date"] = date_match.group(1)
                log_entry["Time"] = date_match.group(2)

            # Extract user-defined keywords
            for keyword in keywords:
                match = re.search(rf"{keyword}:\[(.*?)\]", line)
                log_entry[keyword] = match.group(1) if match else ""

            log_data.append(log_entry)

    # Convert dictionary to Pandas DataFrame
    df_logs = pd.DataFrame(log_data)

    # Display DataFrame
    if df_logs.empty:
        print("No matching log entries found for the given keywords.")
        return df_logs

    return df_logs

# Ask user for keywords to extract
user_input = input("Enter the keywords you want to extract (comma-separated, e.g., u, db, c, execute): ").split(",")
keywords_to_extract = [field.strip() for field in user_input if field.strip()]

if not keywords_to_extract:
    print("Invalid keywords provided. Please enter valid log keywords.")
else:
    # Path to log file (Change this to your actual file path)
    log_file_path = 'C:/Users/chandresh.kanyal/Downloads/postgresql-2025-02-16.log'

    # Run log extraction function
    df_logs = extract_log_values(log_file_path, keywords_to_extract)

    if not df_logs.empty:
        # Keep only unique combinations of extracted fields (excluding Session ID)
        unique_columns = keywords_to_extract  # Only the extracted fields
        df_unique = df_logs.drop_duplicates(subset=unique_columns)

        # Export to Excel file
        excel_file_path = "extracted_unique_pairs.xlsx"
        df_unique.to_excel(excel_file_path, index=False)

        print(f"\n✅ Extracted unique pairs have been saved to '{excel_file_path}'")

        print("\nExtracted Unique Log Data (Ignoring Session ID):\n")
        print(df_unique.to_string(index=False))  # Print all unique rows without index
