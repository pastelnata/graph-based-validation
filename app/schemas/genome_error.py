"""Genome error schema for validation failures."""

from pydantic import BaseModel
from .genome_properties import GenomeProperty

class GenomeError(BaseModel):
    """Represents a validation error for a genome property."""
    genome_property: GenomeProperty
    reason: str
    message: str
    error_type: str
