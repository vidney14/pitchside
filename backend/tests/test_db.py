import pytest

from pipeline import db


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    c.execute(
        "INSERT INTO players (player_id, name, team, position) VALUES (5503, 'Lionel Messi', 'Argentina', 'Forward')"
    )
    return c


def base_event(**overrides):
    ev = {
        "event_id": "e1", "idx": 1, "period": 1, "minute": 10, "second": 0,
        "team": "Argentina", "player_id": 5503, "event_type": "Pass",
        "x": 10.0, "y": 20.0, "outcome": "Complete",
    }
    ev.update(overrides)
    return ev


def test_insert_and_read_back(conn):
    db.insert_event(conn, base_event())
    assert conn.execute("SELECT count(*) FROM events").fetchone()[0] == 1


def test_unknown_player_id_rejected(conn):
    with pytest.raises(ValueError, match="not in player registry"):
        db.insert_event(conn, base_event(event_id="e2", player_id=999999))


def test_null_player_id_allowed(conn):
    # e.g. a Half Start event has no player
    db.insert_event(conn, base_event(event_id="e3", player_id=None))
    assert conn.execute("SELECT count(*) FROM events").fetchone()[0] == 1


def test_column_bounds_enforced_after_alter(conn):
    # simulates the day-6 bug: an unconstrained ALTER TABLE let an
    # impossible xg=9.5 in silently. insert_event must reject it once
    # the agent has registered bounds for the column.
    conn.execute("ALTER TABLE events ADD COLUMN xg FLOAT")
    conn.execute("INSERT INTO column_bounds VALUES ('xg', 0.0, 1.0)")

    db.insert_event(conn, base_event(event_id="e4", xg=0.42))  # in range: fine

    with pytest.raises(ValueError, match="outside registered bounds"):
        db.insert_event(conn, base_event(event_id="e5", xg=9.5))


def test_stats_counts_by_team_and_type(conn):
    db.insert_event(conn, base_event())
    db.insert_event(conn, base_event(event_id="e2", event_type="Shot", team="France"))
    s = db.stats(conn)
    assert s["total_events"] == 2
    assert s["by_team"] == {"Argentina": 1, "France": 1}
    assert s["by_event_type"] == {"Pass": 1, "Shot": 1}
