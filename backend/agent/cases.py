import json

from pipeline import db
from pipeline.poison import inject
from pipeline.replay import DATA_FILE, match_events


def capture_failure(scenario_id: int) -> dict:
    """Replay a scenario in a fresh in-memory DB until it crashes.
    Returns the error message, the failing payload, and the current schema."""
    conn = db.connect(":memory:")
    with open(DATA_FILE) as f:
        db.load_players(conn, json.load(f)["lineups"])

    events = inject(match_events(), [scenario_id])
    for ev in events:
        ev.pop("_scenario", None)
        try:
            db.insert_event(conn, ev)
        except Exception as exc:
            return {
                "scenario": scenario_id,
                "error": str(exc).splitlines()[0],
                "payload": ev,
                "schema": conn.execute(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_name = 'events' ORDER BY ordinal_position"
                ).fetchall(),
            }
    raise RuntimeError(f"scenario {scenario_id} did not fail")