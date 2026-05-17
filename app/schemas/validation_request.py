"""Request schema for validation endpoint."""

from pydantic import BaseModel

from .genome_properties import GenomeProperty

class ValidationRequest(BaseModel):
    """Request containing properties to validate against rules."""
    properties: list[GenomeProperty]
