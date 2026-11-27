# Visual companion — AI/BI Dashboard

A native Databricks dashboard, quick to build, low risk, and gives the audience a visual
before the chat app does the talking. Databricks SQL > Dashboards > Create dashboard.

## Widget 0 — Recent alerts (top section, table) + link to the chat app
Put this at the very top of the dashboard, above the KPI charts.

**Query:**
```sql
SELECT checked_at, gateway_id, area, read_date, network_success_pct
FROM workspace.gold.degradation_alert_log
ORDER BY checked_at DESC
LIMIT 5
```
Display as a table. This is populated by the Lakeflow Job's `log_alert` task (see
`databricks_alert_and_job_setup.md`) — empty until the job has run at least once.

Next to it, add a **Text** widget (markdown) with a link to **AI Playground** (the Databricks
App export hit a template bug and was dropped for this demo — see `databricks_app_export.md`):
```markdown
### Ask the agent
[Open the AMI Network Health Agent in Playground →](<your-workspace-url>/ml/playground)
```
This is the "click through to the chat interface" piece — a plain link, not a context-aware
deep link. Make sure the Playground session it opens to already has the agent configured
(tools + system prompt) so whoever clicks it doesn't land on a blank Playground.

## Widget 1 — Network trend (line chart)
**Query:**
```sql
SELECT read_date, gateway_id, area, network_success_pct
FROM workspace.gold.gateway_daily_network_health
ORDER BY gateway_id, read_date
```
Chart: line, X = `read_date`, Y = `network_success_pct`, series/color = `gateway_id`. This is
the single most important visual — GW-114 (Andheri East) should visibly peel away from the
other three flat lines.

## Widget 2 — Current network snapshot (table)
**Query:**
```sql
SELECT gateway_id, area, network_success_pct, avg_rssi_dbm, meters_with_weak_signal
FROM workspace.gold.gateway_daily_network_health
WHERE read_date = (SELECT MAX(read_date) FROM workspace.gold.gateway_daily_network_health)
ORDER BY network_success_pct
```
Display as a table, sorted worst-first so the degrading gateway is at the top.

## Widget 3 — Weak-signal meters by gateway (bar chart)
**Query:**
```sql
SELECT gateway_id, meters_with_weak_signal
FROM workspace.gold.gateway_daily_network_health
WHERE read_date = (SELECT MAX(read_date) FROM workspace.gold.gateway_daily_network_health)
ORDER BY meters_with_weak_signal DESC
```
Chart: bar, X = `gateway_id`, Y = `meters_with_weak_signal`.

## Notes
- All three widgets read from the single gold table — no joins needed, keeps this fast to build.
- Since the data window is anchored to `current_date()` (see `rebuild_medallion_clean.sql`),
  re-running the refresh job before the demo will make these widgets reflect "today" without
  any dashboard changes.
- Set the dashboard to auto-refresh (e.g. every 15 min) or just hit refresh manually right
  before presenting.
