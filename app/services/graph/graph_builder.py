import json
import logging
from pathlib import Path
from typing import Optional

import networkx as nx

from app.schemas.graph import (
    CycleInfo,
    Graph,
)
from app.schemas.rule import Rule

logger = logging.getLogger(__name__)


class GraphBuilderError(Exception):
    """Base exception for graph builder errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class GraphSaveError(GraphBuilderError):
    """Raised when saving a graph fails."""

class GraphLoadError(GraphBuilderError):
    """Raised when loading a graph fails."""

class GraphBuildError(GraphBuilderError):
    """Raised when building a graph fails."""

class GraphBuilder:
    """
    Builds a directed graph from a list of Rule objects.
    """

    GRAPH_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "resources" / "graphs"


    def build_graph(self, rules: list[Rule], genome_type: str) -> Graph:
        try:
            graph = nx.DiGraph()

            nodes = self.create_nodes(rules)
            edges = [
                (rule.source, rule.target, {"rule_details": rule.rule_details.model_dump()})
                for rule in rules
            ]
            
            graph.add_nodes_from(nodes)
            graph.add_edges_from(edges)

            cycles = self.detect_cycles(graph, rules)

            graph = Graph(
                genome_type=genome_type,
                graph=graph,
                cycles=cycles
            )
            self.save_graph(graph)
            return graph
        except Exception as error:
            error_msg = f"Failed to build graph: {str(error)}"
            logger.error(error_msg, exc_info=True)
            raise GraphBuildError(error_msg, original_error=error) from error


    def create_nodes(self, rules: list[Rule]) -> list[str]:
        attribute_names = set()
        for rule in rules:
            attribute_names.add(rule.source)
            attribute_names.add(rule.target)
        return sorted(attribute_names)


    def detect_cycles(self, graph: nx.DiGraph, rules: list[Rule]) -> list[CycleInfo]:
        all_cycles = list(nx.recursive_simple_cycles(graph))
        return [
            CycleInfo(
                cycle=cycle,
                rules_involved=self.find_rules_for_cycle(cycle, rules),
            )
            for cycle in all_cycles
        ]


    def find_rules_for_cycle(self, cycle: list[str], rules: list[Rule]) -> list[Rule]:
        cycle_rules = []
        for i in range(len(cycle)):
            source = cycle[i]
            target = cycle[(i + 1) % len(cycle)]
            for rule in rules:
                if rule.source == source and rule.target == target:
                    cycle_rules.append(rule)
        return cycle_rules


    def save_graph(self, graph: Graph):
        try:
            graph_json = {
                "genome_type": graph.genome_type,
                "graph": nx.node_link_data(graph.graph),
                "cycles": [cycle.model_dump(mode="json") for cycle in graph.cycles],
            }

            self.GRAPH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            output_path = self.GRAPH_OUTPUT_DIR / f"{graph.genome_type}.json"
            output_path.write_text(json.dumps(graph_json, indent=2), encoding="utf-8")

            logger.info("Graph saved to %s", output_path)
        except Exception as error:
            error_msg = f"Failed to save graph: {str(error)}"
            logger.error(error_msg, exc_info=True)
            raise GraphSaveError(error_msg, original_error=error) from error
    

    def load_graph(self, genome_type: str) -> Optional[Graph]:
        input_path = self.GRAPH_OUTPUT_DIR / f"{genome_type}.json"

        if not input_path.exists():
            logger.warning("Graph file not found for genome_type=%s", genome_type)
            return None

        try:
            graph_data = json.loads(input_path.read_text(encoding="utf-8"))

            graph_data["graph"] = nx.node_link_graph(graph_data["graph"])
            loaded_graph = Graph.model_validate(graph_data)

            return loaded_graph
        except Exception as error:
            error_msg = f"Failed to load graph for genome_type={genome_type}: {str(error)}"
            logger.error(error_msg, exc_info=True)
            raise GraphLoadError(error_msg, original_error=error) from error