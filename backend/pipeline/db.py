from pathlib import Path

import duckdb

DEFAULT_DB = Path(__file__).resolve().parents[1] / "pitchside.duckdb"

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
    'column does not exist' error. That error is what the agent will reason
    about later. Hardcoding the columns would silently drop the new field
    and the failure would never surface.
    """
    cols = list(ev.keys())
    col_list = ", ".join(cols)
    placeholders = ", ".join("?" for _ in cols)
    values = [ev[c] for c in cols]
    conn.execute(f"INSERT INTO events ({col_list}) VALUES ({placeholders})", values)