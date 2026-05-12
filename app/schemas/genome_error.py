from pydantic import BaseModel
from .genome_properties import GenomeProperty

class GenomeError(BaseModel):    
    genome_property: GenomeProperty
    reason: str
    message: str
    error_type: str