import json

from agent import tools
from agent.llm import structured
from agent.schemas import ToolCall

SYSTEM = """You are investigating a failed insert in a football event pipeline.
You may call tools to inspect the database before a fix is proposed.

Tools:
- get_schema: current columns and types of the events table
- sample_rows: a few real rows, to see what normal data looks like
- lookup_player: fuzzy-match a player name against the registry (argument = the name)
- value_stats: min/max/nulls for a column (argument = column name)
- done: you have enough evidence

Rules:
- Call at most 3 tools, then done.
- If the payload has a player name but no player_id, use lookup_player.
- If a value looks out of range, use value_stats on that column to compare.
- Do not repeat a tool you have already called.
- value_stats only works on columns that already exist. If the suspicious field is new
  (not in the schema), do not call value_stats on an unrelated column — judge the value
  from domain knowledge instead and call done."""


def investigate(case: dict, triage_result, provider: str = "groq", max_steps: int = 3) -> list[dict]:
    """Let the model choose tools. Returns the evidence it gathered."""
    conn = case["conn"]
    evidence = []

    for _ in range(max_steps):
        user = (
            f"ERROR: {case['error']}\n"
            f"PAYLOAD: {json.dumps(case['payload'], default=str)}\n"
            f"TRIAGE: {triage_result.failure_class} - {triage_result.summary}\n"
            f"EVIDENCE SO FAR: {json.dumps(evidence, default=str)}"
        )
        call = structured(provider, ToolCall, [("system", SYSTEM), ("user", user)])
        if call.tool == "done":
            break

        if call.tool == "get_schema":
            result = tools.get_schema(conn)
        elif call.tool == "sample_rows":
            result = tools.sample_rows(conn)
        elif call.tool == "lookup_player":
            result = tools.lookup_player(conn, call.argument)
        elif call.tool == "value_stats":
            result = tools.value_stats(conn, call.argument)
        else:
            result = None

        evidence.append({"tool": call.tool, "argument": call.argument, "why": call.why, "result": result})

    return evidence