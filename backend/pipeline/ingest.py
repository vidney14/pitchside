import json
import sys

from pipeline import bus as B
from pipeline import db
from pipeline import rules
from pipeline.poison import inject
from pipeline.replay import DATA_FILE, match_events, replay

from agent import tools
from agent.heal import heal


def run_ingestion(conn, bus, scenario_ids=None, stop_event=None, delay: float = 0.0,
                   provider: str = "groq") -> None:
    """Replay the match, healing failures as they happen. Shared by the CLI
    and the API so both go through the exact same pipeline.

    stop_event: a threading.Event; when set, the run stops after the event
    currently in flight instead of running to the end of the match.
    """
    with open(DATA_FILE) as f:
        lineups = json.load(f)["lineups"]
    n = db.load_players(conn, lineups)
    bus.emit(B.INFO, f"loaded {n} players")

    events = match_events()
    if scenario_ids:
        events = inject(events, scenario_ids)
        bus.emit(B.INFO, f"poison pills armed: {scenario_ids}")

    for ev in replay(events, delay=delay):
        if stop_event is not None and stop_event.is_set():
            bus.emit(B.INFO, "run stopped by request")
            return

        scenario = ev.pop("_scenario", None)
        try:
            db.insert_event(conn, ev)
            bus.emit(B.OK, f"{ev['minute']:>3}'  {ev['event_type']:<14} {ev['team']}", event_id=ev["event_id"])
        except Exception as exc:
            error = str(exc).splitlines()[0]
            bus.emit(B.CRITICAL, f"event {ev['idx']} (scenario {scenario}) failed: {exc}",
                     event_id=ev["event_id"], scenario=scenario)

            rule = rules.find_rule(conn, error, ev)
            if rule:
                rules.record_hit(conn, rule["id"])
                applied = rules.apply_rule(conn, rule, ev)
                bus.emit(B.RULE, f"rule {rule['id']} matched ({rule['action']}) — no LLM call",
                         event_id=ev["event_id"], rule_id=rule["id"])
                if applied["healed"] and applied["payload"]:
                    db.insert_event(conn, applied["payload"])
                    bus.emit(B.OK, f"retried event {ev['idx']} successfully (via rule)")
                elif applied["healed"]:
                    bus.emit(B.OK, f"event {ev['idx']} skipped via rule")
                else:
                    bus.emit(B.ESCALATE, f"event {ev['idx']} quarantined (rule did not resolve)")
                continue

            case = {
                "error": error,
                "payload": ev,
                "conn": conn,
                "schema": [(c["column"], c["type"]) for c in tools.get_schema(conn)],
            }
            result = heal(case, bus, provider=provider)

            if result["healed"] and result["payload"]:
                db.insert_event(conn, result["payload"])
                bus.emit(B.OK, f"retried event {ev['idx']} successfully")
            elif not result["healed"]:
                bus.emit(B.ESCALATE, f"event {ev['idx']} quarantined for human review")

    total = conn.execute("SELECT count(*) FROM events").fetchone()[0]
    bus.emit(B.INFO, f"done: {total} events in the database")


def main():
    conn = db.connect(fresh=True)
    bus = B.Bus(conn)
    bus.subscribe(B.terminal_printer)
    scenario_ids = [int(s) for s in sys.argv[1:]]
    run_ingestion(conn, bus, scenario_ids, delay=0)


if __name__ == "__main__":
    main()
