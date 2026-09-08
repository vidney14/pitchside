# Findings

- Day 3, triage: with a plain prompt, Gemini classified scenario 6 (player_name replacing player_id) as schema_drift because it trusted the error message over the payload. Fixed by adding a "compare payload keys to schema" rule to the system prompt. Not a scenario-specific hack; applies to any renamed/substituted field.
