# Findings

- Day 3, triage: with a plain prompt, Gemini classified scenario 6 (player_name replacing player_id) as schema_drift because it trusted the error message over the payload. Fixed by adding a "compare payload keys to schema" rule to the system prompt. Not a scenario-specific hack; applies to any renamed/substituted field.

- Day 3, model comparison: on scenario 13 (xg=9.5) Gemini classified data_quality; Groq gpt-oss-120b classified schema_drift despite flagging suspicious_value=true and confidence 0.6. Groq noticed the impossible value but still classified from the error text. Guardrail (day 5) must key off suspicious_value and confidence, not failure_class alone.

 - Day 4, investigate: on scenario 13 the agent called value_stats("x") instead of the failing field. value_stats only works on existing columns, so a brand-new field can never be checked this way. Fix: prompt now tells the agent that for a new field it must reason from domain knowledge, not tools.
  - Gemini free tier is 20 req/day. Switched development to Groq; Gemini reserved for the final eval run.

- Day 5: Groq sometimes emits `done` as a literal tool name instead of an enum value in the ToolCall schema, causing a 400. Investigate loop now treats an unparseable tool call as "done" — the agent proceeds with whatever evidence it has rather than crashing. Degrades gracefully instead of failing the whole heal.

 - Day 6, real bug: when scenario 1 (xg=0.42) and 13 (xg=9.5) run in the same match, the agent's ALTER TABLE for scenario 1 creates an unconstrained FLOAT column. Scenario 13 then inserts silently — no error, no escalation, corrupt data stored. Fix: when adding a column for a metric with known bounds, the agent must include a CHECK constraint. Guardrail now requires it for bounded fields.

- Day 6 fix: DuckDB rejects ADD COLUMN with CHECK (dry-run caught it). Moved bounds
  enforcement into the pipeline: the agent registers [min,max] in a column_bounds table
  when it creates a bounded column, and insert_event validates against it. Result:
  scenario 13 is now caught even after scenario 1 created the column.
