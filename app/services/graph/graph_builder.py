import networkx as nx

from app.schemas.graph import (
    CycleInfo,
    Graph,
)
from app.schemas.rule import Rule


class GraphBuilder:
    """
    Builds a directed graph from a list of Rule objects.
    """

    def build_graph(self, rules: list[Rule], genome_type: str) -> Graph:
        graph = nx.DiGraph()

        nodes = self.create_nodes(rules)
        edges = [
            (rule.source, rule.target, {"rule_details": rule.rule_details.model_dump()})
            for rule in rules
        ]
        
        graph.add_nodes_from(nodes)
        graph.add_edges_from(edges)

        cycles = self.detect_cycles(graph, rules)

        return Graph(
            genome_type=genome_type,
            graph=graph,
            cycles=cycles
        )

    def create_nodes(self, rules: list[Rule]) -> list[str]:
        attribute_names = set()
        for rule in rules:
            attribute_names.add(rule.source)
            attribute_names.add(rule.target)
        return sorted(attribute_names)

    def detect_cycles(self, graph: nx.DiGraph, rules: list[Rule]) -> list[CycleInfo]:
        try:
            all_cycles = list(nx.recursive_simple_cycles(graph))
            return [
                CycleInfo(
                    cycle=cycle,
                    rules_involved=self.find_rules_for_cycle(cycle, rules),
                )
                for cycle in all_cycles
            ]
        except nx.NetworkXError:
            return []

    def find_rules_for_cycle(self, cycle: list[str], rules: list[Rule]) -> list[Rule]:
        cycle_rules = []
        for i in range(len(cycle)):
            source = cycle[i]
            target = cycle[(i + 1) % len(cycle)]
            for rule in rules:
                if rule.source == source and rule.target == target:
                    cycle_rules.append(rule)
        return cycle_rules