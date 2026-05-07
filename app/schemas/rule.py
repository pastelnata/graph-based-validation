from __future__ import annotations

from pydantic import BaseModel, Field

class Rule(BaseModel):
    source: str = Field(...)
    target: str = Field(...)
    rule_details: RuleDetails = Field(...)

class RuleDetails(BaseModel):
    constraint: str = Field(...)
    condition: str | None = Field(
        default=None
    )
    message: str | None = Field(
        default=None,
        max_length=500
    )