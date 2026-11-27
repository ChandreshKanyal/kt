# Databricks Demo — AMI Network Health Monitoring Agent

> Handover README. Anything marked **Unknown – ask Chandresh** is not stated in the files.

## 1. What this is

A prototype **AI agent on Databricks** that watches the health of a smart-meter (AMI) communication network, spots gateways
whose meter-read success rate is falling, and recommends what a human should do before billing or customers are affected.

- **Why it was built:** to measure how long it takes to build an agent on Databricks, as input to a bid/estimation decision.
- **Worked example:** use case #5, "AMI Network Health Monitoring Agent", from the **DivyaNetra RFP** (Adani Electricity Mumbai
  Ltd. / AEML, Appendix-1, Wave-1). Target sentence: *"Continuously monitors AMI network connectivity, detects degradation, and
  recommends remediation before billing or outage impact."*
- **Data:** 100% synthetic and deterministic (hash-based, not random), so every rebuild gives the same story. Nothing is
  connected to a real HES/NMS system.
- **Status:** prototype complete. Whether the demo was presented and the outcome: Unknown – ask Chandresh.

## 2. Tech stack

| Piece | Used for |
|---|---|
| Databricks **Free Edition** (login.databricks.com) | Workspace, serverless SQL warehouse, Unity Catalog (catalog `workspace`) |
| SQL Editor | Builds all tables and tool functions (no notebooks, no Python) |
| Unity Catalog SQL functions | The agent's "tools": read-only data retrieval with no judgement built in |
| AI Playground | The agent: a tools-enabled LLM + the system prompt in `agent_system_prompt.md` |
| Genie Space | Natural-language-to-SQL alternative to the agent |
| AI/BI Dashboard | Visual (trend line, snapshot table, weak-signal bar chart, recent alerts) |
| SQL Alert + Lakeflow Job | Automated, scheduled detection (no LLM involved) |

Design rule used throughout: **tables hold facts only** (no priority, confidence or recommendation columns). All judgement
is produced live by the agent/Genie from the numbers. This mirrors the RFP's split between data foundation (§2.2) and
"Agentic AI Core" (§2.2.6–2.2.8). The agent works **Human-on-the-Loop**: it recommends; a person approves any action.

## 3. Files

| File | What it is | Read when |
|---|---|---|
| `rebuild_medallion_clean.sql` | **The only script you run.** Drops old objects, rebuilds every table and function, ends with verification queries. | Setup / every demo morning |
| `agent_system_prompt.md` | System prompt to paste into AI Playground (advisory format, priority rules, HOTL rules). | Setting up the agent |
| `genie_setup_instructions.md` | Which tables to add to Genie, instruction text, example SQL Q&A. | Setting up Genie |
| `dashboard_setup.md` | The 4 dashboard widgets with their SQL. | Building the dashboard |
| `databricks_alert_and_job_setup.md` | SQL Alert + 3-task Lakeflow Job; optional Slack/Teams/email destinations. | Building automated detection |
| `demo_script.md` | 5-minute demo order, morning-of checklist, what to do if something breaks. | Before presenting |
| `databricks_app_export.md` | Exporting the agent as a Databricks App. **Parked** (Databricks template bug). | Only if you want a standalone chat UI |
| `session_summary.md` | History of the build session and lessons. **Outdated in places** (see §6). | Background |
| `.claude/settings.local.json` | Local AI-assistant setting. Not part of the project; can be deleted. | — |

## 4. What the SQL builds (current version)

Synthetic network: **16 gateways × 8 meters = 128 meters** across Western, Central and Eastern Suburbs of Mumbai, **730 days**
of daily reads ending "today" (dates are anchored to `current_date()`, so the data always looks current).

| Layer | Object | Contents |
|---|---|---|
| Bronze | `workspace.bronze.nms_topology` | Gateway → meter, area, zone, meter type, install date |
| Bronze | `workspace.bronze.hes_meter_reads` | Per meter per day: 24 scheduled reads, successful/failed reads, RSSI signal (dBm) |
| Silver | `workspace.silver.meter_daily_comm_health` | Joined meter-day facts, success %, `signal_quality_flag` (weak if RSSI < −85 dBm) |
| Gold | `workspace.gold.gateway_daily_network_health` | Gateway-day facts: `network_success_pct`, `avg_rssi_dbm`, `meters_with_weak_signal` |
| Gold | `workspace.gold.degradation_alert_log` | Append-only log written by the job (not rebuilt by the script) |

Each gateway follows a scripted scenario so every kind of situation exists:

| Scenario | Gateways |
|---|---|
| Gradual decline (the "hero" story) | GW-114 Andheri East, GW-161 Kurla |
| Mild decline | GW-137 Powai |
| Sudden outage, partly fixed | GW-131 Ghatkopar |
| Flapping / intermittent | GW-142 Vikhroli |
| Seasonal monsoon dip (Jun–Sep) | GW-108 Andheri West, GW-165 Jogeshwari |
| Recovered after a past trough | GW-151 Mulund |
| New install (18 days of history) | GW-112 Borivali |
| Isolated weak meters only | GW-119 Goregaon, GW-170 Dahisar |
| Stable | GW-101, GW-122, GW-125, GW-146, GW-156 |

Tool functions (schema `workspace.gold`):

| Function | Returns |
|---|---|
| `get_gateway_daily_trend(gw, lookback_days)` | Daily facts for one gateway over the last N days (typical 30) |
| `get_network_snapshot()` | Latest day for every gateway |
| `compare_recent_window(gw, window_days)` | Average of last N days vs the N days before (typical 14) |
| `predict_days_to_threshold(gw, threshold, lookback_days)` | Straight-line projection of days until success % crosses the threshold; 0 = already below; NULL = flat/improving |
| `get_weak_signal_meters(gw)` | Meters flagged weak on the latest day (meter problem vs gateway problem) |

## 5. How to turn it on (from zero)

1. **Workspace:** sign in to Databricks Free Edition (no credit card). Whose account the original workspace is in: Unknown – ask Chandresh. If you can't get into it, make your own; everything here can be rebuilt.
2. **Data + tools:** open SQL Editor, paste `rebuild_medallion_clean.sql`, run all. Check the verification queries at the end (GW-114 should show a decline; GW-101's projection should be NULL).
3. **Agent:** AI Playground → choose a model with *Tools enabled* → add the UC functions from §4 as tools → paste `agent_system_prompt.md` as the system prompt (**update it first, see §6**) → ask "What's the state of the AMI network right now?"
4. **Genie (optional):** follow `genie_setup_instructions.md`.
5. **Dashboard:** follow `dashboard_setup.md`.
6. **Automated detection:** follow `databricks_alert_and_job_setup.md` (alert "AMI Network Degradation Alert" on success % < 90; job tasks `refresh_medallion` → `check_degradation` → `log_alert`).
7. **Before a demo:** use the checklist at the top of `demo_script.md` (re-run SQL, run the job once, re-check Playground tools and prompt, refresh dashboard, ask a warm-up question).

Free Edition limits noted in the docs: 1 app per account; apps auto-stop after 24 h; up to 5 concurrent job tasks.

## 6. Known issues (fix these first)

1. **The prompt, demo script and Genie notes are out of sync with the final SQL.**
   - `agent_system_prompt.md`, `demo_script.md`, `databricks_app_export.md` and `session_summary.md` describe the earlier version: 4 gateways, 6 days of data, tool `compare_first_last_day(gateway_id)` and one-argument `get_gateway_daily_trend`.
   - The final SQL **drops** `compare_first_last_day` and creates `compare_recent_window(gw, window_days)`; `get_gateway_daily_trend` and `predict_days_to_threshold` now take a `lookback_days` argument.
   - The prompt's priority rule uses "total decline from first to last observed day", which over 730 days is no longer meaningful.
   - **To do:** rewrite the prompt's tool list and priority rule around `compare_recent_window` and a 14/30-day window, re-test, and update the demo script (16 gateways, 2 years).
2. **Databricks App export is broken** in Databricks' own template (`ImportError: GetSessionIdCallback` from the `mcp` package). Untested fix in the doc: pin `"mcp>=1.10.0"` in the exported app's `pyproject.toml`. The demo uses Playground instead.
3. **Dashboard may not load on some corporate networks** (a content filter blocked the Arrow result stream during setup). Workaround: other network / skip to the job and chat.
4. **The 90% threshold and −85 dBm weak-signal cut-off** are demo choices, not values from AEML.
5. The "billing-risk window" is a straight-line projection, not a failure-prediction model. The docs say so; keep saying so.

## 7. Next improvements

From the docs:
- Compare Genie's live advisories against the Playground agent's for quality.
- Try the newer "Genie Agents" tier if an action-taking agent is needed.
- A real failure-prediction model (RFP §2.2.4.1.6) if "before billing or outage impact" must be more than a projection — separate, larger scope.
- Document/RAG memory (e.g. vector search over the RFP) — separate build.

For production (from `demo_script.md`): real HES/NMS ingestion, a streaming pipeline, and the prediction model above.

## 8. Questions for Chandresh

- Whose Databricks account holds the workspace, and does the Playground agent / Genie space / dashboard / job still exist there?
- Was the DivyaNetra demo delivered? Outcome? Is this use case still being pursued?
- What effort estimate came out of this exercise?
