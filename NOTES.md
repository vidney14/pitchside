# Findings

- Day 3, triage: with a plain prompt, Gemini classified scenario 6 (player_name replacing player_id) as schema_drift because it trusted the error message over the payload. Fixed by adding a "compare payload keys to schema" rule to the system prompt. Not a scenario-specific hack; applies to any renamed/substituted field.

- Day 3, model comparison: on scenario 13 (xg=9.5) Gemini classified data_quality; Groq gpt-oss-120b classified schema_drift despite flagging suspicious_value=true and confidence 0.6. Groq noticed the impossible value but still classified from the error text. Guardrail (day 5) must key off suspicious_value and confidence, not failure_class alone.

- - Day 4, investigate: on scenario 13 the agent called value_stats("x") instead of the failing field. value_stats only works on existing columns, so a brand-new field can never be checked this way. Fix: prompt now tells the agent that for a new field it must reason from domain knowledge, not tools.
  - Gemini free tier is 20 req/day. Switched development to Groq; Gemini reserved for the final eval run.
