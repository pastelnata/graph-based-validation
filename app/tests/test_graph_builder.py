"""Tests for the GraphBuilder service."""
from app.schemas.rule import Rule
from app.services.graph.graph_builder import GraphBuilder


class TestGraphBuilderBasicConstruction:
    """Test basic graph construction from rules."""

    def test_empty_rules_list(self):
        """Test graph construction with no rules."""
        builder = GraphBuilder()
        graph = builder.build_graph([], genome_type="test_genome")

        assert list(graph.graph.nodes()) == []
        assert len(list(graph.graph.edges())) == 0
        assert graph.cycles == []

    def test_single_rule(self):
        """Test graph construction with a single rule."""
        rule = Rule(
            source="fieldA",
            target="fieldB",
            rule_details={"constraint": "fieldB == 5"},
        )

        builder = GraphBuilder()
        graph = builder.build_graph([rule], genome_type="test_genome")

        assert len(list(graph.graph.nodes())) == 2
        assert set(graph.graph.nodes()) == {"fieldA", "fieldB"}

        edges = list(graph.graph.edges(data=True))
        assert len(edges) == 1
        source, target, data = edges[0]
        assert source == "fieldA"
        assert target == "fieldB"
        assert data["rule_details"]["constraint"] == "fieldB == 5"

    def test_multiple_independent_rules(self):
        """Test graph with multiple independent rules."""
        rules = [
            Rule(
                source="a",
                target="b",
                rule_details={"constraint": "b == 1"},
            ),
            Rule(
                source="c",
                target="d",
                rule_details={"constraint": "d == 2"},
            ),
        ]

        builder = GraphBuilder()
        graph = builder.build_graph(rules, genome_type="test_genome")

        assert len(list(graph.graph.nodes())) == 4
        assert set(graph.graph.nodes()) == {"a", "b", "c", "d"}

        assert len(list(graph.graph.edges())) == 2
        assert graph.cycles == []

    def test_nodes_sorted_alphabetically(self):
        """Test that nodes are sorted for consistent ordering."""
        rules = [
            Rule(
                source="z",
                target="a",
                rule_details={"constraint": "a == 1"},
            ),
            Rule(
                source="m",
                target="x",
                rule_details={"constraint": "x == 2"},
            ),
        ]

        builder = GraphBuilder()
        graph = builder.build_graph(rules, genome_type="test_genome")

        node_names = sorted(graph.graph.nodes())
        assert list(graph.graph.nodes()) == node_names

    def test_rule_with_condition(self):
        """Test that rule conditions are preserved in edges."""
        rule = Rule(
            source="fieldA",
            target="fieldB",
            rule_details={"constraint": "fieldB > 10", "condition": "fieldA == 'active'"},
        )

        builder = GraphBuilder()
        graph = builder.build_graph([rule], genome_type="test_genome")

        edges = list(graph.graph.edges(data=True))
        source, target, data = edges[0]
        assert data["rule_details"]["condition"] == "fieldA == 'active'"

    def test_rule_with_message(self):
        """Test that rule messages are preserved in edges."""
        rule = Rule(
            source="fieldA",
            target="fieldB",
            rule_details={
                "constraint": "fieldB > 10",
                "message": "fieldB must be greater than 10"
            },
        )

        builder = GraphBuilder()
        graph = builder.build_graph([rule], genome_type="test_genome")

        edges = list(graph.graph.edges(data=True))
        source, target, data = edges[0]
        assert data["rule_details"]["message"] == "fieldB must be greater than 10"

    def test_rule_with_all_fields(self):
        """Test that all rule detail fields are preserved."""
        rule = Rule(
            source="fieldA",
            target="fieldB",
            rule_details={
                "constraint": "fieldB > 10",
                "condition": "fieldA == 'active'",
                "message": "Validation failed"
            },
        )

        builder = GraphBuilder()
        graph = builder.build_graph([rule], genome_type="test_genome")

        edges = list(graph.graph.edges(data=True))
        source, target, data = edges[0]
        rule_details = data["rule_details"]
        assert rule_details["constraint"] == "fieldB > 10"
        assert rule_details["condition"] == "fieldA == 'active'"
        assert rule_details["message"] == "Validation failed"


class TestGraphBuilderCycleDetection:
    """Test cycle detection in graphs."""

    def test_no_cycles(self):
        """Test graph with no cycles (DAG)."""
        rules = [
            Rule(
                source="a",
                target="b",
                rule_details={"constraint": "b == 1"},
            ),
            Rule(
                source="b",
                target="c",
                rule_details={"constraint": "c == 2"},
            ),
        ]

        builder = GraphBuilder()
        graph = builder.build_graph(rules, genome_type="test_genome")

        assert graph.cycles == []

    def test_simple_cycle_a_b_a(self):
        """Test detection of simple 2-node cycle: a→b→a."""
        rules = [
            Rule(
                source="a",
                target="b",
                rule_details={"constraint": "b == 1"},
            ),
            Rule(
                source="b",
                target="a",
                rule_details={"constraint": "a == 2"},
            ),
        ]

        builder = GraphBuilder()
        graph = builder.build_graph(rules, genome_type="test_genome")

        assert len(graph.cycles) == 1

        cycle = graph.cycles[0]
        assert set(cycle.cycle) == {"a", "b"}
        assert len(cycle.rules_involved) == 2

    def test_simple_cycle_a_b_c_a(self):
        """Test detection of 3-node cycle: a→b→c→a."""
        rules = [
            Rule(
                source="a",
                target="b",
                rule_details={"constraint": "b == 1"},
            ),
            Rule(
                source="b",
                target="c",
                rule_details={"constraint": "c == 2"},
            ),
            Rule(
                source="c",
                target="a",
                rule_details={"constraint": "a == 3"},
            ),
        ]

        builder = GraphBuilder()
        graph = builder.build_graph(rules, genome_type="test_genome")

        assert len(graph.cycles) == 1

        cycle = graph.cycles[0]
        assert set(cycle.cycle) == {"a", "b", "c"}
        assert len(cycle.rules_involved) == 3

    def test_multiple_cycles(self):
        """Test detection of multiple independent cycles."""
        rules = [
            # Cycle 1: a ↔ b
            Rule(
                source="a",
                target="b",
                rule_details={"constraint": "b == 1"},
            ),
            Rule(
                source="b",
                target="a",
                rule_details={"constraint": "a == 2"},
            ),
            # Cycle 2: c ↔ d
            Rule(
                source="c",
                target="d",
                rule_details={"constraint": "d == 3"},
            ),
            Rule(
                source="d",
                target="c",
                rule_details={"constraint": "c == 4"},
            ),
        ]

        builder = GraphBuilder()
        graph = builder.build_graph(rules, genome_type="test_genome")

        assert len(graph.cycles) == 2

        cycle_sets = [set(cycle.cycle) for cycle in graph.cycles]
        assert {"a", "b"} in cycle_sets
        assert {"c", "d"} in cycle_sets

    def test_cycle_with_self_loop(self):
        """Test detection of self-loop (a→a)."""
        rule = Rule(
            source="a",
            target="a",
            rule_details={"constraint": "a == 1"},
        )

        builder = GraphBuilder()
        graph = builder.build_graph([rule], genome_type="test_genome")

        assert len(graph.cycles) == 1

        cycle = graph.cycles[0]
        assert cycle.cycle == ["a"]



class TestGraphEdgeCases:
    """Test edge cases and special scenarios."""

    def test_attributes_with_special_characters(self):
        """Test that attributes with special characters are handled."""
        rule = Rule(
            source="field_A",
            target="field-B",
            rule_details={"constraint": "field-B == 1"},
        )

        builder = GraphBuilder()
        graph = builder.build_graph([rule], genome_type="test_genome")

        assert len(list(graph.graph.nodes())) == 2
        node_names = set(graph.graph.nodes())
        assert "field_A" in node_names
        assert "field-B" in node_names



    def test_duplicate_rules(self):
        """Test graph with duplicate rules."""
        rule = Rule(
            source="a",
            target="b",
            rule_details={"constraint": "b == 1"},
        )

        builder = GraphBuilder()
        graph = builder.build_graph([rule, rule], genome_type="test_genome")

        # Should have 2 edges even though they're identical
        # Note: networkX DiGraph doesn't support multiple edges, so this will be 1 edge
        assert len(list(graph.graph.edges())) == 1
        assert len(list(graph.graph.nodes())) == 2
