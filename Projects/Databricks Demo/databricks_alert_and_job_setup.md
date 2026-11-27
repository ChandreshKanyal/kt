# Automated detection layer — SQL Alert + Lakeflow Job

This is the piece that makes the agent's story "continuously monitors ... detects
degradation" true independent of anyone chatting with it. It's a deterministic,
non-LLM trigger sitting alongside the reasoning layer — the platform itself is
watching.

## Step 1: Create the SQL Alert

Databricks SQL > Alerts > Create alert.

**Query:**
```sql
SELECT gateway_id, area, read_date, network_success_pct
FROM workspace.gold.gateway_daily_network_health
WHERE read_date = (SELECT MAX(read_date) FROM workspace.gold.gateway_daily_network_health)
  AND network_success_pct < 90
```

**Condition:** trigger when the query returns more than 0 rows (row count > 0).

**Name:** `AMI Network Degradation Alert`

**Schedule:** you can leave this unscheduled and drive it from the job instead (Step 2), or
set an independent schedule (e.g. every 15 min) if you want the alert to also fire on its own.

**Notifications:** add yourself as a subscriber so you see it trigger. Optional for the demo,
but a good visual if you want the alert email/notification on screen too. To also push to
Slack/Teams, see Step 1a below before you finish creating the alert.

## Step 1a (optional): Slack / Teams / Email notification destinations

Requires **workspace admin** access.

1. Click your username (top right) > **Settings** > **Workspace admin** tab > **Notifications** >
   **Manage** > **+ Add destination**.
2. For **Slack**: create a Slack app with an *Incoming Webhook* enabled in the target channel
   (slack.com/apps > "Incoming Webhooks"), copy the generated webhook URL, paste it in here.
3. For **Microsoft Teams**: in the target Teams channel, add an *Incoming Webhook* connector,
   copy its URL, paste it in here.
4. For **Email**: no external setup — just list the recipient addresses.
5. Save. Repeat for each destination you want.
6. Back on the `AMI Network Degradation Alert` alert (Step 1), open **Notifications** and add
   each destination you just created, alongside/instead of yourself as a subscriber.

The message that lands in Slack/Teams/email will contain the alert's raw trigger (which
gateway, current %, threshold) — it does not include the LLM's full priority/confidence/
recommendation writeup, since that's only generated when someone opens the chat app. Frame this
in the demo as "the platform detects and pages automatically; the agent explains and
recommends when you ask."

## Step 2: Create the Lakeflow Job

Jobs & Pipelines > Create > Job. Two tasks:

**Task 1 — `refresh_medallion`** (SQL task)
- Type: SQL, against a SQL warehouse (serverless is fine on Free Edition)
- Runs the table-refresh portion of `rebuild_medallion_clean.sql` (Parts 1 onward — you can
  skip the DROP statements in Part 0 once the tables exist, or leave them in since `CREATE
  TABLE ... AS SELECT` in the script already fully replaces table contents each run)
- This is what makes each run look "current" — the date window in the script is anchored to
  `current_date()`, so every run reflects "today"

**Task 2 — `check_degradation`** (SQL Alert task)
- Depends on Task 1 (runs after it succeeds)
- Search for the "SQL Alert" task type, select the `AMI Network Degradation Alert` alert
  created in Step 1
- Choose the same SQL warehouse

**Task 3 — `log_alert`** (SQL task, depends on Task 2)
- This feeds the dashboard's "recent alerts" widget (see `dashboard_setup.md`). Runs
  unconditionally after the alert check (logs nothing new if nothing's below threshold):
```sql
INSERT INTO workspace.gold.degradation_alert_log
SELECT current_timestamp(), gateway_id, area, read_date, network_success_pct
FROM workspace.gold.gateway_daily_network_health
WHERE read_date = (SELECT MAX(read_date) FROM workspace.gold.gateway_daily_network_health)
  AND network_success_pct < 90;
```

**Schedule:** set to run hourly (or whatever cadence reads well) — this is the "continuous
monitoring" cadence. For the live demo itself, don't wait on the schedule: open the job and
click **Run now** to trigger the refresh → alert-check sequence on demand, in front of the
audience.

## Free Edition notes
- Free Edition allows up to 5 concurrent job tasks per account — this job only uses 2, well
  within budget.
- Jobs run on serverless compute by default on Free Edition; no cluster provisioning needed.

## Fallback if SQL Alerts aren't available
If SQL Alerts turn out to be gated/unavailable when you check the workspace tomorrow morning,
skip the alert task and just run Task 1, then run the alert's underlying SELECT directly in the
SQL Editor and read the result live. Same narrative — "the platform ran a check and found GW-114
below threshold" — just without the automated notification wrapper.
