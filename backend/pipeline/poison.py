import copy

# Each scenario: which event to hit, and how to break it.
SCENARIOS = {
    1: {
        "name": "new field xg on a Shot",
        "target": lambda ev: ev["event_type"] == "Shot",
        "mutate": lambda ev: ev.update({"xg": 0.42}),
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