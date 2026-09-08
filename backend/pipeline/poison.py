import copy

# Each scenario: which event to hit, and how to break it.
SCENARIOS = {
    1: {
        "name": "new field xg on a Shot",
        "target": lambda ev: ev["event_type"] == "Shot",
        "mutate": lambda ev: ev.update({"xg": 0.42}),
    },
        4: {
        "name": "minute arrives as a string like 47'",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["minute"] > 45,
        "mutate": lambda ev: ev.update({"minute": f"{ev['minute']}'"}),
    },
    6: {
        "name": "misspelled player name, no id",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["player_id"] == 5503,  # Messi
        "mutate": lambda ev: (ev.pop("player_id"), ev.update({"player_name": "Lionel Mesi"})),
    },
    13: {
        "name": "xg = 9.5, impossible value",
        "target": lambda ev: ev["event_type"] == "Shot" and ev["idx"] > 400,
        "mutate": lambda ev: ev.update({"xg": 9.5}),
    },
}


def inject(events: list[dict], scenario_ids: list[int]) -> list[dict]:
    """Return a copy of events with each scenario applied to one event."""
    out = copy.deepcopy(events)
    for sid in scenario_ids:
        sc = SCENARIOS[sid]
        for ev in out:
            if ev["idx"] > 40 and sc["target"](ev):
                sc["mutate"](ev)
                ev["_scenario"] = sid
                break
    return out