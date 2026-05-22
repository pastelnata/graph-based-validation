"""Response schema for validation endpoint."""

from pydantic import BaseModel

from .genome_error import GenomeError

class ValidationResponse(BaseModel):
    """Response containing validation errors if any."""
    errors: list[GenomeError]
