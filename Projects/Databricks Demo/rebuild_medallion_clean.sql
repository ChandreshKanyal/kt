-- =====================================================================
-- PART 0: CLEAN SLATE — drop everything from earlier iterations
-- =====================================================================
DROP TABLE IF EXISTS workspace.bronze.nms_topology;
DROP TABLE IF EXISTS workspace.bronze.hes_comm_events;
DROP TABLE IF EXISTS workspace.bronze.hes_meter_reads;
DROP TABLE IF EXISTS workspace.bronze.meter_topology;
DROP TABLE IF EXISTS workspace.bronze.gw_profile;
DROP TABLE IF EXISTS workspace.bronze.gw_day_rate;

DROP TABLE IF EXISTS workspace.silver.gateway_daily_health;
DROP TABLE IF EXISTS workspace.silver.meter_daily_comm_health;

DROP TABLE IF EXISTS workspace.gold.agent_advisories;
DROP TABLE IF EXISTS workspace.gold.gateway_daily_network_health;
DROP TABLE IF EXISTS workspace.gold.decision_log;

DROP FUNCTION IF EXISTS workspace.gold.get_gateway_trend;
DROP FUNCTION IF EXISTS workspace.gold.list_degrading_gateways;
DROP FUNCTION IF EXISTS workspace.gold.get_latest_advisories;
DROP FUNCTION IF EXISTS workspace.gold.get_gateway_daily_trend;
DROP FUNCTION IF EXISTS workspace.gold.get_network_snapshot;
DROP FUNCTION IF EXISTS workspace.gold.compare_first_last_day;
DROP FUNCTION IF EXISTS workspace.gold.compare_recent_window;
DROP FUNCTION IF EXISTS workspace.gold.get_decision_history;
DROP FUNCTION IF EXISTS workspace.gold.predict_days_to_threshold;
DROP FUNCTION IF EXISTS workspace.gold.get_weak_signal_meters;

-- =====================================================================
-- PART 1: Schemas
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS workspace.bronze;
CREATE SCHEMA IF NOT EXISTS workspace.silver;
CREATE SCHEMA IF NOT EXISTS workspace.gold;

-- =====================================================================
-- TABLE 1 (bronze): network topology — raw, as NMS would report it.
-- 16 gateways across 3 zones, 8 meters each = 128 meters total.
-- install_date anchored to current_date() so it stays "current" over time.
-- =====================================================================
CREATE TABLE workspace.bronze.nms_topology AS
WITH gateways AS (
  SELECT * FROM VALUES
    ('GW-101', 'Malad West',   'Western Suburbs'),
    ('GW-108', 'Andheri West', 'Western Suburbs'),
    ('GW-112', 'Borivali',     'Western Suburbs'),
    ('GW-114', 'Andheri East', 'Western Suburbs'),
    ('GW-119', 'Goregaon',     'Western Suburbs'),
    ('GW-125', 'Kandivali',    'Western Suburbs'),
    ('GW-122', 'Bandra Kurla', 'Central Suburbs'),
    ('GW-137', 'Powai',        'Central Suburbs'),
    ('GW-161', 'Kurla',        'Central Suburbs'),
    ('GW-165', 'Jogeshwari',   'Central Suburbs'),
    ('GW-170', 'Dahisar',      'Central Suburbs'),
    ('GW-131', 'Ghatkopar',    'Eastern Suburbs'),
    ('GW-142', 'Vikhroli',     'Eastern Suburbs'),
    ('GW-146', 'Bhandup',      'Eastern Suburbs'),
    ('GW-151', 'Mulund',       'Eastern Suburbs'),
    ('GW-156', 'Chembur',      'Eastern Suburbs')
  AS t(gateway_id, area, zone)
)
SELECT
  gateway_id,
  area,
  zone,
  concat(gateway_id, '-MTR-', lpad(cast(idx AS STRING), 3, '0')) AS meter_id,
  CASE (abs(hash(concat(gateway_id, cast(idx AS STRING)))) % 3)
    WHEN 0 THEN 'AMI-STD-1P'
    WHEN 1 THEN 'AMI-STD-3P'
    ELSE 'AMI-CT-3P'
  END AS meter_type,
  date_add(date_sub(current_date(), 1095), abs(hash(concat(gateway_id, cast(idx AS STRING)))) % 1095) AS install_date
FROM gateways
LATERAL VIEW explode(sequence(0, 7)) e AS idx;

-- =====================================================================
-- TABLE 2 (bronze): raw HES-style daily read logs per meter, 730 days
-- (2 years, ending "today" — the window is anchored to current_date()
-- so every rebuild/job run looks current, not frozen to one date).
--
-- Each gateway is assigned one scenario archetype via gw_scenario below.
-- days_ago = 0 is today, days_ago = 729 is the oldest day. Formulas are
-- deterministic (hash-based noise, sin() for flapping) — reproducible
-- every run, not truly random.
--
-- Scenario types:
--   trend   — flat baseline, then a linear ramp starting `pivot_days_ago`
--             days ago at `rate_per_day` (covers stable/gradual/mild
--             decline/slow-improving, depending on the parameters)
--   step    — flat baseline, then a step drop `pivot_days_ago` days ago,
--             plateauing at base - step_drop_pct + step_recovery_pct
--             (sudden hardware/link failure, partially fixed)
--   flap    — oscillates via sin(), no net trend (intermittent/noisy)
--   monsoon — flat baseline minus a fixed penalty during Jun-Sep each
--             year (recurring seasonal RF interference)
--   vshape  — declining toward a trough at `pivot_days_ago`, then
--             recovering afterward (past issue, since resolved)
--
-- install_offset_days truncates history length (new-install gateways).
-- meter_override flags specific meters as chronically weak regardless
-- of the gateway-level scenario (isolated meter-level issue).
-- =====================================================================
CREATE TABLE workspace.bronze.hes_meter_reads AS
WITH gw_scenario AS (
  SELECT * FROM VALUES
    -- gateway_id, scenario_type, base_pct, pivot_days_ago, rate_per_day, secondary_rate,
    -- step_drop_pct, step_recovery_pct, flap_amplitude, monsoon_amplitude, install_offset_days
    ('GW-101', 'trend',   98.5,   0,  0.00, 0.00,  0.0, 0.0, 0.0, 0.0, 9999),  -- stable
    ('GW-108', 'monsoon', 97.0,   0,  0.00, 0.00,  0.0, 0.0, 0.0, 6.5, 9999),  -- seasonal monsoon
    ('GW-112', 'trend',   98.0,   0,  0.00, 0.00,  0.0, 0.0, 0.0, 0.0, 18),    -- new install (18 days)
    ('GW-114', 'trend',   98.0,  20, -0.90, 0.00,  0.0, 0.0, 0.0, 0.0, 9999),  -- gradual decline (hero)
    ('GW-119', 'trend',   99.0,   0,  0.00, 0.00,  0.0, 0.0, 0.0, 0.0, 9999),  -- isolated meter issue
    ('GW-125', 'trend',   98.8,   0,  0.00, 0.00,  0.0, 0.0, 0.0, 0.0, 9999),  -- stable
    ('GW-122', 'trend',   99.2,   0,  0.00, 0.00,  0.0, 0.0, 0.0, 0.0, 9999),  -- stable, high performing
    ('GW-137', 'trend',   97.5,  35, -0.32, 0.00,  0.0, 0.0, 0.0, 0.0, 9999),  -- mild decline
    ('GW-161', 'trend',   97.6,  15, -1.10, 0.00,  0.0, 0.0, 0.0, 0.0, 9999),  -- gradual decline #2
    ('GW-165', 'monsoon', 96.8,   0,  0.00, 0.00,  0.0, 0.0, 0.0, 7.0, 9999),  -- seasonal monsoon #2
    ('GW-170', 'trend',   98.6,   0,  0.00, 0.00,  0.0, 0.0, 0.0, 0.0, 9999),  -- isolated meter issue #2
    ('GW-131', 'step',    98.0,  10,  0.00, 0.00, 22.0, 6.0, 0.0, 0.0, 9999),  -- sudden outage
    ('GW-142', 'flap',    94.0,   0,  0.00, 0.00,  0.0, 0.0, 6.0, 0.0, 9999),  -- flapping/intermittent
    ('GW-146', 'trend',   98.3,   0,  0.00, 0.00,  0.0, 0.0, 0.0, 0.0, 9999),  -- stable
    ('GW-151', 'vshape',  78.0,  90,  0.28, 0.15,  0.0, 0.0, 0.0, 0.0, 9999),  -- improving / recovered
    ('GW-156', 'trend',   98.9,   0,  0.00, 0.00,  0.0, 0.0, 0.0, 0.0, 9999)   -- stable
  AS t(gateway_id, scenario_type, base_pct, pivot_days_ago, rate_per_day, secondary_rate,
       step_drop_pct, step_recovery_pct, flap_amplitude, monsoon_amplitude, install_offset_days)
),
meter_override AS (
  SELECT * FROM VALUES
    ('GW-119', 0), ('GW-119', 1),
    ('GW-170', 0), ('GW-170', 1)
  AS t(gateway_id, meter_idx)
),
days AS (SELECT explode(sequence(1, 730)) AS day_number),
base AS (
  SELECT
    m.meter_id,
    m.gateway_id,
    d.day_number,
    date_add(date_sub(current_date(), 730), d.day_number) AS read_date,
    (730 - d.day_number) AS days_ago,
    ((abs(hash(concat(m.meter_id, cast(d.day_number AS STRING)))) % 201) - 100) / 100.0 AS noise_pts,
    s.scenario_type, s.base_pct, s.pivot_days_ago, s.rate_per_day, s.secondary_rate,
    s.step_drop_pct, s.step_recovery_pct, s.flap_amplitude, s.monsoon_amplitude, s.install_offset_days,
    CASE WHEN mo.meter_idx IS NOT NULL THEN true ELSE false END AS is_override_meter
  FROM workspace.bronze.nms_topology m
  JOIN gw_scenario s ON m.gateway_id = s.gateway_id
  CROSS JOIN days d
  LEFT JOIN meter_override mo
    ON mo.gateway_id = m.gateway_id
   AND mo.meter_idx = CAST(element_at(split(m.meter_id, '-'), -1) AS INT)
  WHERE (730 - d.day_number) <= s.install_offset_days
),
rated_base AS (
  SELECT *,
    CASE scenario_type
      WHEN 'trend' THEN
        CASE WHEN days_ago > pivot_days_ago THEN base_pct
             ELSE base_pct + rate_per_day * (pivot_days_ago - days_ago) END
      WHEN 'step' THEN
        CASE WHEN days_ago > pivot_days_ago THEN base_pct
             ELSE base_pct - step_drop_pct + step_recovery_pct END
      WHEN 'flap' THEN
        base_pct + flap_amplitude * SIN(day_number * 0.9)
      WHEN 'monsoon' THEN
        base_pct - monsoon_amplitude * (CASE WHEN MONTH(read_date) IN (6, 7, 8, 9) THEN 1.0 ELSE 0.0 END)
      WHEN 'vshape' THEN
        CASE WHEN days_ago >= pivot_days_ago
               THEN base_pct + secondary_rate * (days_ago - pivot_days_ago)
             ELSE base_pct + rate_per_day * (pivot_days_ago - days_ago) END
    END AS scenario_pct
  FROM base
),
overridden AS (
  SELECT *,
    CASE WHEN is_override_meter THEN scenario_pct * 0.75 ELSE scenario_pct END AS pre_noise_pct
  FROM rated_base
),
rated AS (
  SELECT
    meter_id, gateway_id, read_date, is_override_meter,
    GREATEST(50.0, LEAST(99.9, pre_noise_pct + noise_pts)) AS success_pct
  FROM overridden
)
SELECT
  meter_id,
  gateway_id,
  read_date,
  24 AS scheduled_reads,
  CAST(ROUND(24 * success_pct / 100.0) AS INT) AS successful_reads,
  24 - CAST(ROUND(24 * success_pct / 100.0) AS INT) AS failed_reads,
  ROUND(
    -60 - ((100 - success_pct) * 1.8)
    + (CASE WHEN is_override_meter THEN -20 ELSE 0 END)
    + (((abs(hash(concat(meter_id, 'rssi', cast(read_date AS STRING)))) % 11) - 5))
  , 1) AS avg_rssi_dbm
FROM rated;

-- =====================================================================
-- TABLE 3 (silver): conformed meter-level daily health.
-- Joins bronze reads to topology, standardizes fields, adds a plain
-- data-quality flag. Still just facts — no verdicts.
-- Weak-signal threshold tightened to -85 dBm (previous -95 threshold
-- never actually triggered for any observed data).
-- =====================================================================
CREATE TABLE workspace.silver.meter_daily_comm_health AS
SELECT
  r.meter_id,
  r.gateway_id,
  t.area,
  t.zone,
  t.meter_type,
  r.read_date,
  r.scheduled_reads,
  r.successful_reads,
  r.failed_reads,
  ROUND(r.successful_reads / r.scheduled_reads * 100, 1) AS success_pct,
  r.avg_rssi_dbm,
  CASE WHEN r.avg_rssi_dbm < -85 THEN 'weak' ELSE 'ok' END AS signal_quality_flag
FROM workspace.bronze.hes_meter_reads r
JOIN workspace.bronze.nms_topology t ON r.meter_id = t.meter_id;

-- =====================================================================
-- TABLE 4 (gold): analytical, consolidated gateway-day facts.
-- One row per gateway per day. Zero interpretation columns —
-- no priority, no confidence, no explanation, no recommended action.
-- =====================================================================
CREATE TABLE workspace.gold.gateway_daily_network_health AS
SELECT
  gateway_id,
  area,
  zone,
  read_date,
  COUNT(DISTINCT meter_id) AS meter_count,
  SUM(scheduled_reads) AS total_scheduled_reads,
  SUM(successful_reads) AS total_successful_reads,
  SUM(failed_reads) AS total_failed_reads,
  ROUND(SUM(successful_reads) / SUM(scheduled_reads) * 100, 1) AS network_success_pct,
  ROUND(AVG(avg_rssi_dbm), 1) AS avg_rssi_dbm,
  SUM(CASE WHEN signal_quality_flag = 'weak' THEN 1 ELSE 0 END) AS meters_with_weak_signal
FROM workspace.silver.meter_daily_comm_health
GROUP BY gateway_id, area, zone, read_date;

-- =====================================================================
-- TABLE 5 (gold): degradation alert log. Append-only record of every time
-- the automated SQL Alert check found a gateway below threshold — this is
-- what the "recent alerts" section of the dashboard reads from. The job's
-- log_alert task (see databricks_alert_and_job_setup.md) INSERTs into this
-- on every run; it is NOT repopulated by this rebuild script.
-- =====================================================================
CREATE TABLE IF NOT EXISTS workspace.gold.degradation_alert_log (
  checked_at TIMESTAMP,
  gateway_id STRING,
  area STRING,
  read_date DATE,
  network_success_pct DOUBLE
);

-- =====================================================================
-- PART 2: Agent tools — pure data retrieval, zero built-in judgment.
-- =====================================================================
CREATE OR REPLACE FUNCTION workspace.gold.get_gateway_daily_trend(gw STRING, lookback_days INT)
RETURNS TABLE (gateway_id STRING, area STRING, zone STRING, read_date DATE, meter_count BIGINT,
               total_scheduled_reads BIGINT, total_successful_reads BIGINT,
               network_success_pct DOUBLE, avg_rssi_dbm DOUBLE, meters_with_weak_signal BIGINT)
COMMENT 'Returns daily network health facts for one gateway over the trailing lookback_days (typical value: 30), ordered by date, most recent last. No interpretation included.'
RETURN
  SELECT gateway_id, area, zone, read_date, meter_count, total_scheduled_reads,
         total_successful_reads, network_success_pct, avg_rssi_dbm, meters_with_weak_signal
  FROM workspace.gold.gateway_daily_network_health
  WHERE gateway_id = gw
    AND read_date > date_sub(current_date(), lookback_days)
  ORDER BY read_date;

CREATE OR REPLACE FUNCTION workspace.gold.get_network_snapshot()
RETURNS TABLE (gateway_id STRING, area STRING, zone STRING, read_date DATE,
               network_success_pct DOUBLE, avg_rssi_dbm DOUBLE, meters_with_weak_signal BIGINT)
COMMENT 'Returns the most recent day of data for every gateway — a current-state snapshot, facts only.'
RETURN
  SELECT gateway_id, area, zone, read_date, network_success_pct, avg_rssi_dbm, meters_with_weak_signal
  FROM workspace.gold.gateway_daily_network_health g
  WHERE read_date = (SELECT MAX(read_date) FROM workspace.gold.gateway_daily_network_health);

CREATE OR REPLACE FUNCTION workspace.gold.compare_recent_window(gw STRING, window_days INT)
RETURNS TABLE (gateway_id STRING, area STRING, zone STRING,
               recent_avg_pct DOUBLE, prior_avg_pct DOUBLE, pct_point_change DOUBLE,
               recent_days_count BIGINT, prior_days_count BIGINT)
COMMENT 'Compares average network_success_pct over the most recent window_days (typical value: 14) against the equal-length period immediately before it. Positive pct_point_change = improving, negative = declining. Low recent_days_count or NULL prior_avg_pct means limited history (e.g. a newly installed gateway) — lower confidence in that case.'
RETURN
  WITH recent AS (
    SELECT gateway_id, area, zone, AVG(network_success_pct) AS avg_pct, COUNT(*) AS n
    FROM workspace.gold.gateway_daily_network_health
    WHERE gateway_id = gw AND read_date > date_sub(current_date(), window_days)
    GROUP BY gateway_id, area, zone
  ),
  prior AS (
    SELECT gateway_id, AVG(network_success_pct) AS avg_pct, COUNT(*) AS n
    FROM workspace.gold.gateway_daily_network_health
    WHERE gateway_id = gw
      AND read_date <= date_sub(current_date(), window_days)
      AND read_date > date_sub(current_date(), 2 * window_days)
    GROUP BY gateway_id
  )
  SELECT r.gateway_id, r.area, r.zone,
         ROUND(r.avg_pct, 1) AS recent_avg_pct, ROUND(p.avg_pct, 1) AS prior_avg_pct,
         ROUND(r.avg_pct - p.avg_pct, 1) AS pct_point_change,
         r.n AS recent_days_count, p.n AS prior_days_count
  FROM recent r
  LEFT JOIN prior p ON r.gateway_id = p.gateway_id;

CREATE OR REPLACE FUNCTION workspace.gold.predict_days_to_threshold(gw STRING, threshold DOUBLE, lookback_days INT)
RETURNS TABLE (gateway_id STRING, area STRING, zone STRING, current_pct DOUBLE,
               daily_slope_pct DOUBLE, projected_days_to_threshold DOUBLE)
COMMENT 'Linear-regression projection of days until network_success_pct crosses a threshold, based on the trailing lookback_days (typical value: 14) of observed daily trend. A heuristic extrapolation over a recent window, not a trained failure-prediction model. Returns 0 if already at/below threshold, NULL if the recent trend is flat or improving.'
RETURN
  WITH h AS (
    SELECT gateway_id, area, zone, read_date, network_success_pct,
           ROW_NUMBER() OVER (PARTITION BY gateway_id ORDER BY read_date) AS day_idx
    FROM workspace.gold.gateway_daily_network_health
    WHERE gateway_id = gw AND read_date > date_sub(current_date(), lookback_days)
  ),
  slope AS (
    SELECT gateway_id, area, zone,
           COVAR_POP(day_idx, network_success_pct) / NULLIF(VAR_POP(day_idx), 0) AS daily_slope_pct,
           MAX(CASE WHEN day_idx = (SELECT MAX(day_idx) FROM h) THEN network_success_pct END) AS current_pct
    FROM h
    GROUP BY gateway_id, area, zone
  )
  SELECT gateway_id, area, zone, current_pct, ROUND(daily_slope_pct, 3) AS daily_slope_pct,
         CASE
           WHEN current_pct <= threshold THEN 0
           WHEN daily_slope_pct < 0 THEN ROUND((current_pct - threshold) / (-daily_slope_pct), 1)
           ELSE NULL
         END AS projected_days_to_threshold
  FROM slope;

CREATE OR REPLACE FUNCTION workspace.gold.get_weak_signal_meters(gw STRING)
RETURNS TABLE (meter_id STRING, gateway_id STRING, area STRING, meter_type STRING,
               read_date DATE, success_pct DOUBLE, avg_rssi_dbm DOUBLE)
COMMENT 'Returns meters currently flagged weak-signal for a gateway, on the most recent day of data. Use this to distinguish an isolated meter-level problem from a gateway-wide issue.'
RETURN
  SELECT meter_id, gateway_id, area, meter_type, read_date, success_pct, avg_rssi_dbm
  FROM workspace.silver.meter_daily_comm_health
  WHERE gateway_id = gw
    AND signal_quality_flag = 'weak'
    AND read_date = (SELECT MAX(read_date) FROM workspace.silver.meter_daily_comm_health WHERE gateway_id = gw)
  ORDER BY avg_rssi_dbm;

-- =====================================================================
-- PART 3: Verification — confirm the clean rebuild
-- =====================================================================
SHOW TABLES IN workspace.bronze;
SHOW TABLES IN workspace.silver;
SHOW TABLES IN workspace.gold;

SELECT * FROM workspace.bronze.nms_topology LIMIT 5;
SELECT * FROM workspace.bronze.hes_meter_reads LIMIT 5;
SELECT * FROM workspace.silver.meter_daily_comm_health LIMIT 5;

-- Latest snapshot across all 16 gateways — should show a mix of high and
-- low network_success_pct depending on scenario.
SELECT * FROM workspace.gold.gateway_daily_network_health
WHERE read_date = (SELECT MAX(read_date) FROM workspace.gold.gateway_daily_network_health)
ORDER BY network_success_pct;

-- One scenario check per archetype (recent trend, 14-day window):
SELECT * FROM workspace.gold.get_gateway_daily_trend('GW-114', 14) ORDER BY read_date; -- gradual decline
SELECT * FROM workspace.gold.get_gateway_daily_trend('GW-131', 14) ORDER BY read_date; -- sudden outage
SELECT * FROM workspace.gold.get_gateway_daily_trend('GW-151', 14) ORDER BY read_date; -- recovered

-- Projection sanity checks: GW-114/GW-161 should be positive or 0,
-- GW-101 (stable) should be NULL, GW-112 (new install) should still work
-- despite only 18 days of history.
SELECT * FROM workspace.gold.predict_days_to_threshold('GW-114', 90.0, 14);
SELECT * FROM workspace.gold.predict_days_to_threshold('GW-101', 90.0, 14);
SELECT * FROM workspace.gold.predict_days_to_threshold('GW-112', 90.0, 14);

-- Recent-window comparison: GW-151 should show recent improving even
-- though its full history includes a trough.
SELECT * FROM workspace.gold.compare_recent_window('GW-151', 14);

-- Should now return rows (previous -95 threshold never triggered):
SELECT * FROM workspace.gold.get_weak_signal_meters('GW-119');
SELECT * FROM workspace.gold.get_weak_signal_meters('GW-170');
