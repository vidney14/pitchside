import json
from pathlib import Path
from pipeline import db

d = json.load(open(Path(__file__).parent / "match_3869685.json"))
conn = db.connect(":memory:")
n = db.load_players(conn, d["lineups"])
print("loaded", n, "players")
print(conn.execute("SELECT team, count(*) FROM players GROUP BY team").fetchall())
