from typing import Literal

from pydantic import BaseModel, Field


class Triage(BaseModel):
    """First look at a failure: what kind is it, and do we need to dig deeper?"""

    failure_class: Literal[
        "schema_drift",    # feed sent a field/shape the table doesn't know
        "data_quality",    # a value is the wrong type, misspelled, or impossible
        "referential",     # refers to a player/team we don't have
        "duplicate",       # we've seen this event before
        "ordering",        # events arriving out of sequence
        "unknown",
    ]
    summary: str = Field(description="One sentence: what went wrong, in plain English.")
    suspicious_value: bool = Field(
        description="True if a value in the payload looks impossible or corrupt, not just unfamiliar."
    )
    needs_investigation: bool = Field(
        description="True if the agent should inspect the database before proposing a fix."
    )
    confidence: float = Field(ge=0, le=1)