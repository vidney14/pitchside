import json
import sys

from pipeline import bus as B
from pipeline import db
from pipeline.poison import inject
from pipeline.replay import DATA_FILE, match_events, replay


def main():
    conn = db.connect(fresh=True)
    bus = B.Bus(conn)
    bus.subscribe(B.terminal_printer)

    with open(DATA_FILE) as f:
        lineups = json.load(f)["lineups"]
    n = db.load_players(conn, lineups)
    bus.emit(B.INFO, f"loaded {n} players")

    events = match_events()
    scenario_ids = [int(s) for s in sys.argv[1:]]
    if scenario_ids:
        events = inject(events, scenario_ids)
        bus.emit(B.INFO, f"poison pills armed: {scenario_ids}")

    for ev in replay(events, delay=0):
        scenario = ev.pop("_scenario", None)
        try:
            db.insert_event(conn, ev)
            bus.emit(B.OK, f"{ev['minute']:>3}'  {ev['event_type']:<14} {ev['team']}", event_id=ev["event_id"])
        except Exception as exc:
            bus.emit(B.CRITICAL, f"event {ev['idx']} (scenario {scenario}) failed: {exc}",
                     event_id=ev["event_id"], scenario=scenario, payload=ev, error=str(exc))
            bus.emit(B.FATAL, "pipeline halted — no agent attached yet")
            break

    total = conn.execute("SELECT count(*) FROM events").fetchone()[0]
    bus.emit(B.INFO, f"done: {total} events in the database")


if __name__ == "__main__":
    main()