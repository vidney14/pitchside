import json

from pipeline import db, rules


def test_error_signature_collapses_digits():
    a = rules.error_signature("player_id 999999 not in player registry")
    b = "player_id 42 not in player registry"
    assert __import__("re").search(a, b)


def test_promotion_requires_min_hits():
    conn = db.connect(":memory:")
    detail = {
        "error_signature": rules.error_signature("Binder Error: no column xg"),
        "failure_class": "schema_drift",
        "action": "alter_table",
        "sql": "ALTER TABLE events ADD COLUMN xg FLOAT",
    }
    for _ in range(2):  # below the default threshold of 3
        conn.execute("INSERT INTO audit_log (stage, detail) VALUES ('HEALED', ?)", [json.dumps(detail)])
    assert rules.promotion_candidates(conn, min_hits=3) == []

    conn.execute("INSERT INTO audit_log (stage, detail) VALUES ('HEALED', ?)", [json.dumps(detail)])
    candidates = rules.promotion_candidates(conn, min_hits=3)
    assert len(candidates) == 1
    assert candidates[0]["action"] == "alter_table"


def test_find_rule_matches_generalized_pattern_and_applies():
    conn = db.connect(":memory:")
    rules.promote_rule(
        conn, failure_class="schema_drift",
        error_pattern=rules.error_signature('Table "events" does not have a column with name "xg"'),
        action="alter_table", sql="ALTER TABLE events ADD COLUMN xg FLOAT",
    )
    match = rules.find_rule(conn, 'Table "events" does not have a column with name "xg"', {})
    assert match is not None
    assert match["action"] == "alter_table"

    applied = rules.apply_rule(conn, match, {"xg": 0.3})
    assert applied["healed"] is True
    assert conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name='events' AND column_name='xg'"
    ).fetchone() is not None


def test_find_rule_respects_payload_pattern():
    conn = db.connect(":memory:")
    rules.promote_rule(
        conn, failure_class="data_quality", error_pattern="misspelled",
        action="transform_payload", payload_patch={"player_id": 5503},
        payload_pattern={"player_name": "Lionel Mesi"},
    )
    assert rules.find_rule(conn, "misspelled name", {"player_name": "Lionel Mesi"}) is not None
    assert rules.find_rule(conn, "misspelled name", {"player_name": "Someone Else"}) is None


def test_record_hit_increments():
    conn = db.connect(":memory:")
    rid = rules.promote_rule(conn, failure_class="x", error_pattern="x", action="skip_record")
    rules.record_hit(conn, rid)
    rules.record_hit(conn, rid)
    hits = conn.execute("SELECT hits FROM rules WHERE id = ?", [rid]).fetchone()[0]
    assert hits == 2
