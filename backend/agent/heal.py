import json

from agent.guardrail import check
from agent.investigate import investigate
from agent.propose import propose
from agent.triage import triage


def apply_patch(payload: dict, patch: dict) -> dict:
    """Apply a payload_patch: set values, remove keys where the value is None."""
    out = dict(payload)
    for key, value in patch.items():
        if value is None:
            out.pop(key, None)
        else:
            out[key] = value
    return out


def heal(case: dict, bus=None, provider: str = "groq") -> dict:
    """Run the full agent graph. Returns what to do with the event."""
    conn = case["conn"]

    def say(stage, text, **d):
        if bus:
            bus.emit(stage, text, **d)

    t = triage(case, provider)
    say("AGENT", f"triage → {t.failure_class} ({t.confidence})", summary=t.summary)

    ev = investigate(case, t, provider)
    say("AGENT", f"investigate → {[e['tool'] for e in ev]}")

    p = propose(case, t, ev, provider)
    say("AGENT", f"propose → {p.action}", detail=p.sql or p.payload_patch)

    ok, why = check(p, conn, t)
    say("GUARD" if ok else "ESCALATE", why)

    if not ok:
        return {"healed": False, "reason": why, "proposal": p}

    if p.action == "alter_table":
        conn.execute(p.sql)
        if p.bounds:
            col = p.sql.split("ADD COLUMN")[1].split()[0]
            conn.execute(
                "INSERT OR REPLACE INTO column_bounds VALUES (?, ?, ?)",
                [col, p.bounds[0], p.bounds[1]],
            )
            say("GUARD", f"registered bounds {col} in {p.bounds}")
        say("HEALED", f"applied: {p.sql}")
        return {"healed": True, "payload": case["payload"], "proposal": p}

    if p.action == "transform_payload":
        fixed = apply_patch(case["payload"], p.payload_patch)
        say("HEALED", f"patched: {json.dumps(p.payload_patch, default=str)}")
        return {"healed": True, "payload": fixed, "proposal": p}

    if p.action == "skip_record":
        say("HEALED", "skipped duplicate")
        return {"healed": True, "payload": None, "proposal": p}

    return {"healed": False, "reason": "unknown action", "proposal": p}