import os
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import tkinter as tk
from tkinter import filedialog


# Function to select folder for PDFs
def select_directory():
    root = tk.Tk()
    root.withdraw()
    selected_directory = filedialog.askdirectory(title="Select folder containing PDF files")
    root.destroy()
    return selected_directory


# Function to select Excel file
def select_excel_file():
    root = tk.Tk()
    root.withdraw()
    selected_file = filedialog.askopenfilename(
        title="Select master file",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    root.destroy()
    return selected_file


# Process PDF data
def transform_to_desired_format(df, invoice_number):
    client_name = None
    invoice_date = None
    items = []
    total = None
    conversion = None
    aws_account_id = None

    capture_items = False

    for i, row in df.iterrows():
        content = row["Content"]

        if client_name is None and "Invoice :" in content:
            client_name = content.split("Invoice :")[0].strip()

        if invoice_date is None:
            date_match = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", content)  # Matches dates in DD.MM.YYYY format
            if date_match:
                invoice_date = datetime.strptime(date_match.group(0), "%d.%m.%Y").strftime("%d-%b-%y")

        if "DESCRIPTION" in content.upper():
            capture_items = True
            continue

        if "SERVICES USAGE" in content.upper():
            capture_items = False

        if capture_items and i > 0:
            previous_row = df.iloc[i - 1]["Content"]
            if "DESCRIPTION" in previous_row.upper():
                elements = content.split()
                if len(elements) >= 8:
                    item_description = elements[0]
                    hsn_sac = elements[2]
                    quantity = elements[3]
                    unit_price = elements[4]
                    sgst_ugst = elements[5]
                    cgst = elements[6]
                    igst = elements[7]

                    items.append({
                        "Invoice No.": invoice_number,
                        "Invoice Date": invoice_date,
                        "Item": item_description,
                        "HSN/SAC": hsn_sac,
                        "Quantity": quantity,
                        "Unit Price": unit_price,
                        "SGST/UGST": sgst_ugst,
                        "CGST": cgst,
                        "IGST": igst,
                        "AWS Account ID": aws_account_id,
                        "Conversion Rate": conversion,
                        "Total": total
                    })

        if "Invoice Total" in content:
            total_match = re.search(r"(\d+,\d+\.\d+)", content)
            if total_match:
                total = total_match.group(1).replace(",", "")

        if "toINR-" in content:
            conversion_match = re.search(r"toINR-([\d.]+)", content)
            if conversion_match:
                conversion = conversion_match.group(1)

        if re.match(r"\d{12}_(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)", content):
             aws_account_match = re.search(r"(\d{12})", content)
             if aws_account_match:
              aws_account_id = aws_account_match.group(1)

    for item in items:
        item["AWS Account ID"] = aws_account_id
        item["Conversion Rate"] = conversion
        item["Total"] = total

    return pd.DataFrame(items)


# Process all PDFs in folder
def process_pdfs_in_folder(folder_path):
    all_data = []
    errors = []

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".pdf"):
            file_path = os.path.join(folder_path, file_name)
            invoice_number = os.path.splitext(file_name)[0]

            try:
                print(f"Processing file: {file_name}")
                with pdfplumber.open(file_path) as pdf:
                    page = pdf.pages[0]
                    lines = page.extract_text().split("\n")
                    df = pd.DataFrame({"Content": lines})

                items_df = transform_to_desired_format(df, invoice_number)

                if not items_df.empty:
                    all_data.append(items_df)

            except Exception as e:
                print(f"Error processing file {file_name}: {e}")
                errors.append(f"{file_name}: {e}")

    combined_df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    return combined_df, errors


# Process Excel file
def process_excel_file(file_path):
    try:
        print(f"Reading Excel file: {file_path}")
        df = pd.read_excel(file_path, sheet_name="Data")
        required_columns = ["AWS Account Name", "Internal/External", "AWS Account ID", "Project Name-1"]

        extracted_df = df[required_columns]
        extracted_df = extracted_df.dropna(how="any").drop_duplicates()

        extracted_df["AWS Account ID"] = extracted_df["AWS Account ID"].astype(str).str.replace("\.0$", "", regex=True).str.strip()

        return extracted_df.reset_index(drop=True)

    except Exception as e:
        print(f"Error processing Excel file: {e}")
        return None


# Main function
def main():
    print("Select the folder containing the PDFs:")
    pdf_folder_path = select_directory()

    print("Select the master Excel file:")
    excel_file_path = select_excel_file()

    if pdf_folder_path and excel_file_path:
        pdf_df, pdf_errors = process_pdfs_in_folder(pdf_folder_path)

        if not pdf_df.empty:
            pdf_df["AWS Account ID"] = pdf_df["AWS Account ID"].astype(str).str.strip()

        master_table = process_excel_file(excel_file_path)

        print("\nDataFrame from PDFs:")
        print(pdf_df)

        print("\nDataFrame from Master Excel:")
        print(master_table)

        if not pdf_df.empty and master_table is not None:
            merged_df = pd.merge(pdf_df, master_table, on="AWS Account ID", how="left")

            # Define the final column order and fill static/blank fields
            final_columns = [
                "BU", "PRS No.", "Vendor Name", "AWS Account Name", "Internal/External",
                "AWS Account ID", "Project Name-1", "Invoice No.", "Invoice Date",
                "Vendor Taxable Value", "GST", "Invoice Amount", "PO/RC Details", "Month",
                "Description", "Project Pin", "Project Name", "Status"
            ]

            merged_df["BU"] = ""
            merged_df["PRS No."] = ""
            merged_df["Vendor Name"] = "REDINGTON (INDIA) LIMITED"
            merged_df["Vendor Taxable Value"] = merged_df["Unit Price"]
            merged_df["GST"] = merged_df["IGST"]
            merged_df["Invoice Amount"] = merged_df["Total"]
            merged_df["PO/RC Details"] = ""
            merged_df["Month"] = ""
            merged_df["Description"] = ""
            merged_df["Project Pin"] = ""
            merged_df["Project Name"] = ""
            merged_df["Status"] = ""

            merged_df = merged_df[final_columns]

            print("\nFinal DataFrame:")
            print(merged_df)

            current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = os.path.join(pdf_folder_path, f"{current_datetime}.xlsx")
            merged_df.to_excel(output_file, index=False)
            print(f"Final data saved to: {output_file}")

            # Automatically open the saved file
            try:
                os.startfile(output_file)
            except Exception as e:
                print(f"Could not open the file automatically: {e}")

        else:
            print("\nNo data to merge.")

        if pdf_errors:
            error_log_file = os.path.join(pdf_folder_path, f"errors_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
            with open(error_log_file, "w") as f:
                for error in pdf_errors:
                    f.write(error + "\n")
            print(f"Errors logged to: {error_log_file}")
    else:
        print("\nFile selection was canceled. Exiting.")


if __name__ == "__main__":
    main()
