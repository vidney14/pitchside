import json
from collections import Counter
from pathlib import Path

d = json.load(open(Path(__file__).parent / "match_3869685.json"))
events = d["events"]

print("total events:", len(events))
print("event types:", Counter(e["type"]["name"] for e in events).most_common(10))

# find one Pass and one Shot and print them fully
first_pass = next(e for e in events if e["type"]["name"] == "Pass")
first_shot = next(e for e in events if e["type"]["name"] == "Shot")
print(json.dumps(first_pass, indent=2))
print(json.dumps(first_shot, indent=2))