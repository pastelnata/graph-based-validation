from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class Rule(BaseModel):
    """
    Represents a cross-field validation rule.
    """
    
    source: str = Field(...)
    target: str = Field(...)
    constraint: str = Field(...)
    condition: str | None = Field(
        default=None
    )
    message: str | None = Field(
        default=None,
        max_length=500
    )