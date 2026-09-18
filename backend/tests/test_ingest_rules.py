"""A promoted rule must short-circuit the LLM agent entirely."""
import json

import pipeline.ingest as ingest_mod
from pipeline import bus as B
from pipeline import db, rules
from pipeline.replay import DATA_FILE


def test_promoted_rule_intercepts_before_llm(monkeypatch):
    conn = db.connect(":memory:")
    rules.promote_rule(
        conn, failure_class="schema_drift",
        error_pattern=rules.error_signature('Table "events" does not have a column with name "xg"'),
        action="alter_table", sql="ALTER TABLE events ADD COLUMN xg FLOAT",
    )

    with open(DATA_FILE) as f:
        lineups = json.load(f)["lineups"]
    db.load_players(conn, lineups)

    seen = []
    bus = B.Bus(conn)
    bus.subscribe(seen.append)

    def fail_if_called(*a, **kw):
        raise AssertionError("heal() should not be called when a rule matches")

    monkeypatch.setattr(ingest_mod, "heal", fail_if_called)

    ingest_mod.run_ingestion(conn, bus, scenario_ids=[1], delay=0)

    stages = [m["stage"] for m in seen]
    assert "RULE" in stages
    assert "AGENT" not in stages
    assert conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name='events' AND column_name='xg'"
    ).fetchone() is not None
