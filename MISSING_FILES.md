# Files not stored in this repository

This repository holds everything in the KT handover folder **except** the items below. They were left out on purpose (see
`.gitignore`) because they are credentials, personal data, confidential finance documents, too large for GitHub, or live in
their own repositories. They exist in Chandresh's original KT folder; get them through a secure channel (company shared drive,
direct copy), never by email or chat, and never commit them.

## Projects with their own GitHub repositories

| Folder | Repository |
|---|---|
| `Dedupe/` | `github.com/ChandreshKanyal/dedupah` (private) — clone it into `Dedupe/` |
| `Projects/Video Analytics/Surveillance/surveillance-alert-analytics-cv/` | `github.com/ChandreshKanyal/surveillance-alert-analytics-cv` |
| `Projects/Archive/Video-Analytics/` | `github.com/ChandreshKanyal/Video-Analytics` |
| `Projects/Archive/UPSRTC/transitCodes/` | `github.com/ChandreshKanyal/TransitProject` (UPSRTC anomaly ensemble scripts) |

## Credentials and secrets (rotate them after handover)

| Item | What it is |
|---|---|
| `Access/Credentials/Server Details.txt` | Airflow server and a database connection (address, logins) |
| `Access/Credentials/Superset Credentials.txt` | Superset logins and start commands |
| `Projects/LIC/sslvpn-hcsteam-client-config.ovpn` | VPN profile with an embedded private key |
| `Projects/Archive/Presentation/Oracle Credentials.txt` | VPN and Oracle Analytics dev/UAT logins |
| `Projects/Archive/Presentation/Original.pptx` | Full Svakarma review deck including a client server inventory with IP addresses (`Chandresh's Part.pptx` in the repo has the same review without that slide) |
| `Projects/Archive/UPSRTC/scripts_later_version_ORIGINAL.zip` | Original zip with a hard-coded Redshift password (the repo has a cleaned copy) |

Code that used hard-coded credentials now reads environment variables instead:
`REDSHIFT_HOST`, `REDSHIFT_PORT`, `REDSHIFT_DB`, `REDSHIFT_USER`, `REDSHIFT_PASSWORD` (UPSRTC `scripts/utils/redshift.py`, the cleaned
zip, EBA `Rule Engine.ipynb`), `WEATHERAPI_KEY` and `NEWSDATA_API_KEY` (UPSRTC `API Work/`). The Zabbix note now shows placeholders.

## Personal data

| Item | Why excluded |
|---|---|
| `Projects/Proposal Forms Scan/*.pdf` (except `Empty Form.pdf`) | Scanned insurance proposal forms; may be real customers' data |
| `Projects/LIC/trial.pdf` | Sample proposal form; may be filled in |
| `Projects/LIC/Character Dataset/images/` | 201 page images split from scanned proposal forms |
| `Projects/LIC/data-…-batch-0000.zip` | An AI-chat account data export (private conversations) |
| `Projects/Video Analytics/Surveillance/IMG_2865.MOV` | 2.8 GB video of people (also above GitHub's size limit) |
| `Projects/Archive/OAC/Enrollment_detailed_data.csv`, `Enrollment First Sheet Data.zip` | Jan Aadhaar enrolment records |
| `Projects/Archive/OAC/postgresql-2025-02-15.log`, `…-16.log` | Database logs that may contain data (89 + 73 MB) |
| `Projects/Archive/EBA Docs/all_anomalies_with_rules*.csv`, `anomaly_results_route_225.csv`, `final_unexplained_anomalies.csv` | Trip results naming individual conductors and drivers |
| Two result CSVs inside the UPSRTC zip (`classified_anomalies_with_insights.csv`, `inference_output.csv`) | Same (removed from the cleaned zip) |
| `Projects/Archive/EBA Docs/sagemaker-ai-workshop-*.csv` | Workshop access codes and AWS account IDs |
| `Projects/Archive/Scraper/Log Scraper/User-IP.xlsx` | User names / IP addresses from application logs |
| `Projects/Archive/UPSRTC/Superset.html` + `Superset_files/` | Saved Superset session page and its page assets (server address, session content) |

The EBA `Rule Engine.ipynb` saved outputs (trip rows with staff IDs) were cleared; the code is unchanged. Staff IDs in
`EBA Docs/README_ANOMALY_DETECTION.md` were replaced with `<id redacted>`.

## Confidential finance documents

| Item | What it is |
|---|---|
| `scraper2.0/FW_ Redington Working Period April-26/` | April 2026 AWS invoice reconciliation workbooks |
| `Projects/Archive/Scraper/December Invoices/`, `March Invoices/`, `March Invoices.zip` | Sample Redington invoice PDFs and outputs |
| `Projects/Archive/Scraper/Redington India Ltd Calulation.xlsx` | Earlier master workbook |

To test the scraper you need a few real invoice PDFs and the master workbook from the finance team.

## Too large / old build output

| Item | Why |
|---|---|
| `Projects/Archive/Scraper/pdf_scraper.zip` (117 MB) | Over GitHub's 100 MB file limit; an older scraper build |
| `Projects/Archive/Scraper/pdf_scraper/` | The same older build, unzipped; rebuild from `scraper.py` if needed |

## Not kept anywhere (re-create when needed)

Virtual environments, `node_modules`, caches and `.lnk` shortcuts were deleted during cleanup or are ignored; the install steps
are in each project's README.
