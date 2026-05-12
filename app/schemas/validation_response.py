from pydantic import BaseModel

from .genome_error import GenomeError

class ValidationResponse(BaseModel):
    errors: list[GenomeError]