import copy

# Each scenario: how to break it, and what the CORRECT answer is.
# expected_action is the label the eval harness scores against.
SCENARIOS = {
    1: {
        "name": "new field xg on a Shot",
        "target": lambda ev: ev["event_type"] == "Shot",
        "mutate": lambda ev: ev.update({"xg": 0.42}),
        "expected_action": "alter_table",
    },
    2: {
        "name": "new field pass_length on a Pass",
        "target": lambda ev: ev["event_type"] == "Pass",
        "mutate": lambda ev: ev.update({"pass_length": 23.4}),
        "expected_action": "alter_table",
    },
    3: {
        "name": "player_id renamed to actor",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["player_id"],
        "mutate": lambda ev: ev.update({"actor": ev.pop("player_id")}),
        "expected_action": "transform_payload",
    },
    4: {
        "name": "minute arrives as a string like 47'",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["minute"] > 45,
        "mutate": lambda ev: ev.update({"minute": f"{ev['minute']}'"}),
        "expected_action": "transform_payload",
    },
    5: {
        "name": "x and y merged into one string",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["x"],
        "mutate": lambda ev: ev.update({"location": f"{ev.pop('x')},{ev.pop('y')}"}),
        "expected_action": "transform_payload",
    },
    6: {
        "name": "misspelled player name, no id",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["player_id"] == 5503,
        "mutate": lambda ev: (ev.pop("player_id"), ev.update({"player_name": "Lionel Mesi"})),
        "expected_action": "transform_payload",
    },
    7: {
        "name": "unknown player id (substitute not in registry)",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["idx"] > 500,
        "mutate": lambda ev: ev.update({"player_id": 999999}),
        "expected_action": "escalate",
    },
    8: {
        "name": "team key renamed to team_name",
        "target": lambda ev: ev["team"] == "Argentina" and ev["idx"] > 300,
        "mutate": lambda ev: ev.update({"team_name": ev.pop("team")}),
        "expected_action": "transform_payload",
    },
    9: {
        "name": "duplicate event_id, identical payload",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["idx"] > 200,
        "mutate": lambda ev: ev.update({"event_id": "DUPLICATE-1"}),
        "expected_action": "skip_record",
        "twin": True,
    },
    10: {
        "name": "x arrives as a text label instead of a coordinate",
        "target": lambda ev: ev["event_type"] == "Shot" and ev["idx"] > 300,
        "mutate": lambda ev: ev.update({"x": "left-center"}),
        "expected_action": "escalate",
    },
    11: {
        "name": "idx arrives as text",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["idx"] > 700,
        "mutate": lambda ev: ev.update({"idx": f"e{ev['idx']}"}),
        "expected_action": "escalate",
    },
    12: {
        "name": "nested location object",
        "target": lambda ev: ev["event_type"] == "Shot" and ev["idx"] > 500,
        "mutate": lambda ev: ev.update({"coords": {"x": ev.pop("x"), "y": ev.pop("y")}}),
        "expected_action": "transform_payload",
    },
    13: {
        "name": "xg = 9.5, impossible value",
        "target": lambda ev: ev["event_type"] == "Shot" and ev["idx"] > 400,
        "mutate": lambda ev: ev.update({"xg": 9.5}),
        "expected_action": "escalate",
    },
    14: {
        "name": "minute = -3",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["idx"] > 600,
        "mutate": lambda ev: ev.update({"minute": -3}),
        "expected_action": "escalate",
    },
    15: {
        "name": "second = 99",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["idx"] > 800,
        "mutate": lambda ev: ev.update({"second": 99}),
        "expected_action": "escalate",
    },
    16: {
        "name": "period = 9",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["idx"] > 900,
        "mutate": lambda ev: ev.update({"period": 9}),
        "expected_action": "escalate",
    },
    17: {
        "name": "payload is a lineup object, not an event",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["idx"] > 1000,
        "mutate": lambda ev: (ev.clear(), ev.update({"squad": "Argentina", "formation": "4-3-3"})),
        "expected_action": "escalate",
    },
    18: {
        "name": "required team field missing",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["idx"] > 1100,
        "mutate": lambda ev: ev.pop("team"),
        "expected_action": "transform_payload",
    },
    19: {
        "name": "ten new fields at once (provider version bump)",
        "target": lambda ev: ev["event_type"] == "Shot" and ev["idx"] > 700,
        "mutate": lambda ev: ev.update({f"metric_{i}": i * 0.1 for i in range(10)}),
        "expected_action": "alter_table",
    },
    20: {
        "name": "event_id is null",
        "target": lambda ev: ev["event_type"] == "Pass" and ev["idx"] > 1200,
        "mutate": lambda ev: ev.update({"event_id": None}),
        "expected_action": "escalate",
    },
}


def inject(events: list[dict], scenario_ids: list[int]) -> list[dict]:
    """Return a copy of events with each scenario applied to one event."""
    out = copy.deepcopy(events)
    for sid in scenario_ids:
        sc = SCENARIOS[sid]
        for i, ev in enumerate(out):
            if ev.get("idx", 0) > 40 and "_scenario" not in ev and sc["target"](ev):
                if sc.get("twin"):
                    twin = copy.deepcopy(ev)
                    twin["event_id"] = "DUPLICATE-1"
                    out.insert(i, twin)
                sc["mutate"](ev)
                ev["_scenario"] = sid
                break
    return out