# Demo script — AMI Network Health Monitoring Agent

Target use case (verbatim, from DivyaNetra RFP Appendix-1 Wave-1 #5):
> "Continuously monitors AMI network connectivity, detects degradation, and recommends
> remediation before billing or outage impact"

Run order, each numbered point maps to one phrase in that sentence.

## 0. Before you start (morning-of checklist)
- [ ] Re-run `rebuild_medallion_clean.sql` in the SQL Editor so the date window is fresh.
- [ ] Trigger the Lakeflow Job once manually so the alert has fired at least once before the demo
      (belt-and-suspenders in case live triggering hiccups in front of the audience).
- [ ] Open AI Playground, confirm the model, all 4 tools, and the current system prompt are
      still in place (Playground sessions can reset) — re-paste `agent_system_prompt.md` if in doubt.
- [ ] Refresh the dashboard.
- [ ] Ask the agent one warm-up question yourself so the first response isn't a cold start.

## 1. The picture (30 sec) — "continuously monitors"
Open the dashboard. Point at the trend line chart: four gateways, three flat, one (GW-114,
Andheri East) clearly falling. This is the network health picture, built from raw HES/NMS-style
data flowing through a medallion pipeline (bronze → silver → gold).

## 2. The automated check (1 min) — "detects degradation"
Open the Lakeflow Job. Show the two-task graph (refresh → alert check). Click **Run now**. Walk
through it live: task 1 refreshes the gold table, task 2 evaluates the SQL Alert and fires
because GW-114 is below the 90% threshold. Make the point explicitly: **this detection doesn't
require anyone to ask a question** — it's a standing, scheduled check on the platform itself.

## 3. The reasoning (2-3 min) — "recommends remediation before billing or outage impact"
Open **AI Playground** with the agent already configured (the Databricks App export hit a
template dependency bug and was dropped for this demo — the agent itself is fully validated,
just presented via Playground instead of a standalone app). Ask something like "what's the
state of the AMI network right now, and what needs attention?" Let the agent:
- pull the snapshot and drill into GW-114's trend (tool calls, not fabricated numbers — point
  this out, maybe show the MLflow trace if you set one up)
- state the trigger/evidence with real numbers
- explain what's likely happening operationally
- classify priority (should land High for GW-114)
- state confidence and why
- call out the projected days-to-threshold ("~N days until this crosses the 90% billing-risk
  line, based on the observed trend — a projection, not a guarantee")
- recommend an action for a human to approve (HOTL — never claims to execute it)

Optionally also ask about a healthy gateway (e.g. GW-122) to show the agent is honest when
nothing's wrong, not just manufacturing problems.

## 4. Ground it in the RFP (30 sec)
One sentence: this maps directly to the RFP's own architecture split — data foundation (§2.2)
vs. Agentic AI Core reasoning (§2.2.6-§2.2.8) — and operates in Human-on-the-Loop mode throughout:
the agent recommends and prioritizes, a human approves any field dispatch, billing change, or
customer communication.

## 5. Scope honesty (closing, 30 sec)
This is a prototype: 4 gateways, 6 days of synthetic (deterministic, not random) data, built in
Databricks Free Edition. What it proves is the *pattern* — continuous automated detection plus
live agentic reasoning over governed facts. Production would need real HES/NMS ingestion, a
genuinely streaming pipeline, and — if "before billing or outage impact" needs to be a guarantee
rather than a projection — a trained failure-prediction model (RFP §2.2.4.1.6), which is a
separate, larger scope item not attempted here.

## If something breaks live
- Playground rate-limited: switch to a different tools-enabled model in the dropdown — separate
  quota buckets often unblock immediately. Have a second model already tested as backup.
- Alert task fails/unavailable: run the alert's SELECT directly in the SQL Editor and narrate
  the result instead of the automated trigger.
- Dashboard not loading (e.g. a network content-filter blocking the Arrow-format result
  stream, as seen during setup): switch network (e.g. phone hotspot) if available, or skip
  straight to the job run, then the chat — the numbers the agent cites make the same point
  without the chart.
