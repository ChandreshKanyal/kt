# Genie Space setup — AMI Network Health

## Step 1: Which tables to add to the Genie Space
Add these three (Genie > New Space > select tables):
- `workspace.gold.gateway_daily_network_health` — primary table, one row per gateway per day
- `workspace.silver.meter_daily_comm_health` — meter-level detail, for drill-down questions
- `workspace.bronze.nms_topology` — meter type / install date, for context questions

You don't need to add the bronze read-log table or the three SQL functions — Genie writes
its own SQL against the tables directly.

## Step 2: Paste this into "Instructions" (General Instructions box)

---

This space answers questions about AMI (Advanced Metering Infrastructure) network health for
AEML's Smart Metering network. The core table, gateway_daily_network_health, has one row per
gateway per day with these facts: network_success_pct (% of scheduled meter reads that
succeeded), avg_rssi_dbm (average signal strength, more negative = weaker), and
meters_with_weak_signal (count of meters below signal threshold). There is no pre-computed
priority, confidence, or recommendation anywhere in this data — you generate that judgment
yourself from the numbers.

When asked about a specific gateway's health, pull its full daily history (ordered by
read_date) and:
1. State the trend in plain numbers: starting % vs. latest %, and the point change.
2. Classify severity yourself, checking both conditions (either one alone sets High) using the
   TOTAL decline from first to last observed day, not the average daily change: latest
   network_success_pct below 90%, OR total decline of 15+ points = high priority; neither of
   those but total decline of 5-15 points = medium; total decline under 5 points = low; flat or
   improving = none.
3. State your confidence and why (e.g. "high confidence — the decline is consistent across
   all 6 days" vs. "low confidence — limited data, could be noise").
4. End with a recommendation phrased for a human reviewer to act on (e.g. "recommend a
   diagnostic visit"), never as if you are taking the action yourself.

When asked to compare gateways or find the worst-performing one, query all gateways for the
latest date, and where relevant, look at each one's trend over the full period, not just the
latest snapshot.

When a gateway is declining, also project how many days remain until network_success_pct
crosses 90% (the billing-risk threshold), using a linear-regression slope over the observed
days (see the worked example below). State it as a projection based on the observed trend,
never as a guarantee, and omit it entirely for flat or improving gateways.

Be honest when a gateway is healthy — do not manufacture a problem. If nothing in the data
is concerning, say so plainly.

Keep answers concise and operational — this is read by network operations staff, not a
general audience.

---

## Step 3: Add these as example questions (Genie > Example SQL queries)
Genie learns your intent faster with a few worked examples. Add each question below, run the
SQL Genie proposes, and if it's correct, save it as a "trusted" example.

**Q: "Which gateway has the biggest decline over the observed period?"**
```sql
WITH ordered AS (
  SELECT gateway_id, area, read_date, network_success_pct,
         ROW_NUMBER() OVER (PARTITION BY gateway_id ORDER BY read_date) AS rn_asc,
         ROW_NUMBER() OVER (PARTITION BY gateway_id ORDER BY read_date DESC) AS rn_desc
  FROM workspace.gold.gateway_daily_network_health
)
SELECT f.gateway_id, f.area, f.network_success_pct AS start_pct, l.network_success_pct AS latest_pct,
       ROUND(f.network_success_pct - l.network_success_pct, 1) AS decline_pct_points
FROM (SELECT * FROM ordered WHERE rn_asc = 1) f
JOIN (SELECT * FROM ordered WHERE rn_desc = 1) l ON f.gateway_id = l.gateway_id
ORDER BY decline_pct_points DESC;
```

**Q: "Show me the daily trend for GW-114"**
```sql
SELECT read_date, network_success_pct, avg_rssi_dbm, meters_with_weak_signal
FROM workspace.gold.gateway_daily_network_health
WHERE gateway_id = 'GW-114'
ORDER BY read_date;
```

**Q: "What's the current state of the whole network?"**
```sql
SELECT gateway_id, area, network_success_pct, avg_rssi_dbm, meters_with_weak_signal
FROM workspace.gold.gateway_daily_network_health
WHERE read_date = (SELECT MAX(read_date) FROM workspace.gold.gateway_daily_network_health);
```

**Q: "How many days until GW-114 crosses the 90% billing-risk threshold?"**
```sql
WITH h AS (
  SELECT gateway_id, area, read_date, network_success_pct,
         ROW_NUMBER() OVER (PARTITION BY gateway_id ORDER BY read_date) AS day_idx
  FROM workspace.gold.gateway_daily_network_health
  WHERE gateway_id = 'GW-114'
),
slope AS (
  SELECT gateway_id, area,
         COVAR_POP(day_idx, network_success_pct) / NULLIF(VAR_POP(day_idx), 0) AS daily_slope_pct,
         MAX(CASE WHEN day_idx = (SELECT MAX(day_idx) FROM h) THEN network_success_pct END) AS current_pct
  FROM h
  GROUP BY gateway_id, area
)
SELECT gateway_id, area, current_pct, ROUND(daily_slope_pct, 3) AS daily_slope_pct,
       CASE
         WHEN current_pct <= 90.0 THEN 0
         WHEN daily_slope_pct < 0 THEN ROUND((current_pct - 90.0) / (-daily_slope_pct), 1)
         ELSE NULL
       END AS projected_days_to_threshold
FROM slope;
```
A result of `0` means the gateway is already at or below threshold — phrase it as "already
below threshold," not "0 days until."

## Notes
- Genie won't automatically apply the priority/confidence classification in its SQL — that
  judgment happens in Genie's natural-language response after the query runs, driven by the
  Instructions text above. If its written answers skip the classification, ask it explicitly:
  "classify the severity and your confidence" in the chat, or tighten the instructions text.
- If Genie's answers feel too terse, add a line to Instructions like "always include a one-line
  recommendation, even for healthy gateways" — Genie responds well to explicit formatting asks.
