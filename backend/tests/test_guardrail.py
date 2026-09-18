from agent.guardrail import check
from agent.schemas import FixProposal, Triage
from pipeline import db


def make_triage(**overrides):
    d = dict(failure_class="schema_drift", summary="x", suspicious_value=False,
             needs_investigation=False, confidence=0.9)
    d.update(overrides)
    return Triage(**d)


def make_proposal(**overrides):
    d = dict(action="alter_table", diagnosis="x", sql="ALTER TABLE events ADD COLUMN xg FLOAT",
             confidence=0.9, rationale="x")
    d.update(overrides)
    return FixProposal(**d)


def test_escalate_action_always_blocked():
    conn = db.connect(":memory:")
    ok, why = check(make_proposal(action="escalate", sql=None), conn, make_triage())
    assert ok is False
    assert "escalate" in why


def test_low_confidence_blocked():
    conn = db.connect(":memory:")
    ok, why = check(make_proposal(confidence=0.5), conn, make_triage())
    assert ok is False
    assert "confidence" in why


def test_suspicious_value_cannot_become_column():
    conn = db.connect(":memory:")
    ok, why = check(make_proposal(), conn, make_triage(suspicious_value=True))
    assert ok is False
    assert "new column" in why


def test_alter_table_sql_must_match_allowlist():
    conn = db.connect(":memory:")
    ok, why = check(make_proposal(sql="DROP TABLE events"), conn, make_triage())
    assert ok is False
    assert "not allowlisted" in why


def test_alter_table_dry_run_failure_blocked():
    conn = db.connect(":memory:")
    conn.execute("ALTER TABLE events ADD COLUMN xg FLOAT")
    # adding the same column again should fail the dry run
    ok, why = check(make_proposal(), conn, make_triage())
    assert ok is False
    assert "dry-run failed" in why


def test_valid_alter_table_passes():
    conn = db.connect(":memory:")
    ok, why = check(make_proposal(), conn, make_triage())
    assert ok is True


def test_transform_payload_requires_patch():
    conn = db.connect(":memory:")
    ok, why = check(make_proposal(action="transform_payload", sql=None, payload_patch=None), conn, make_triage())
    assert ok is False
    assert "no patch" in why
