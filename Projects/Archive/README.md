# Archive — older or finished work

> Handover README. Anything marked **Unknown – ask Chandresh** is not stated in the files.
> Status of each item (finished / paused / abandoned / still running somewhere): Unknown – ask Chandresh unless noted.

## Map

| Item | One line | Size of interest |
|---|---|---|
| [UPSRTC/](#1-upsrtc--bus-trip-theft-detection-and-dynamic-scheduling) | UP State Road Transport Corp.: data warehouse on AWS + theft (anomaly) detection + dynamic scheduling design | **Largest project** |
| [Airflow Codes/](#2-airflow-codes) | Airflow DAGs that run the UPSRTC data pipeline on AWS | Part of UPSRTC |
| [EBA Docs/](#3-eba-docs) | Earlier bus-trip anomaly model + results + rule-engine notebook (UPSRTC data) | Part of UPSRTC |
| [OAC/](#4-oac--jan-aadhaar-dashboards) | Oracle Analytics dashboards on Jan Aadhaar enrolment data | Small |
| [Presentation/](#5-presentation) | Svakarma infra review deck, Data-practice scraper pitch, RBI/Morningstar PDF-to-Excel notebooks | Small |
| [Scraper/](#6-scraper) | **Source code** of the Redington invoice tool in `KT/scraper2.0/` + log scrapers | Needed by scraper2.0 |
| [Video-Analytics/](#7-video-analytics-first-attempt) | First guard-monitoring prototype (Streamlit) | Superseded |
| [SLM/](#8-slm) | FLAN-T5 chatbot and PDF Q&A notebooks | Experiments |
| [RPY/](#9-rpy--easymorph) | EasyMorph ETL how-to and workflow files | Small |
| [Zabbix/](#10-zabbix) | Zabbix install/uninstall notes and monitoring matrix | Small |
| [Leap/](#11-leap) | Pendo mobile SDK integration guide | Small |
| [Unsorted/](#12-unsorted) | Car-glass pricing model found in LIC (unrelated) | Small |
| [Loose files](#13-loose-files) | AI hardware benchmark, AWS services catalogue, demo SQL | Small |

---

## 1. UPSRTC — bus-trip theft detection and dynamic scheduling

**Client:** Uttar Pradesh State Road Transport Corporation (UPSRTC). Conductors issue tickets on offline handheld machines
(ETIMs) and sync at the end of the day; the client's AFC (automatic fare collection) system is a PostgreSQL database.

**Goals (from the docs):**
1. **Theft analysis** (`UPSRTC- Use Case - Theft Analysis.docx`): detect conductors pocketing fares (12 scenarios: no ticket, one ticket for many, under-reporting, wrong discounts…). Method: ML flags trips with unusually low passengers or low fare for the passengers, then a **rule engine** explains them away (weekend, holiday, event, weather, breakdown, ETIM log mismatch). Explained → *Warning*; unexplained → *Alert / theft*.
2. **Dynamic scheduling** (`Dynamic Scheduling.docx`, `Use Cases DS.docx`): adjust trips for festival demand, accidents/road blocks (Google Maps API), weather (OpenWeatherMap / IMD), and route profitability (revenue per km). `Conditions and Rules.docx` has the capacity rule (accept passengers up to 1.6 × 50-seat capacity per trip).
3. `Model R&D.txt`: candidate SageMaker JumpStart regressors (TabTransformer, AutoGluon, CatBoost, LightGBM).

**Architecture as built:**
```
client AFC PostgreSQL --(SP_SRCDATAEXTRACT: COPY tables to CSV, full/incremental)--> EC2 Postgres (schema snapshot_1)
  --(Airflow DAG)--> S3 bucket (test-airflow-chan) --COPY--> Redshift cluster transit-da-cluster (ap-south-1)
  --(stored procedures merge_transaction_master_1, merge_route_master ...)--> master tables (raw_data.mst_*)
  --> ensemble anomaly model (scripts/ml) --> rule engine --> classified anomalies --> Superset dashboards
```
- Master tables and column mappings: `Data Mapping.xlsx`, `Mapping.xlsx`, `UPSRTC Project Status.xlsx` (sheet Mapping) — route, region, vehicle, schedule, transaction master (`MST_ROUTE_TXN`: trip, waybill, income, passengers, conductor/driver IDs, bus plate), weather, news.
- SQL: `MST_TM SP.sql` (transaction-master merge), `ROUTE_MASTER.SQL`, `OLD_MST_RM.txt`, `Final Extraction Procedure (1)` (config-driven extraction procedure), `New folder/` (calendar, create, procedure), `../Demo Execution Instruction.sql` (inserts one demo trip into raw tables to show the flow live).
- `Superset.html`: saved Superset SQL Lab page (Superset ran on port 8088 of a server).

**Model (`scripts/ml/`):** `AnomalyDetectionEnsemble` = IQR outlier on income + IQR outlier on passengers + IsolationForest on
(month, year, day, day of week, income, passengers); a trip is anomalous when **2 of 3** agree. `ensemble_model.py` trains on an
S3 extract and saves `ensemble_model.joblib`; `inference_code.py` scores a new S3 file → `inference_output.csv`;
`rule_engine.py` joins with `incidents.csv`, `up_calendar.csv`, `weather_alerts.csv` (± day windows, weekends, bridge days) and writes
Warning/Alert with a plain-English insight per trip. `scripts/ingest/` runs the merge procedure and UNLOADs new rows to S3.
`final_anomaly_ensemble.py` / `ensemble_model_codes/` are earlier versions.
A later copy of `scripts/` (with `final_push.py`, the trained `.joblib` and sample CSVs) is `UPSRTC/scripts_later_version.zip`
(moved here from `Projects/LIC/`; also contains the hard-coded Redshift password).

**Status (from `UPSRTC Project Status.xlsx`):** extraction from the AFC DB, S3 upload, Redshift tables, mappings, incremental logic,
tracking table, error log, consolidated procedure: **Completed**. Weather API: identified (weatherapi.com), table/script pending.
Incident API, fuel API, Talend-style automation: **Not started**. Route-optimisation model: not started per the sheet.
Theft model + rule engine: built (code above). Whether UPSRTC is live, paused or closed: Unknown – ask Chandresh.

**How to run (if the AWS resources still exist):**
1. In Airflow, trigger `start_all_aws_services` (starts the EC2 instance, resumes the Redshift cluster, starts SageMaker notebook `transit-db-notebook`).
2. Trigger `etl_multi_table` or `full_dag_trial` (Postgres → S3 → Redshift → `CALL merge_transaction_master_1()`).
3. `cd scripts && python ml/ensemble_model.py` (train) → `python ml/inference_code.py` → `python ml/rule_engine.py` (needs `ensemble_output.csv`, `incidents.csv`, `up_calendar.csv`, `weather_alerts.csv` in the working folder). Needs AWS credentials (boto3) and Redshift access.
4. **Stop/pause the Redshift cluster and EC2 afterwards** — they cost money while running.

**Problems to fix:** `scripts/utils/redshift.py` hard-codes the Redshift host/user/password (move to env vars / Airflow connection); `API Work/` scripts hard-code API keys; S3 paths and IAM role ARNs are hard-coded; `rule_engine.py` reads local CSVs, not Redshift.

## 2. Airflow Codes

UPSRTC orchestration DAGs (tag `transit`, all manual-trigger): `turn_on_instances.py` (`start_all_aws_services`),
`postgres_to_s3_to_redshift.py.py` (`load_existing_table_to_redshift`, one table), `etl_multi_table.py` (`etl_multi_table`, 5 AFC tables into
`demo.*_demo`), `call_procedure.py` (`run_redshift_procedure`), `full_dag.py` (`full_dag_trial`: start services → extract → S3 → Redshift → merge).
Airflow connections expected: `postgres_ec2`, `redshift_conn`, `aws_default`. The Airflow server's address and login are in
`KT/Access/Credentials/Server Details.txt`. Whether this Airflow is the same EC2 machine that now hosts Dedupe: Unknown – ask Chandresh.

## 3. EBA Docs

Earlier, standalone version of the UPSRTC theft model (what "EBA" stands for: Unknown – ask Chandresh).
`README_ANOMALY_DETECTION.md` describes it: IQR + z-score + IsolationForest + pattern rules per route, combined score 0–10 (≥3 anomaly, ≥5 high
priority); run on **2,080,312 trips → 47,099 anomalies, 18,084 high priority**. `anomaly_detection_model.py`, `visualize_anomalies_fixed.py`,
`anomaly_model_route_8.pkl`, result CSVs (`all_anomalies_with_rules*.csv`, `final_unexplained_anomalies.csv`, `anomaly_results_route_225.csv`),
`forecast_routes_30days.csv` (predicted passengers and recommended trips per route), `busy routes (1).csv`, `Rule Engine.ipynb` (Redshift
queries + rules; **hard-coded password**). `sagemaker-ai-workshop-_teams_2025-08-12.csv` is a list of AWS workshop team codes/join links, unrelated.
**Sensitive:** results name individual conductor and driver IDs as "suspicious" — handle as personnel data.

## 4. OAC — Jan Aadhaar dashboards

Oracle Analytics (OAC/OAS) work on **Jan Aadhaar** enrolment data (Rajasthan; sample rows are from Ajmer district): enrolment counts by
district → block/city → GP/ward → village, rural/urban, by date. Files: DV projects `Jan Aadhaar v1.0.dva`, `v2.0.dva` (+ PDF exports),
table DDL (`Create Commands/`, `ADMIN.*`, `*.LOCATION_HIERARCHY.txt` for row-level security by user), `LEVEL_ID.sql` (aggregation table),
`Enrollment_detailed_data.csv` (34 MB) and `Enrollment First Sheet Data.zip` (6 Excel extracts), and two large PostgreSQL logs (Feb 2025).
Logins for the Oracle dev/UAT environment are in `Presentation/Oracle Credentials.txt`.
**Sensitive:** enrolment IDs are government-scheme identifiers — treat the CSV/zip as personal data; the PostgreSQL logs may contain queries with data.

## 5. Presentation

- `Chandresh's Part.pptx` / `Original.pptx`: **Svakarma project review** for the client's IT leadership — Svakarma and OMNIFIN on AWS (prod/UAT/dev: OMNIFIN DB, app server with ESB/Core/ALF, web, jump and security servers, RDS Postgres), migration of Svakarma from an old AWS account to the company's AWS account, issues (site not reachable globally, jump-server RDP licences, DR/BCP pending, password expiry notices), and the HCS service-desk/ITIL process. Whether Svakarma is still your responsibility: Unknown – ask Chandresh. (A "SvaKarma" shortcut also exists on Chandresh's Documents.)
- `Scraper- Chandresh.pptx`: Data-practice pitch for a web-crawling / document-parsing / reporting service.
- `Appendix Table 3/`, `Statement- 21/`, `Statement- 23/`: notebooks that download RBI "State Finances: A Study of Budgets" PDFs and convert tables to Excel (public data).
- `Use Case- 2/`: tabula PDF-table extraction of a Morningstar report.
- `Oracle Credentials.txt`: **secret** (VPN + Oracle Analytics dev/UAT logins). Do not share.

## 6. Scraper

- `scraper.py` + `scraper.spec`: source of `KT/scraper2.0/scraper/scraper.exe` (see `KT/scraper2.0/README.md` for use and rebuild). The duplicate `dist/` and `build/` output was removed; rebuilding recreates them.
- `pdf_scraper/` (+ `pdf_scraper.zip`): an older/different build (`Scraper.exe`, not identical).
- `December Invoices/`, `March Invoices/` (+ zip): sample Redington invoice PDFs and outputs — confidential finance data.
- `Redington India Ltd Calulation.xlsx`: earlier master workbook.
- `Log Scraper/`: `Log Scraper.py` / `User-IP Scraper.py` pull date, time, session and chosen keys (e.g. user, IP) out of application logs into Excel (`User-IP.xlsx`). Which system's logs: Unknown – ask Chandresh.

## 7. Video-Analytics (first attempt)

Streamlit app (`app.py`) + `ml_engine.py` (`GuardMonitoringEngine`: YOLOv8n person detection + MediaPipe pose → alertness, posture,
attention, position, turnout scores) + `config.py` (speed/balanced/accuracy profiles). Repo `github.com/ChandreshKanyal/Video-Analytics`
(one commit, 2026-02-12). Run: `pip install streamlit ultralytics mediapipe opencv-python` then `streamlit run app.py`.
**Superseded** by `Projects/Video Analytics/Surveillance/`. (Its virtualenvs were removed; recreate one if you need to run it.)

## 8. SLM

Notebooks: `SLM.ipynb` (google/flan-t5-small chatbot in Gradio), `FLAN T5.ipynb` and `Chatbot.ipynb` (PDF Q&A: PyMuPDF text → chunks →
sentence-transformers embeddings → cosine similarity → FLAN-T5 answer, Gradio UI). Run in Jupyter/Colab; first cells install packages.
Purpose / client: Unknown – ask Chandresh.

## 9. RPY — EasyMorph

Step-by-step guide (`EasyMorph.docx/.pdf`, `RPY_EasyMorph.docx/.pdf`: connect DB → merge → derived columns → report → PDF/Excel export →
pivot/unpivot) and workflow files `EM_Trial_Run.morph`, `TRIAL RUN.morph`, `final_run.morph` (open in EasyMorph Desktop).
What "RPY" is and who the report is for: Unknown – ask Chandresh.

## 10. Zabbix

`Zabbix greenfield installation.txt` (Zabbix 7.4 on Ubuntu 22.04 with MySQL + Apache; **contains a DB password**),
`Uninstalling Zabbix.txt` (full removal steps), `Zabbix Capabilities.xlsx` (monitoring matrix: servers, network, storage, VMware, EC2,
databases, web servers, UPS/PDU/sensors with KPIs and thresholds). A Zabbix agent runs on the Dedupe EC2 server (see
`Dedupe/PROGRESS.md`, "How to work on this server"). Which Zabbix server it reports to: Unknown – ask Chandresh.

## 11. Leap

`Pendo.docx`: prerequisites and best practices for integrating the Pendo analytics SDK in Android/iOS apps (initialise early, identify
users, track events, test online/offline). Client "Leap": Unknown – ask Chandresh.

## 12. Unsorted

`Unsorted/car-glass-model/`: a scikit-learn 1.0.2 ExtraTreesRegressor pipeline (features: year, auto-glass type, make, model,
number of doors, car features) — an auto-glass / car price model — plus `convert_model.py`, which re-saves the joblib as a plain
pickle (paths point to a Downloads folder). Found in `Projects/LIC/`, unrelated to LIC. Which project it belongs to: Unknown – ask Chandresh.

## 13. Loose files

- `AI_Inference_Benchmark.xlsx` (Feb–Mar 2026): inference benchmark of an NVIDIA L4 GPU server (850/1000), M1 MacBook Pro (535), HP ProBook Snapdragon X Elite with NPU on (423) / off (290), HP ProBook AMD (300), Dell Latitude Intel (256), with a device recommendation per use.
- `Aws Services.xlsx`, `Aws Services Modified.xlsx`: catalogue of ~420 AWS services marked data-related or not, grouped (storage, database, analytics, AI…) with plain-language descriptions, use cases and limitations.
- `Demo Execution Instruction.sql`: inserts one demo UPSRTC trip into the raw tables (see §1).
- `SLM - Shortcut.lnk`: Windows shortcut that only works on Chandresh's laptop — delete.

## Before sharing this folder

Remove or vault: `Presentation/Oracle Credentials.txt`; `UPSRTC/scripts/utils/redshift.py`; `EBA Docs/Rule Engine.ipynb`;
`UPSRTC/API Work/` (`api_trial/api_trial.py`, `api_trial/news_api.py`, `from datetime import datetime, timedelta.py` — API keys);
`Zabbix/Zabbix greenfield installation.txt`, `UPSRTC/scripts_later_version.zip`. Personal data: `OAC/Enrollment_*`, OAC PostgreSQL logs,
EBA results naming staff IDs.
