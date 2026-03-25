from pydantic import BaseModel

from .genome_properties import GenomeProperty

class ValidationRequest(BaseModel):
    properties: list[GenomeProperty]