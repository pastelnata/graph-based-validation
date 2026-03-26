from typing import Literal

from pydantic import BaseModel

PropertyType = Literal["STANDARD", "GENOME_PROPERTY"]

class GenomeProperty(BaseModel):
    property_type: PropertyType
    name: str
    value: str
    unit: str
    genome_type: str