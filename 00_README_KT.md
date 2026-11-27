# KT Handover — Chandresh Kanyal

Start here. This file maps everything in the handover folder. Each project folder has its own README with more detail.

**This folder is the GitHub repository `github.com/ChandreshKanyal/kt` (private).** Credentials, personal data, confidential
finance files and very large files are deliberately **not** in git; [MISSING_FILES.md](MISSING_FILES.md) lists each one and where
to get it. Dedupe, the Sentinel prototype, the old Video-Analytics app and UPSRTC's `transitCodes` live in their own GitHub repos
(also listed there). Hard-coded passwords and API keys in the archived code were replaced by environment variables.
Anything marked **"Unknown – ask Chandresh"** is not stated in the files; it is collected in [Questions for the KT session](#questions-for-the-kt-session).

## Folder map

| Folder | What it is | Status | Start with |
|---|---|---|---|
| `Dedupe/` | Customer-data deduplication platform for Indian banking/insurance (match, golden record, households, human review). Python engine + FastAPI + web portal. | Working platform (portal, API, CLI); 606 tests; synthetic data only. Preview running on the shared EC2 server. | `KT_HANDOVER.md` → `docs/Technical_Overview.docx` → `README.md` → `PROGRESS.md` |
| `scraper2.0/` | Desktop tool: Redington AWS invoice PDFs → reconciled Excel. Built `.exe` only; source is in `Projects/Archive/Scraper/`. | Built Apr 2025; current use unknown | `scraper2.0/README.md` |
| `Projects/Databricks Demo/` | AI-agent prototype on Databricks Free Edition (AMI Network Health use case, DivyaNetra RFP / Adani Electricity). SQL + setup docs. | Prototype done | `README.md` |
| `Projects/LIC/` | LIC RFP: handwritten proposal-form data extraction. RFP, scope, character dataset, page images. No extraction code. (Unrelated items were moved to the Archive.) | Stage unknown | `README.md` |
| `Projects/Proposal Forms Scan/` | Scanned LIC proposal forms (test input for LIC). | Data | `README.md` |
| `Projects/Video Analytics/` | AI CCTV analytics for bank branches: 4 design docs + a working guard-alertness prototype (YOLO11 + MediaPipe, FastAPI + React). | Docs + prototype | `README.md` |
| `Projects/Archive/` | Older work: UPSRTC (bus-trip theft detection + data warehouse on AWS, with its Airflow DAGs and EBA model), OAC (Jan Aadhaar), Svakarma infra review deck, scraper **source code**, first video-analytics attempt, Zabbix, SLM, RPY, Leap. | Archived | `README.md` |
| `Access/` | `ACCESS_README.txt` and `Credentials/` (server details, Superset logins). | Live secrets | See [Access](#access-and-accounts) |

---

## Dedupe — customer data deduplication platform

- **What it is:** finds records of the same customer across many sources, joins them into one person with a stable ID and a golden
  record, links households, sends doubtful pairs to a human reviewer, and explains every decision. CPU only. Three ways to use it:
  web portal, command line / Python library (`dedupe run …`), headless REST service.
- **Client / purpose:** B2B product for Indian banking and insurance, Aurionpro-branded. No real customer or design partner yet.
  Which client or sales opportunity it is aimed at: Unknown – ask Chandresh.
- **Tech stack:** Python 3.10+ (tested 3.12); DuckDB + Parquet pipeline; NumPy (own logistic regression, EM); FastAPI + Uvicorn;
  plain-JavaScript portal; SQLite or PostgreSQL; Docker; pytest, ruff.
- **How to run:** `Dedupe/KT_HANDOVER.md` §4 (short version) and `Dedupe/README.md` §2–§6 (full reference).
- **Where it's deployed:** a shared AWS EC2 Linux server, repo `~/dedupah`; the user's portal preview is the `dedupe-preview` container
  on 127.0.0.1:8001 (reach it through an SSH port forward). The same server runs other people's services (Shankar's service on 8000,
  host PostgreSQL, Superset, gunicorn, Ollama, Zabbix agent) — **do not touch them**. Rules: `Dedupe/PROGRESS.md` → "How to work on this server".
- **Code:** GitHub `ChandreshKanyal/dedupah` (private, personal account). The KT copy was updated to GitHub's latest (24 Nov 2026)
  plus `KT_HANDOVER.md`.
- **Status:** 606 tests pass (Docker), ruff clean. Balanced settings F1 0.931 with identifiers / 0.918 without (synthetic);
  692k records in 445 s. **Synthetic data only**; no legal, compliance (DPDP, RBI KYC, IRDAI, UIDAI) or penetration test.
- **Open decisions / next steps** (from `PROGRESS.md`): make Balanced the default for new projects; next phase = integrate Shankar's
  image engine (ID-card OCR, face matching) — agree the interface first; robustness at ~5M records; smaller items listed there.
  `docs/HANDOVER_QUESTIONS.md` answers 8 handover questions about rules, results, review assignment and PAN/Aadhaar handling.
- **Rules:** never store raw Aadhaar; keep and back up `DEDUPE_TOKEN_KEY`; credentials only via environment variables; after each
  change update `docs/DEVELOPMENT_LOG.md` and `PROGRESS.md`, run pytest + ruff, commit.

## scraper2.0 — Redington AWS invoice reconciliation tool

- **What it is:** Windows `.exe` (PyInstaller). Reads Redington (AWS reseller) invoice PDFs, extracts invoice no./date/items/GST/total/INR rate/AWS account ID,
  joins to a master Excel by AWS account ID, writes a timestamped Excel.
- **Client / purpose:** internal finance reconciliation of AWS invoices. Which team uses it and how often: Unknown – ask Chandresh.
- **Tech stack:** Python, pdfplumber, pandas, tkinter, PyInstaller.
- **How to run:** double-click `scraper2.0/scraper/scraper.exe`, pick the PDF folder, then the master Excel. Rebuild from
  `Projects/Archive/Scraper/scraper.py` with `pyinstaller scraper.spec`.
- **Where deployed:** nowhere; runs on a user's PC.
- **Status / issues:** exe is identical to the April 2025 build in Archive; why it is called "2.0": Unknown – ask Chandresh. Parsing depends on the
  exact PDF layout (first page only). `FW_ Redington Working Period April-26/` holds reconciliation workbooks with confidential finance data.

## Databricks Demo — AMI Network Health Monitoring Agent

- **What it is:** prototype AI agent to estimate agent-building effort. Medallion tables (bronze/silver/gold) on synthetic meter data,
  SQL tool functions, AI Playground agent, Genie Space, dashboard, SQL Alert + Lakeflow Job.
- **Client / purpose:** DivyaNetra RFP, Adani Electricity Mumbai Ltd., Appendix-1 Wave-1 use case #5.
- **Tech stack:** Databricks Free Edition, Unity Catalog SQL, AI Playground, Genie, AI/BI Dashboard, Lakeflow Jobs.
- **How to run:** run `rebuild_medallion_clean.sql` in the SQL Editor, then the setup docs, then `demo_script.md`.
- **Where deployed:** a Databricks Free Edition workspace. Whose account: Unknown – ask Chandresh.
- **Status / issues:** prototype done. **The agent prompt, demo script and Genie notes are out of sync with the final SQL** (they describe
  4 gateways / 6 days and a `compare_first_last_day` tool that the final script drops; the SQL now builds 16 gateways × 2 years and
  `compare_recent_window`). Update the prompt before any demo. App export blocked by a dependency bug in Databricks' template (demo
  uses Playground). Whether the demo happened and the outcome: Unknown – ask Chandresh.

## LIC — handwritten proposal form data extraction

- **What it is:** response to LIC RFP ref. LIC/CO/ITDT/RISE/2526/AI-006/HPDE (29 Jan 2026): extract handwritten data from proposal
  forms into JSON with confidence scores, plus HITL review, mobile capture SDK and form redesign. Qualification (pass/fail Techathon):
  ≥95% field accuracy, ≥97% character accuracy, ≤5% rejected, ≤10% manually corrected; award to lowest price among qualifiers.
- **Client:** Life Insurance Corporation of India.
- **Tech stack:** per the RFP, Vision-LLM / multimodal IDP hosted in India (MeitY cloud). In the folder: a 65-class handwritten
  character dataset and 201 scanned page images. (A scikit-learn model found here turned out to be an unrelated auto-glass
  pricing model; it was moved to `Archive/Unsorted/car-glass-model/`.)
- **How to run:** no extraction code or instructions in the folder. Where the code is: Unknown – ask Chandresh.
- **Where deployed:** Unknown – ask Chandresh. Access to LIC's network uses the SSL-VPN profile in this folder.
- **Status:** RFP dates were Feb 2026 (submission 20 Feb, demos 23-27 Feb). Bid/Techathon outcome: Unknown – ask Chandresh.
- **Still in this folder but not LIC work:** an AI-chat data export zip (likely personal) — decide whether to remove.

## Proposal Forms Scan

- 15 image-only scanned LIC proposal forms (incl. `Empty Form.pdf`, `Real Doc.pdf`, `Need Fix.pdf`). Test input for LIC.
- Whether they contain real customers' data, and what is wrong with `Need Fix.pdf`: Unknown – ask Chandresh.

## Video Analytics — AI CCTV analytics for bank branches

- **What it is:** design pack for a 13-use-case branch CCTV analytics platform (handbook, architecture, execution SOP, MLOps) and a
  prototype, **"Sentinel Analytics"**: multi-camera guard monitoring (absent / slouching / sleeping / on phone), guard face enrolment
  and recognition, footfall counting, alert video clips, login with roles; plus a separate weapon-detection demo.
- **Client:** a bank; survey file is named "BOB-AI based CCTV Solution-Survey". Which bank and engagement stage: Unknown – ask Chandresh.
- **Tech stack:** YOLO11m + custom guard model, MediaPipe Pose, facenet-pytorch, DeepSORT, OpenCV, PyTorch (GPU), FastAPI + WebSocket,
  SQLite, JWT, React + Vite; dataset labelled in Roboflow.
- **How to run:** Linux `./start.sh` (builds the frontend, serves everything on :8000) after installing requirements **plus several
  packages missing from `requirements.txt`** (list in the README); Windows dev: `start.ps1`. Set `SENTINEL_SECRET_KEY` and change the
  seeded admin password on first sign-in.
- **Where deployed:** where it runs today: Unknown – ask Chandresh. Code on GitHub `ChandreshKanyal/surveillance-alert-analytics-cv`
  (personal account); KT copy updated to GitHub's latest (Aug 2026) plus Chandresh's upload/Windows-script commit. A branch
  `shankars-edits` exists.
- **Status / next steps:** see `Projects/Video Analytics/README.md` §5–6 (security defaults to remove, `.env` not git-ignored, gate
  model missing from the repo, retrain on varied footage). Full-platform roadmap in `doc3` (~26–32 weeks to a 3–5 branch pilot).

## Archive

See `Projects/Archive/README.md`. Highlights:
- **UPSRTC** (largest): client's AFC ticketing DB → EC2 Postgres → S3 → Redshift (`transit-da-cluster`, ap-south-1) via Airflow DAGs →
  master tables → anomaly ensemble (IQR income + IQR passengers + IsolationForest, 2-of-3 vote) → rule engine (holiday/weekend/weather/
  incident → Warning, else Alert). Extraction and warehouse done; weather/incident APIs and route-optimisation model not finished.
  **If the AWS resources still exist they cost money while running.**
- **Presentation/** includes a **Svakarma** project review (OMNIFIN + Svakarma on AWS, account migration, jump server, DR pending).
- **OAC/** Jan Aadhaar enrolment dashboards (Oracle Analytics); **Scraper/** is the scraper2.0 source; Zabbix, SLM, RPY, Leap notes.
Status of each: Unknown – ask Chandresh.

---

## Access and accounts

Credential values are **not** copied here. Rotate every password listed below after handover and get personal accounts where possible.

| Access | Where it is described | Notes |
|---|---|---|
| EC2 server (Dedupe + Superset + others) | `Dedupe/PROGRESS.md` → "How to work on this server" | SSH as `chandresh`; inbound port 22 is open only to Chandresh's IP, so the security group needs your IP. Your own SSH key/user is needed. |
| Dedupe server secrets | Server file `~/dedupah/.env` (not in this folder) | Postgres user/password, auth secret, `DEDUPE_TOKEN_KEY`. Back up the token key. |
| Dedupe portal admin (server) | Created on the server; password chosen privately | Create your own admin with `accounts_cli create-admin`. |
| Airflow server + a database connection | `Access/Credentials/Server Details.txt` | Public IP, login, Airflow admin-user command and URL, DB host/port/name/user/password. |
| Apache Superset | `Access/Credentials/Superset Credentials.txt` | Superset logins, a root login and the commands to start Superset. |
| Remote Desktop | `Default.rdp` (kept in Chandresh's Documents, not in this folder) | Target machine: Unknown – ask Chandresh. |
| LIC SSL-VPN | `Projects/LIC/sslvpn-hcsteam-client-config.ovpn` | Contains an embedded private key + certificate and asks for a username/password. Request your own VPN account. |
| Oracle Analytics (dev/UAT) + VPN | `Projects/Archive/Presentation/Oracle Credentials.txt` | Old OAC work. |
| GitHub repos | `ChandreshKanyal/dedupah`, `ChandreshKanyal/surveillance-alert-analytics-cv`, `ChandreshKanyal/Video-Analytics` | Personal account. Transfer to a company organisation. |
| AWS (S3, Redshift, EC2, IAM roles) | Code in Archive/UPSRTC, Airflow Codes | Which AWS account(s) and how you get console access: Unknown – ask Chandresh. |
| Databricks Free Edition | — | Account owner unknown. |
| Roboflow workspace | `annotated_data/data.yaml` in the surveillance repo | Workspace owner/login unknown. |

## Risks to fix before sharing this folder

**Secrets in files (rotate, then remove or move to a vault):**
- `Access/Credentials/*.txt` — live server, DB and Superset credentials.
- `Projects/LIC/sslvpn-hcsteam-client-config.ovpn` — embedded VPN private key.
- `Projects/Archive/Presentation/Oracle Credentials.txt` — VPN and Oracle logins.
- **Fixed on 2026-11-27 (now read from environment variables / placeholders):** UPSRTC `scripts/utils/redshift.py` and
  `scripts_later_version.zip` (Redshift password; the original zip is kept locally, out of git), EBA `Rule Engine.ipynb`
  (DB password; outputs cleared), UPSRTC `API Work/` (weather/news API keys), Zabbix install note (password).
  **The old values are still valid until rotated** — rotate the Redshift password and both API keys.
- `Dedupe/src/dedupe/config/settings.py` — a default dev database URL with a password (dev default; confirm it is not used anywhere real).

**Personal or sensitive data:**
- `Projects/LIC/data-…-batch-0000.zip` — an AI-chat account export (conversations); likely personal.
- `Projects/Proposal Forms Scan/Real Doc.pdf` (and possibly others) — may be a real customer's proposal form.
- `Projects/Video Analytics/Surveillance/IMG_2865.MOV` (2.8 GB) — source footage of people for the guard model.
- `Projects/Archive/OAC/Enrollment_detailed_data.csv` and `Enrollment First Sheet Data.zip` — Jan Aadhaar enrollment data.
- `Projects/LIC/Character Dataset/images/` — 201 page images split from scanned proposal forms; may contain customer data.
- `Projects/Archive/EBA Docs/` result CSVs and README — name individual conductor/driver IDs as "suspicious" (personnel data).
- `Projects/Archive/EBA Docs/sagemaker-ai-workshop-_teams_2025-08-12.csv` — AWS workshop team codes, join links and account IDs.
- `scraper2.0/FW_ Redington Working Period April-26/` and `Projects/Archive/Scraper/*Invoices*` — confidential finance data.
- `Projects/Archive/Presentation/Chandresh's Part.pptx`, `Scraper- Chandresh.pptx` — personal work slides (probably fine; check).

**Cleanup already done (2026-11-27):** removed `scraper2.0.zip`, `Projects/LIC/guard_model.pt`, the duplicate LIC RFP copy,
`Projects/Archive/Scraper/dist` and `build`, and every virtualenv / `node_modules` / cache folder (recreate them with the install
steps in each README). Moved `LIC/scrippts.zip` → `Archive/UPSRTC/scripts_later_version.zip` and the auto-glass model →
`Archive/Unsorted/car-glass-model/`.

**Still to decide:** two different `character_dataset_2.zip` files in LIC; `Projects/Archive/Scraper/pdf_scraper/` (older build);
`Projects/Databricks Demo/.claude/`; `Projects/Archive/SLM - Shortcut.lnk`.

---

## Questions for the KT session

**General**
1. Who is the receiving owner for each project, and which projects are still active vs. closed?
2. Should the three GitHub repos be transferred to a company organisation (and who owns that org)?
3. Which AWS account(s) host the EC2 server, S3 and Redshift, and how does the new owner get console/IAM access?
4. What does `Default.rdp` connect to, and does the new owner need it?

**Dedupe**
5. Which client or sales opportunity is Dedupe for, and who is the business sponsor?
6. Should new projects default to Balanced? Who agrees the image-engine interface with Shankar? Where is the `docker run` command for the preview (only in the assistant's notes on the server)?
7. Where is the backup of the server's `DEDUPE_TOKEN_KEY` and `.env`?
8. Answers to the three retention/erasure questions (are we the processor; may backups expire; machinery only?).
9. Is the Airflow server in `Server Details.txt` the same EC2 machine as Dedupe?

**scraper2.0**
10. Who uses the scraper, how often, and what does "2.0" change versus the Archive build (the exe is identical)?
11. Is the Redington April-26 reconciliation finished, and who receives it?

**Databricks Demo**
12. Whose Databricks account holds the workspace? Was the DivyaNetra demo delivered, and what was the outcome?

**LIC**
13. Was the bid submitted, and what happened at the Techathon (accuracy achieved)?
14. Where is the extraction code? What are the `A2–Z2` classes in the character dataset? Which project does the auto-glass model (`model*.joblib/.pkl`) belong to?
15. Should the AI-chat export zip be removed from `LIC/`?
16. Who issued the SSL-VPN profile, and how does the new owner get their own?

**Proposal Forms Scan**
17. Are any of the forms (especially `Real Doc.pdf`) real customer data? What needs fixing in `Need Fix.pdf`?

**Video Analytics**
18. Which bank is "BOB", and what stage is the engagement at?
19. Where are the training images and which GPU machine was used for training? Who owns the Roboflow workspace?
20. Where does Sentinel run today? Where is the gate segmentation model? What should happen to the `shankars-edits` branch?
21. Can `IMG_2865.MOV` be shared (people in it, consent)?

**Archive**
22. Is any archived project still live (UPSRTC pipeline, Airflow DAGs, Redshift cluster, Superset dashboards, OAC/Jan Aadhaar, Zabbix)? Are the AWS resources stopped?
23. Can the archived credentials and personal-data files be deleted?
24. Is Svakarma (infra/AWS review deck in `Presentation/`) still a responsibility to hand over?
25. What do "EBA", "RPY" and "Leap" refer to (clients/projects)?

**Databricks Demo (extra)**
26. Should the agent prompt be updated to the final SQL (16 gateways, `compare_recent_window`), or is the demo closed?
