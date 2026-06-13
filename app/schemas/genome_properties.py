"""Genome property schema definition."""

from typing import Literal, Optional

from pydantic import BaseModel

PropertyType = Literal["STANDARD", "GENOME_PROPERTY"]

class GenomeProperty(BaseModel):
    """Represents a single genome property with its metadata."""
    property_type: PropertyType
    name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    genome_type: Optional[str] = None
