"""Graph schema for validation rule graphs."""

from __future__ import annotations
from typing import Any

import networkx as nx
from pydantic import BaseModel, Field, field_validator

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

    @field_validator("graph", mode="before")
    @classmethod
    def parse_graph(cls, value: Any) -> nx.DiGraph:
        if isinstance(value, dict):
            return nx.node_link_graph(value, directed=True)
        return value
