> **Status: deprioritized for the demo.** Export hit a crash bug in Databricks' own
> `agent-openai-agents-sdk` export template (`ImportError: cannot import name
> 'GetSessionIdCallback' from mcp.client.streamable_http` — a transitive dependency
> mismatch between `databricks-openai` and the resolved `mcp` package version,
> unrelated to our agent config). The agent itself is fully validated and correct
> (see `agent_system_prompt.md` test results). **The demo uses AI Playground directly
> instead** — see `demo_script.md`. Revisit this export only if there's spare time
> after the demo is otherwise locked down; a possible fix is adding an explicit
> `"mcp>=1.10.0"` dependency to the exported app's `pyproject.toml` and redeploying,
> untested under time pressure.

# Demo surface — export the Playground agent to a Databricks App

Playground/Genie screens work but read as dev tools. Exporting the already-tested agent to
Databricks Apps gives a real chat UI for the demo, reusing the exact tool wiring and system
prompt already validated — no new agent code to write or debug tonight.

## Prerequisites
- The agent is already configured in AI Playground: model with "Tools enabled", the 4 UC
  functions attached (`get_gateway_daily_trend`, `get_network_snapshot`, `compare_first_last_day`,
  `predict_days_to_threshold`), and the system prompt from `agent_system_prompt.md` pasted in.
- Test it in Playground first — ask it "what's the state of the network" and "what's happening
  with GW-114" and confirm it calls tools and produces the full advisory shape (including the
  new billing-risk projection line) before exporting.

## Export steps
1. In Playground, click **Get code** > **Export to Databricks Apps**.
2. App name must start with `agent-` and contain only lowercase letters, numbers, and hyphens —
   e.g. `agent-ami-network-health`.
3. Add a short app description (e.g. "AMI Network Health Monitoring Agent — DivyaNetra demo").
4. Select or create an MLflow experiment for tracing (useful if you want to show a trace of a
   tool call during the demo as a "look, it's really calling the data" moment).
5. Confirm the permission grants Databricks proposes — MLflow experiment, serving endpoint, and
   the 4 UC functions. Accept them.
6. Wait for install/deploy to finish, then click **View Agent** to open the generated app — this
   has a built-in chat UI and becomes the primary demo surface.

## Free Edition notes
- Free Edition allows **1 app per account**. If you already have another app deployed, you'll
  need to delete it first or reuse that slot.
- Apps auto-stop 24 hours after being started/updated/redeployed. **Redeploy or restart it the
  morning of the demo** so it's fresh and warm when you present.

## If export isn't available or fails
Fall back to demoing directly from the AI Playground screen — same agent, same tools, same
system prompt, just a less polished UI. Nothing about the underlying capability changes.
