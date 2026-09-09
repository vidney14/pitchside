import re

ALTER_PATTERN = re.compile(
    r"^\s*ALTER\s+TABLE\s+events\s+ADD\s+COLUMN\s+(\w+)\s+(FLOAT|INTEGER|VARCHAR|BOOLEAN|DOUBLE)"
    r"(\s+CHECK\s*\([^;]+\))?\s*;?\s*$",
    re.IGNORECASE,
)

MIN_CONFIDENCE = 0.8


def check(proposal, conn, triage_result) -> tuple[bool, str]:
    """Return (allowed, reason). Nothing reaches the database without passing this."""

    if proposal.action == "escalate":
        return False, "agent chose to escalate"

    if proposal.confidence < MIN_CONFIDENCE:
        return False, f"confidence {proposal.confidence} below {MIN_CONFIDENCE}"

    if triage_result.suspicious_value and proposal.action == "alter_table":
        return False, "suspicious value must not become a new column"

    if proposal.action == "alter_table":
        if not proposal.sql:
            return False, "alter_table with no SQL"
        if not ALTER_PATTERN.match(proposal.sql):
            return False, f"SQL not allowlisted: {proposal.sql}"
        try:
            conn.execute("BEGIN")
            conn.execute(proposal.sql)
            conn.execute("ROLLBACK")
        except Exception as exc:
            conn.execute("ROLLBACK")
            return False, f"dry-run failed: {exc}"

    if proposal.action == "transform_payload":
        if not proposal.payload_patch:
            return False, "transform_payload with no patch"

    return True, "allowlisted, dry-run ok"