from pipeline.poison import SCENARIOS, inject
from pipeline.replay import match_events

VALID_ACTIONS = {"alter_table", "transform_payload", "skip_record", "escalate"}


def test_every_scenario_has_a_valid_expected_action():
    for sid, sc in SCENARIOS.items():
        assert sc["expected_action"] in VALID_ACTIONS, f"scenario {sid} has an invalid expected_action"


def test_inject_marks_exactly_one_event_per_scenario():
    events = match_events()
    for sid in SCENARIOS:
        out = inject(events, [sid])
        tagged = [e for e in out if e.get("_scenario") == sid]
        assert len(tagged) == 1, f"scenario {sid} tagged {len(tagged)} events, expected 1"


def test_scenario_9_inserts_a_duplicate_twin():
    events = match_events()
    out = inject(events, [9])
    dup_ids = [e["event_id"] for e in out if e["event_id"] == "DUPLICATE-1"]
    assert len(dup_ids) == 2, "scenario 9 should produce two events sharing event_id DUPLICATE-1"
