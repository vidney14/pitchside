import json
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
MATCH_ID = 3869685  # Argentina v France, 2022 World Cup final
OUT = Path(__file__).parent / f"match_{MATCH_ID}.json"

def fetch_json(path: str):
    url = f"{BASE}/{path}"
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def main():
    events = fetch_json(f"events/{MATCH_ID}.json")
    lineups = fetch_json(f"lineups/{MATCH_ID}.json")
    OUT.write_text(json.dumps({"events": events, "lineups": lineups}))
    print(f"saved {len(events)} events and {len(lineups)} team lineups to {OUT}")


if __name__ == "__main__":
    main()