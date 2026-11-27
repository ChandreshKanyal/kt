# Databricks AI Agent Prototype — Session Summary

## Goal
Build a free, fast prototype of an AI agent on Databricks to estimate how long agent-building
takes, for a judgment call. Used as the worked example: the "AMI Network Health Monitoring
Agent" from the DivyaNetra RFP (Adani Electricity Mumbai Ltd., Appendix-1, Wave-1, use case #5) —
answering "where is the AMI network degrading, and what do we fix before it hits billing or the
customer?"

## Platform decision
- **Databricks Free Edition** (login.databricks.com) — free, no credit card, no time limit.
  Not the 14-day trial (that needs a cloud account and is for business evaluation, not quick
  prototyping).
- Free Edition includes a serverless SQL warehouse by default — no separate provisioning needed.

## What was actually built

### 1. Medallion architecture tables (Unity Catalog, catalog = `workspace`)
Built entirely via SQL Editor (not notebooks), using **deterministic, hash-based synthetic
data** (not `rand()`) so results are reproducible every run — real-looking variance without
randomness.

| Layer | Table | Contents |
|---|---|---|
| Bronze | `workspace.bronze.nms_topology` | 4 gateways × 8 meters, meter type, install date |
| Bronze | `workspace.bronze.hes_meter_reads` | Raw daily read logs per meter: scheduled/successful/failed reads, signal strength (RSSI) |
| Silver | `workspace.silver.meter_daily_comm_health` | Joined + standardized meter-day facts, success %, weak-signal flag |
| Gold | `workspace.gold.gateway_daily_network_health` | Aggregated gateway-day facts: network success %, avg signal, weak-signal meter count |

**Key design decision:** the data layer holds **only facts — no priority, confidence,
explanation, or recommended action stored anywhere.** That reasoning is generated live by the
agent/Genie at query time from the raw numbers, not pre-baked into tables. This mirrors the
RFP's own separation between the "data foundation" (§2.2) and the "Agentic AI Core" reasoning
layer (§2.2.6).

Fixed per-gateway trend (for realism, not randomized each run):
- GW-101 Malad West — stable (+0.05 pts/day)
- GW-114 Andheri East — clearly degrading (−3.20 pts/day) ← the "story" gateway
- GW-122 Bandra Kurla — stable, high-performing (−0.10 pts/day)
- GW-137 Powai — mild decline (−1.10 pts/day)

### 2. Query tools (Unity Catalog SQL functions on `gold` schema)
- `get_gateway_daily_trend(gateway_id)` — full daily history for one gateway
- `get_network_snapshot()` — latest day, all gateways
- `compare_first_last_day(gateway_id)` — first vs. last day, raw % point change

These are pure data retrieval — no judgment baked in.

### 3. Two agent front-ends tested
- **AI Playground** — attached the 3 functions as tools, pasted a system prompt instructing it
  to generate priority/confidence/explanation/recommendation live from the raw numbers, in
  HOTL (Human-on-the-Loop) framing (never claims to execute actions itself).
- **Genie Space** — pointed at the 3 tables directly (Genie writes its own SQL rather than
  calling custom functions); used an "Instructions" text block + example Q&A pairs to get the
  same advisory-style output.

### Key product clarification learned
"Genie" and "Agent" are different things in Databricks:
- **Genie** = natural-language-to-SQL over selected tables, conversational analytics, shareable
  link. Classic/simpler tier.
- **Agent** (Playground / Agent Bricks / Mosaic AI Agent Framework) = calls custom tools,
  multi-step reasoning, deployable as a versioned/governed endpoint.
- Databricks announced (June 2026 Data+AI Summit) an expanded **"Genie Agents"** tier that adds
  autonomous action-taking, Slack/Teams/Gmail integration, and MCP support — blurring this line.
  What was built in this session is the classic, simpler Genie Space — not the new Genie Agents
  tier.

## Files produced this session
**⚠️ Since this is an Incognito conversation, download these now if you need them —**
**they won't carry over automatically.**

| File | Status | Purpose |
|---|---|---|
| `rebuild_medallion_clean.sql` | **Current / final** | Complete script: drops all prior tables/functions, rebuilds fact-only medallion tables + 3 query functions from scratch |
| `agent_system_prompt.md` | **Current** | System prompt for Playground — instructs live advisory generation with priority/confidence rules |
| `genie_setup_instructions.md` | **Current** | Genie Space setup guide — which tables to add, Instructions text, example Q&A pairs |
| `ami_network_health_agent.py` | Superseded | Original Python/PySpark notebook version — replaced by pure-SQL approach |
| `setup_agent_data_layer.sql` | Superseded | Early version, references old table names |
| `create_medallion_tables.sql` | Superseded | Randomized-per-run version — replaced by deterministic version |
| `create_medallion_tables_static.sql` | Superseded | Folded into `rebuild_medallion_clean.sql` |

## Time estimate data points gathered so far
- Free Edition signup → workspace ready: ~5 min
- SQL table/function creation (once script is written): a few minutes to run
- Playground tool attach + system prompt + testing: ~20-30 min
- Genie Space setup + instructions + testing: ~15-20 min
- **Designing** the fact-only architecture and writing the SQL (the actual thinking work): took
  several iterations in this session — worth noting as the real time sink, not the clicking

## Open items / possible next steps
- Test whether Genie's live-generated advisories (priority/confidence) match quality of
  Playground's function-calling version
- Consider the "Genie Agents" tier (autonomous, action-taking) if the judgment call needs that
  data point too — bigger lift than what's been tested
- The image's advisory format included "predicted failure in N days" and "billing cycle risk in
  N days" — flagged as **not supportable** by current fact tables; would need a real
  failure-prediction model (RFP §2.2.4.1.6), a separate and larger scope item
- Real document/RAG memory (vector search over an uploaded doc like the RFP itself) was
  discussed as a heavier, separately-timed build vs. the system-prompt approach used so far
