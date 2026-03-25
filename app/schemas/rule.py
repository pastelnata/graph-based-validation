from pydantic import BaseModel

class Rule(BaseModel):
    inputs: list[str]
    expression: str