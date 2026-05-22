"""Graph schema for validation rule graphs."""

from __future__ import annotations

import networkx as nx
from pydantic import BaseModel, Field

from app.schemas.rule import Rule


class CycleInfo(BaseModel):
    """Information about a cycle detected in the rule graph."""
    cycle: list[str]
    rules_involved: list[Rule]


class Graph(BaseModel):
    """Represents a directed graph of validation rules."""
    model_config = {"arbitrary_types_allowed": True}

    genome_type: str = Field(...)
    graph: nx.DiGraph
    cycles: list[CycleInfo] = Field(default_factory=list)
