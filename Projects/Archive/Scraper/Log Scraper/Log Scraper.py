import pandas as pd
import re
from loguru import logger

def extract_log_values(file_path, keywords):
    log_data = []
    found_keywords = {key: False for key in keywords}  # Track if any keyword was found

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            log_entry = {}

            # Always extract Date, Time, and Session ID
            date_match = re.search(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}\.\d{3}) IST \[(\d+)\]", line)
            if date_match:
                log_entry["Date"] = date_match.group(1)
                log_entry["Time"] = date_match.group(2)
                log_entry["Session ID"] = date_match.group(3)

            # Extract user-defined keywords dynamically
            for keyword in keywords:
                keyword_regex_patterns = [
                    rf"{keyword}:\[(.*?)\]",     # Matches u:[value]
                    rf"{keyword}:\s*(\S+)",      # Matches u: value
                    rf"{keyword}=(\S+)",         # Matches u=value
                    rf"{keyword}\s*<([^>]*)>",   # Matches u <value>
                    rf"{keyword}\s*:\s*(.*?)(?:\s|$)"  # Matches u: value (even if space after)
                ]

                match = None
                for pattern in keyword_regex_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        break  # Stop at first match

                # Special handling for "execute" command (since it often appears differently)
                if keyword.lower() == "execute":
                    match = re.search(r"execute\s+<unnamed>:\s+(.*)", line, re.IGNORECASE)
                
                if match:
                    log_entry[keyword] = match.group(1).strip()
                    found_keywords[keyword] = True  # Mark keyword as found
                else:
                    log_entry[keyword] = ""  # Keep blank if not found

            log_data.append(log_entry)

    # Convert dictionary to Pandas DataFrame
    df_logs = pd.DataFrame(log_data)

    # Display DataFrame
    if df_logs.empty:
        logger.warning("No matching log entries found for the given keywords.")
        return df_logs

    # Warn user if a keyword was not found in any log entry
    for key, found in found_keywords.items():
        if not found:
            logger.warning(f"⚠ Warning: Keyword '{key}' was not found in any log entries.")

    return df_logs

# Ask user for any words they want to extract
user_input = input("Enter the words you want to extract (comma-separated, e.g., u, db, c, execute, duration): ").split(",")
keywords_to_extract = [field.strip() for field in user_input if field.strip()]

if not keywords_to_extract:
    logger.error("Invalid keywords provided. Please enter valid log words.")
else:
    # Path to log file (Change this to your actual file path)
    log_file_path = 'C:/Users/chandresh.kanyal/Downloads/log_file_1.log'

    # Run log extraction function
    df_logs = extract_log_values(log_file_path, keywords_to_extract)

    if not df_logs.empty:
        print("\nExtracted Log Data (Top 10 Rows):\n")
        print(df_logs.head(10).to_string(index=False))  # Print only top 10 rows without index
