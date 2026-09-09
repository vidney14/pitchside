from rapidfuzz import process


def get_schema(conn, table: str = "events") -> list[dict]:
    """Table ke columns aur unke types."""
    rows = conn.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = ? ORDER BY ordinal_position", [table]
    ).fetchall()
    return [{"column": c, "type": t} for c, t in rows]


def sample_rows(conn, n: int = 5) -> list[dict]:
    """Kuch asli rows, taaki AI dekhe data normally kaisa dikhta hai."""
    cur = conn.execute(f"SELECT * FROM events LIMIT {int(n)}")
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def lookup_player(conn, name: str, min_score: float = 85.0) -> dict | None:
    """Galat spelling wale naam ko registry se match karo."""
    rows = conn.execute("SELECT player_id, name, team FROM players").fetchall()
    names = {r[1]: (r[0], r[2]) for r in rows}
    match = process.extractOne(name, names.keys())
    if match and match[1] >= min_score:
        pid, team = names[match[0]]
        return {"player_id": pid, "name": match[0], "team": team, "score": round(match[1], 1)}
    return None


def value_stats(conn, column: str) -> dict | None:
    """Column ki min/max/nulls — impossible values pakadne ke liye."""
    cols = {c["column"] for c in get_schema(conn)}
    if column not in cols:
        return None
    r = conn.execute(
        f"SELECT min({column}), max({column}), count(*), count({column}) FROM events"
    ).fetchone()
    return {"column": column, "min": r[0], "max": r[1], "rows": r[2], "non_null": r[3]}
