"""Deterministic rules learned from repeated agent heals.

Once the same failure has been healed the same way several times, the
fix is no longer a judgement call -- it's a known recipe. Promoting it
into the `rules` table lets ingest.py apply it directly, skipping the
LLM round-trip entirely.

Usage (promote from history):
    python -m pipeline.rules promote
    python -m pipeline.rules promote --min-hits 5
    python -m pipeline.rules list
"""
import argparse
import json
import re

from pipeline import db


def error_signature(error: str) -> str:
    """Collapse the specific offending value out of an error message so
    repeats of the same failure produce the same pattern.
    e.g. 'player_id 999999 not in player registry' -> 'player_id \\d+ not in player registry'
    """
    return re.sub(r"\d+", r"\\d+", re.escape(error))


def find_rule(conn, error: str, payload: dict) -> dict | None:
    """Return the first enabled rule matching this error + payload, else None."""
    rows = conn.execute(
        "SELECT id, failure_class, error_pattern, payload_pattern, action, sql, payload_patch "
        "FROM rules WHERE enabled = true ORDER BY hits DESC, id ASC"
    ).fetchall()
    for rid, failure_class, error_pattern, payload_pattern_json, action, sql, payload_patch_json in rows:
        try:
            if not re.search(error_pattern, error):
                continue
        except re.error:
            continue
        pattern = json.loads(payload_pattern_json) if payload_pattern_json else {}
        if all(payload.get(k) == v for k, v in pattern.items()):
            return {
                "id": rid,
                "failure_class": failure_class,
                "action": action,
                "sql": sql,
                "payload_patch": json.loads(payload_patch_json) if payload_patch_json else None,
            }
    return None


def record_hit(conn, rule_id: int) -> None:
    conn.execute("UPDATE rules SET hits = hits + 1 WHERE id = ?", [rule_id])


def apply_rule(conn, rule: dict, payload: dict) -> dict:
    """Apply a matched rule the same way heal() applies a fresh proposal.
    Returns {"healed": bool, "payload": dict | None}."""
    action = rule["action"]
    if action == "alter_table":
        conn.execute(rule["sql"])
        return {"healed": True, "payload": payload}
    if action == "transform_payload":
        out = dict(payload)
        for key, value in (rule["payload_patch"] or {}).items():
            if value is None:
                out.pop(key, None)
            else:
                out[key] = value
        return {"healed": True, "payload": out}
    if action == "skip_record":
        return {"healed": True, "payload": None}
    return {"healed": False, "payload": None}


def promote_rule(conn, *, failure_class: str, error_pattern: str, action: str,
                  sql: str | None = None, payload_patch: dict | None = None,
                  payload_pattern: dict | None = None, created_from_audit: int | None = None) -> int:
    """Insert a new rule. Returns its id."""
    conn.execute(
        "INSERT INTO rules (failure_class, error_pattern, payload_pattern, action, sql, "
        "payload_patch, created_from_audit) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            failure_class, error_pattern,
            json.dumps(payload_pattern) if payload_pattern else None,
            action, sql,
            json.dumps(payload_patch) if payload_patch else None,
            created_from_audit,
        ],
    )
    return conn.execute("SELECT currval('rule_seq')").fetchone()[0]


def promotion_candidates(conn, min_hits: int = 3) -> list[dict]:
    """Group successful HEALED audit_log entries by (failure_class, error_signature,
    action) and return groups that have reached min_hits and have no existing
    enabled rule with the same signature yet."""
    rows = conn.execute(
        "SELECT id, detail FROM audit_log WHERE stage = 'HEALED' ORDER BY id"
    ).fetchall()
    existing = {
        r[0] for r in conn.execute("SELECT error_pattern FROM rules WHERE enabled = true").fetchall()
    }

    groups: dict[tuple, list] = {}
    for audit_id, detail_json in rows:
        d = json.loads(detail_json)
        sig = d.get("error_signature")
        action = d.get("action")
        failure_class = d.get("failure_class")
        if not sig or not action:
            continue
        groups.setdefault((failure_class, sig, action), []).append((audit_id, d))

    out = []
    for (failure_class, sig, action), entries in groups.items():
        if len(entries) < min_hits or sig in existing:
            continue
        last_id, last_detail = entries[-1]
        out.append({
            "failure_class": failure_class,
            "error_pattern": sig,
            "action": action,
            "count": len(entries),
            "created_from_audit": last_id,
            "sql": last_detail.get("sql"),
            "payload_patch": last_detail.get("payload_patch"),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("promote", help="scan audit_log and promote repeated heals into rules")
    p.add_argument("--min-hits", type=int, default=3)
    p.add_argument("--db", default=None)

    p = sub.add_parser("list", help="show current rules")
    p.add_argument("--db", default=None)

    args = ap.parse_args()
    conn = db.connect(args.db)

    if args.cmd == "promote":
        candidates = promotion_candidates(conn, args.min_hits)
        if not candidates:
            print("no promotion candidates")
            return
        for c in candidates:
            rid = promote_rule(
                conn,
                failure_class=c["failure_class"],
                error_pattern=c["error_pattern"],
                action=c["action"],
                sql=c["sql"],
                payload_patch=c["payload_patch"],
                created_from_audit=c["created_from_audit"],
            )
            print(f"promoted rule {rid}: {c['failure_class']} / {c['action']} "
                  f"(seen {c['count']}x) pattern={c['error_pattern']!r}")

    elif args.cmd == "list":
        rows = conn.execute(
            "SELECT id, failure_class, error_pattern, action, hits, enabled FROM rules ORDER BY id"
        ).fetchall()
        if not rows:
            print("no rules yet")
        for rid, fc, pattern, action, hits, enabled in rows:
            flag = "on " if enabled else "off"
            print(f"[{flag}] rule {rid:>3} | {fc:<12} | {action:<17} | hits={hits:<3} | {pattern}")


if __name__ == "__main__":
    main()
