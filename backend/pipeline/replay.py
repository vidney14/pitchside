import json
import time
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "match_3869685.json"

# Event types worth streaming. Ball Receipt*, Carry and Pressure are dropped:
# they are over half of all events and add nothing to the dashboard.
KEEP_TYPES = {
    "Pass", "Shot", "Dribble", "Duel", "Foul Committed", "Foul Won", "Interception",
    "Clearance", "Block", "Ball Recovery", "Goal Keeper", "Substitution", "Miscontrol",
    "Dispossessed", "Offside", "Half Start", "Half End", "Starting XI", "Own Goal For",
    "Own Goal Against", "Bad Behaviour", "Injury Stoppage", "Error", "50/50",
}


def load_raw_events():
    with open(DATA_FILE) as f:
        return json.load(f)["events"]


def get_outcome(raw: dict):
    type_name = raw["type"]["name"]
    block_key = type_name.lower().replace(" ", "_")   # "Foul Committed" -> "foul_committed"
    block = raw.get(block_key)
    if isinstance(block, dict) and "outcome" in block:
        return block["outcome"]["name"]
    if type_name == "Pass":
        return "Complete"       # StatsBomb only records an outcome when a pass fails
    return None


def flatten(raw: dict) -> dict:
    loc = raw.get("location") or [None, None]
    return {
        "event_id":   raw["id"],
        "idx":        raw["index"],
        "period":     raw["period"],
        "minute":     raw["minute"],
        "second":     raw["second"],
        "team":       raw["team"]["name"],
        "player_id":  (raw.get("player") or {}).get("id"),
        "event_type": raw["type"]["name"],
        "x":          loc[0],
        "y":          loc[1],
        "outcome":    get_outcome(raw),
    }


def match_events() -> list[dict]:
    """All events worth streaming, flattened, in match order."""
    return [flatten(e) for e in load_raw_events() if e["type"]["name"] in KEEP_TYPES]


def replay(events: list[dict], delay: float = 2.0):
    """Yield events one at a time with a pause, like a live feed.
    delay=0 replays instantly (for tests)."""
    for ev in events:
        yield ev
        if delay:
            time.sleep(delay)