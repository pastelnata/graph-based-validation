"""Rule schema definitions for validation rules."""

from __future__ import annotations

from pydantic import BaseModel, Field

class RuleDetails(BaseModel):
    """Details of a validation rule including constraint and condition."""
    constraint: str = Field(...)
    condition: str | None = Field(
        default=None
    )
    message: str | None = Field(
        default=None,
        max_length=500
    )

class Rule(BaseModel):
    """Represents a single validation rule with source and target properties."""
    source: str = Field(...)
    target: str = Field(...)
    rule_details: RuleDetails = Field(...)
