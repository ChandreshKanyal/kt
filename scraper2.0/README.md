# scraper2.0 — Redington AWS invoice → Excel reconciliation tool

> Handover README. Anything marked **Unknown – ask Chandresh** is not stated in the files.

## 1. What this is

A small Windows desktop tool for the **monthly reconciliation of AWS invoices from Redington (India) Ltd**, the reseller through
which the company buys AWS. Each AWS account gets an invoice PDF; doing the month by hand means typing each one into Excel.
The tool reads a folder of invoice PDFs, pulls out the key values, matches each invoice to its AWS account in a master
workbook, and writes one Excel sheet in the finance team's column layout.

- **Users:** finance/accounts team (who exactly and how often: Unknown – ask Chandresh).
- **Status:** built as a `.exe` (build of 2 Apr 2025); the April 2026 working files suggest it was still used in 2026, but current use is unconfirmed. Why it is called "2.0": Unknown – ask Chandresh (the exe is
  identical to the build of `Projects/Archive/Scraper/scraper.py` made on the same date).

## 2. Folder contents

| Item | What it is |
|---|---|
| `scraper/scraper.exe` + `scraper/_internal/` | The tool (PyInstaller one-folder build, Python 3.13). Keep the two together. |
| `FW_ Redington Working Period April-26/` | April 2026 working files: `Book1.xlsx` (invoice lines) and `Redington India Ltd Calulation.xlsx` (Summary, Pivot, Data — the master — and a USD/INR sheet). **Confidential finance data.** |

**Source code is not here.** It is `Projects/Archive/Scraper/scraper.py` (+ `scraper.spec`). That folder also has sample
invoice PDFs (`December Invoices/`, `March Invoices/`) and an older build (`pdf_scraper/`).

## 3. How to use it

1. Put the month's Redington invoice PDFs in one folder. **File name must be the invoice number** (e.g. `C240671073.pdf`); the tool uses it as "Invoice No.".
2. Double-click `scraper/scraper.exe`. A console window opens.
3. Dialog 1: choose the folder with the PDFs. Dialog 2: choose the master Excel file.
4. Output: `<YYYY-MM-DD_HH-MM-SS>.xlsx` saved **in the PDF folder** and opened automatically. If any PDF failed, `errors_<timestamp>.log` is written there too.

**Master Excel requirements:** a sheet named **`Data`** with columns `AWS Account Name`, `Internal/External`, `AWS Account ID`,
`Project Name-1` (the `Data` sheet of `Redington India Ltd Calulation.xlsx` has this layout).

**Output columns:** BU, PRS No., Vendor Name (always "REDINGTON (INDIA) LIMITED"), AWS Account Name, Internal/External,
AWS Account ID, Project Name-1, Invoice No., Invoice Date, Vendor Taxable Value, GST, Invoice Amount, PO/RC Details, Month,
Description, Project Pin, Project Name, Status. BU, PRS No., PO/RC, Month, Description, Project Pin/Name and Status are left
**blank** for the finance team to fill.

## 4. How it works (scraper.py)

- `pdfplumber` reads the **first page only** of each PDF and splits it into lines.
- From the lines it takes: invoice date (first `DD.MM.YYYY`), line items (the line right after "DESCRIPTION", needs ≥8 space-separated values: item, HSN/SAC, qty, unit price, SGST/UGST, CGST, IGST), "Invoice Total", the INR conversion rate (`toINR-<rate>`), and the 12-digit AWS account ID (line starting `<12 digits>_<MON>`).
- Joins to the master on AWS Account ID (left join). Vendor Taxable Value = unit price, GST = IGST, Invoice Amount = invoice total.
- Stack: Python, pdfplumber, pandas, openpyxl, tkinter (file dialogs), PyInstaller.

## 5. How to change and rebuild

```
cd Projects\Archive\Scraper
python -m venv .venv
.venv\Scripts\python -m pip install pdfplumber pandas openpyxl pyinstaller
.venv\Scripts\python scraper.py            # run from source
.venv\Scripts\pyinstaller scraper.spec     # rebuild -> dist\scraper\scraper.exe
```
Copy the new `dist\scraper\` folder over `scraper2.0\scraper\`.

## 6. Known limitations

- Depends on Redington's exact PDF layout; if their template changes, fields silently go missing (check the output against a few PDFs every month).
- Only the first page is read; only the first item line after "DESCRIPTION" is captured.
- Accounts missing from the master get blank account name/project.
- Invoices not named by invoice number get a wrong "Invoice No.".
- No automated tests.

## 7. Next improvements (suggestions)

- Read all pages and all line items; validate that line totals add up to the invoice total.
- Warn on AWS accounts not found in the master.
- Read the invoice number from the PDF instead of the file name.
- Keep the source in a company git repo and attach a version number to each build.

## 8. Questions for Chandresh

- Who runs this each month and who receives the output? Is the April 2026 reconciliation finished?
- What changed in "2.0"? Is `pdf_scraper/` in the Archive an older version?
