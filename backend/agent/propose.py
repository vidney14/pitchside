import json

from agent.llm import structured
from agent.schemas import FixProposal

SYSTEM = """You propose a fix for a failed insert in a football event pipeline.

Allowed actions:
- alter_table: ONLY `ALTER TABLE events ADD COLUMN <name> <TYPE>`. New columns are always nullable.
  Use when the feed added a genuinely new, plausible measurement.
- transform_payload: change values in the payload before retrying. Use for wrong types
  ("46'" -> 46), or replacing a name with a looked-up id.
- skip_record: the record is a harmless duplicate.
- escalate: you are not confident, OR the value is impossible/corrupt. Never invent a fix
  for corrupt data. An impossible value must NEVER become a new column.

Rules:
- xG must be between 0 and 1. minute >= 0. second 0-59. period 1-5.
- If evidence shows a value outside its valid range, action MUST be escalate.
- confidence below 0.8 means escalate.
- payload_patch: use {"key": value} to set, {"key": null} to remove.

- -When adding a column for a metric with known bounds (e.g. xg is 0-1), set the `bounds`
  field to [min, max]. The column itself is unconstrained; the pipeline enforces the range."""


def propose(case: dict, triage_result, evidence: list, provider: str = "groq") -> FixProposal:
    user = (
        f"ERROR: {case['error']}\n"
        f"PAYLOAD: {json.dumps(case['payload'], default=str)}\n"
        f"TRIAGE: {triage_result.failure_class} | suspicious={triage_result.suspicious_value} | {triage_result.summary}\n"
        f"EVIDENCE: {json.dumps(evidence, default=str)}"
    )
    return structured(provider, FixProposal, [("system", SYSTEM), ("user", user)])