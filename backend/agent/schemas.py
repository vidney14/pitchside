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

class ToolCall(BaseModel):
    """Agent ka decision: konsa tool, kis input ke saath."""
    tool: Literal["get_schema", "sample_rows", "lookup_player", "value_stats", "done"]
    argument: str = Field(default="", description="Player name for lookup_player, column name for value_stats, else empty.")
    why: str = Field(description="One line: why this tool now.")

class FixProposal(BaseModel):
    """The agent's proposed fix. This is a contract, not a suggestion."""

    action: Literal[
        "alter_table",       # add a new nullable column
        "transform_payload", # change values in the payload
        "skip_record",       # duplicate, safe to ignore
        "escalate",          # don't guess — ask a human
    ]
    diagnosis: str = Field(description="One sentence: what actually went wrong.")
    sql: str | None = Field(default=None, description="Only for alter_table. Must be ALTER TABLE events ADD COLUMN ...")
    payload_patch: dict | None = Field(default=None, description="Only for transform_payload. Keys to set or remove.")
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(description="Why this fix is safe.")