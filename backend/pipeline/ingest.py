import json

from pipeline import db
from pipeline.replay import DATA_FILE, match_events, replay

import sys
from pipeline.poison import inject


def main():
    conn = db.connect(fresh=True)

    with open(DATA_FILE) as f:
        lineups = json.load(f)["lineups"]
    n = db.load_players(conn, lineups)
    print(f"loaded {n} players")

    events = match_events()
    scenario_ids = [int(s) for s in sys.argv[1:]]
    if scenario_ids:
        events = inject(events, scenario_ids)
        print(f"poison pills armed: {scenario_ids}")

    for ev in replay(events, delay=0):
        scenario = ev.pop("_scenario", None)
        try:
            db.insert_event(conn, ev)
            print(f"[OK]        {ev['minute']:>3}'  {ev['event_type']:<14} {ev['team']}")
        except Exception as exc:
            print(f"[CRITICAL]  event {ev['idx']} (scenario {scenario}) failed: {exc}")
            print("pipeline halted — no agent attached yet")
            break

    total = conn.execute("SELECT count(*) FROM events").fetchone()[0]
    print(f"done: {total} events in the database")


if __name__ == "__main__":
    main()