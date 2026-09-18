import json
import os
from pathlib import Path

import duckdb

DEFAULT_DB = Path(os.environ.get(
    "PITCHSIDE_DB_PATH",
    str(Path(__file__).resolve().parents[1] / "pitchside.duckdb"),
))

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    player_id  INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    team       VARCHAR NOT NULL,
    position   VARCHAR
);

CREATE TABLE IF NOT EXISTS events (
    event_id   VARCHAR PRIMARY KEY,
    idx        INTEGER NOT NULL,
    period     INTEGER NOT NULL CHECK (period BETWEEN 1 AND 5),
    minute     INTEGER NOT NULL CHECK (minute >= 0),
    second     INTEGER NOT NULL CHECK (second BETWEEN 0 AND 59),
    team       VARCHAR NOT NULL,
    player_id  INTEGER,
    event_type VARCHAR NOT NULL,
    x          FLOAT,
    y          FLOAT,
    outcome    VARCHAR
);

CREATE SEQUENCE IF NOT EXISTS audit_seq;

CREATE TABLE IF NOT EXISTS audit_log (
    id      INTEGER DEFAULT nextval('audit_seq'),
    ts      TIMESTAMP DEFAULT now(),
    stage   VARCHAR NOT NULL,
    detail  JSON
);

CREATE TABLE IF NOT EXISTS column_bounds (
    column_name VARCHAR PRIMARY KEY,
    min_value   DOUBLE,
    max_value   DOUBLE
);

CREATE SEQUENCE IF NOT EXISTS rule_seq;

CREATE TABLE IF NOT EXISTS rules (
    id                 INTEGER DEFAULT nextval('rule_seq'),
    failure_class      VARCHAR NOT NULL,
    error_pattern      VARCHAR NOT NULL,
    payload_pattern    JSON,
    action             VARCHAR NOT NULL,
    sql                VARCHAR,
    payload_patch      JSON,
    created_from_audit INTEGER,
    enabled            BOOLEAN NOT NULL DEFAULT true,
    hits               INTEGER NOT NULL DEFAULT 0,
    created_at         TIMESTAMP DEFAULT now()
);
"""


def connect(path=None, fresh=False):
    """Open the database (create it if needed). fresh=True deletes it first.
    Pass ":memory:" for a throwaway database."""
    if path is None:
        path = DEFAULT_DB
    if str(path) != ":memory:" and fresh:
        Path(path).unlink(missing_ok=True)
    conn = duckdb.connect(str(path))
    conn.execute(SCHEMA)
    return conn


def load_players(conn, lineups) -> int:
    """Insert every player from both teams' lineups. Return how many."""
    rows = []
    for team in lineups:
        for p in team["lineup"]:
            # unused substitutes have an empty positions list
            position = p["positions"][0]["position"] if p["positions"] else None
            rows.append((p["player_id"], p["player_name"], team["team_name"], position))
    conn.executemany(
        "INSERT OR REPLACE INTO players (player_id, name, team, position) VALUES (?, ?, ?, ?)",
        rows,
    )
    return len(rows)


def insert_event(conn, ev: dict) -> None:
    """Insert one flattened event.

    The column list is built from the payload's keys on purpose. If the feed
    sends a field the table doesn't have (e.g. "xg"), DuckDB raises a real
    'column does not exist' error. That error is what the agent reasons about.
    Hardcoding the columns would silently drop the new field.

    Two checks run before the insert, both enforcing rules the schema cannot:
    - bounds registered by the agent when it created a bounded column
    - referential integrity for player_id
    """
    bounds = dict(
        (row[0], (row[1], row[2]))
        for row in conn.execute(
            "SELECT column_name, min_value, max_value FROM column_bounds"
        ).fetchall()
    )
    for col, val in ev.items():
        if col in bounds and isinstance(val, (int, float)):
            lo, hi = bounds[col]
            if not (lo <= val <= hi):
                raise ValueError(f"{col}={val} outside registered bounds [{lo}, {hi}]")

    if ev.get("player_id") is not None:
        known = conn.execute(
            "SELECT 1 FROM players WHERE player_id = ?", [ev["player_id"]]
        ).fetchone()
        if not known:
            raise ValueError(f"player_id {ev['player_id']} not in player registry")

    cols = list(ev.keys())
    col_list = ", ".join(cols)
    placeholders = ", ".join("?" for _ in cols)
    values = [ev[c] for c in cols]
    conn.execute(f"INSERT INTO events ({col_list}) VALUES ({placeholders})", values)


def stats(conn) -> dict:
    """Summary of the current match state, for the dashboard's stats panel."""
    total = conn.execute("SELECT count(*) FROM events").fetchone()[0]
    by_type = conn.execute(
        "SELECT event_type, count(*) FROM events GROUP BY event_type ORDER BY 2 DESC"
    ).fetchall()
    by_team = conn.execute("SELECT team, count(*) FROM events GROUP BY team").fetchall()
    by_stage = conn.execute("SELECT stage, count(*) FROM audit_log GROUP BY stage").fetchall()
    return {
        "total_events": total,
        "by_event_type": dict(by_type),
        "by_team": dict(by_team),
        "audit_by_stage": dict(by_stage),
    }


def recent_audit(conn, limit: int = 200) -> list[dict]:
    rows = conn.execute(
        "SELECT id, ts, stage, detail FROM audit_log ORDER BY id DESC LIMIT ?", [limit]
    ).fetchall()
    return [{"id": r[0], "ts": str(r[1]), "stage": r[2], "detail": json.loads(r[3])} for r in rows]


def list_rules(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT id, failure_class, error_pattern, payload_pattern, action, sql, "
        "payload_patch, created_from_audit, enabled, hits, created_at FROM rules ORDER BY id"
    ).fetchall()
    cols = ["id", "failure_class", "error_pattern", "payload_pattern", "action", "sql",
            "payload_patch", "created_from_audit", "enabled", "hits", "created_at"]
    out = []
    for row in rows:
        d = dict(zip(cols, row))
        d["created_at"] = str(d["created_at"])
        if d["payload_pattern"]:
            d["payload_pattern"] = json.loads(d["payload_pattern"])
        if d["payload_patch"]:
            d["payload_patch"] = json.loads(d["payload_patch"])
        out.append(d)
    return out