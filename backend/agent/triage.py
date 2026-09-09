import json

from agent.llm import structured
from agent.schemas import Triage

SYSTEM = """You are the first responder for a football (soccer) event data pipeline.
An insert into the `events` table just failed. Classify the failure.

Domain knowledge:
- Event fields come from a live match feed. New fields can appear when the provider updates.
- xG (expected goals) is a probability between 0 and 1.
- Minute is a non-negative integer; second is 0-59; period is 1-5.
- Player names and ids come from a lineup registry; misspellings happen.

Be sceptical. A value that is impossible (out of range, wrong sign, nonsense) is a data
problem, not a schema problem, even if the error message looks like a missing column.
Set suspicious_value=true in that case and lower your confidence.

Do not classify from the error message alone. Compare the payload keys to the schema:
if a payload key is missing and a similar-looking new key is present (e.g. player_id
gone, player_name present), the feed has substituted or renamed a field. That is a data
or referential problem, not schema drift. Schema drift is only when a genuinely new
measurement appears alongside all the expected fields."""


def triage(case: dict, provider: str = "groq") -> Triage:
    user = (
        f"ERROR:\n{case['error']}\n\n"
        f"FAILING PAYLOAD:\n{json.dumps(case['payload'], default=str)}\n\n"
        f"CURRENT TABLE SCHEMA (column, type):\n{json.dumps(case['schema'])}"
    )
    return structured(provider, Triage, [("system", SYSTEM), ("user", user)])