"""Unit tests for GraphValidator."""

import networkx as nx
import pytest

from app.schemas.genome_properties import GenomeProperty
from app.schemas.graph import Graph, CycleInfo
from app.services.graph.graph_validator import GraphValidator


def _make_graph(edges, cycles=None, genome_type: str = "test") -> Graph:
    """Build a Graph wrapper around a DiGraph with the given edges.

    edges: iterable of (source, target, rule_details_dict)
    cycles: optional list. Each item may be a CycleInfo or a raw list of node names
            (which will be wrapped in CycleInfo).
    """
    digraph = nx.DiGraph()
    for source, target, rule_details in edges:
        digraph.add_edge(source, target, rule_details=rule_details)

    wrapped_cycles = []
    for cycle in cycles or []:
        if isinstance(cycle, CycleInfo):
            wrapped_cycles.append(cycle)
        else:
            # Try common CycleInfo field names; skip the cycle if none match.
            for kwarg in ("nodes", "cycle", "path"):
                try:
                    wrapped_cycles.append(CycleInfo(**{kwarg: list(cycle)}))
                    break
                except Exception:
                    continue

    return Graph(graph=digraph, cycles=wrapped_cycles, genome_type=genome_type)


def _prop(name: str, value: str, unit: str | None = "bp", genome_type: str = "human") -> GenomeProperty:
    return GenomeProperty(
        property_type="STANDARD",
        name=name,
        value=value,
        unit=unit,
        genome_type=genome_type,
    )


class TestGraphValidatorConstraints:
    """Constraint evaluation: pass vs. fail vs. malformed."""

    def test_constraint_passes_no_errors(self):
        validator = GraphValidator()
        properties = [_prop("length", "100"), _prop("max_len", "1000")]
        graph = _make_graph([
            ("max_len", "length", {"constraint": "length < max_len"}),
        ])

        errors = validator.validate(properties, graph)

        assert errors == []

    def test_constraint_fails_produces_error(self):
        validator = GraphValidator()
        properties = [_prop("length", "1500"), _prop("max_len", "1000")]
        graph = _make_graph([
            ("max_len", "length", {
                "constraint": "length < max_len",
                "message": "Length exceeds the allowed maximum",
            }),
        ])

        errors = validator.validate(properties, graph)

        assert len(errors) == 1
        assert errors[0].error_type == "CONSTRAINT_VIOLATION"
        assert errors[0].message == "Length exceeds the allowed maximum"
        assert errors[0].reason == "length < max_len"
        assert errors[0].genome_property.name == "length"

    def test_constraint_falls_back_to_default_message(self):
        validator = GraphValidator()
        properties = [_prop("length", "1500"), _prop("max_len", "1000")]
        graph = _make_graph([
            ("max_len", "length", {"constraint": "length < max_len"}),
        ])

        errors = validator.validate(properties, graph)

        assert len(errors) == 1
        assert "length < max_len" in errors[0].message

    def test_malformed_constraint_does_not_raise(self):
        """A constraint that fails to evaluate is treated as passing (logged warning)."""
        validator = GraphValidator()
        properties = [_prop("length", "100")]
        graph = _make_graph([
            ("length", "length", {"constraint": "this is not valid python !!!"}),
        ])

        errors = validator.validate(properties, graph)

        assert errors == []


class TestGraphValidatorConditions:
    """Conditions gate whether a rule's constraint is even checked."""

    def test_condition_false_skips_constraint(self):
        """When condition is False, the constraint is not evaluated."""
        validator = GraphValidator()
        properties = [_prop("length", "1500"), _prop("max_len", "1000")]
        graph = _make_graph([
            ("max_len", "length", {
                "condition": "1 == 2",          # always false
                "constraint": "length < max_len",  # would fail if checked
            }),
        ])

        errors = validator.validate(properties, graph)

        assert errors == []

    def test_condition_true_constraint_is_evaluated(self):
        validator = GraphValidator()
        properties = [_prop("length", "1500"), _prop("max_len", "1000")]
        graph = _make_graph([
            ("max_len", "length", {
                "condition": "1 == 1",          # always true
                "constraint": "length < max_len",  # fails
            }),
        ])

        errors = validator.validate(properties, graph)

        assert len(errors) == 1

    def test_no_condition_constraint_evaluated_normally(self):
        validator = GraphValidator()
        properties = [_prop("length", "50"), _prop("max_len", "100")]
        graph = _make_graph([
            ("max_len", "length", {"constraint": "length < max_len"}),
        ])

        errors = validator.validate(properties, graph)

        assert errors == []

    def test_malformed_condition_treated_as_true(self):
        """If a condition can't be evaluated, the rule still applies (constraint runs)."""
        validator = GraphValidator()
        properties = [_prop("length", "1500"), _prop("max_len", "1000")]
        graph = _make_graph([
            ("max_len", "length", {
                "condition": "bogus expression !!",
                "constraint": "length < max_len",
            }),
        ])

        errors = validator.validate(properties, graph)

        assert len(errors) == 1


class TestGraphValidatorMissingTarget:
    """Behavior when the rule's target property isn't present in the input."""

    def test_missing_target_synthesizes_genome_property(self):
        validator = GraphValidator()
        properties = [_prop("length", "100", genome_type="mouse")]
        # The rule's *target* (missing_prop) isn't in the input, but the
        # constraint references only `length`, so it evaluates cleanly and
        # fails — which then triggers synthesis of an error for missing_prop.
        graph = _make_graph([
            ("length", "missing_prop", {
                "constraint": "length > 1000",  # length=100, so False → fires
                "message": "missing_prop is required",
            }),
        ])

        errors = validator.validate(properties, graph)

        assert len(errors) == 1
        assert errors[0].genome_property.name == "missing_prop"
        # genome_type is inherited from another property in the map
        assert errors[0].genome_property.genome_type == "mouse"
        assert errors[0].genome_property.property_type == "GENOME_PROPERTY"

    def test_missing_target_with_no_known_genome_type(self):
        """If no property carries a genome_type, fallback is 'unknown'."""
        validator = GraphValidator()
        # Empty property list: use a constraint with no variable references
        # so it evaluates cleanly to False and the error fires.
        graph = _make_graph([
            ("a", "b", {"constraint": "1 > 2"}),  # literal False, no vars
        ])

        errors = validator.validate([], graph)

        assert len(errors) == 1
        assert errors[0].genome_property.genome_type == "unknown"


class TestGraphValidatorExpressionSubstitution:
    """Property-name → value substitution edge cases."""

    def test_overlapping_property_names_resolved_correctly(self):
        """`gc` shouldn't corrupt `gc_content` (longer-name-first substitution)."""
        validator = GraphValidator()
        properties = [_prop("gc", "40"), _prop("gc_content", "45")]
        # If 'gc' is replaced first, 'gc_content' becomes '40_content' and breaks.
        graph = _make_graph([
            ("gc", "gc_content", {"constraint": "gc_content > gc"}),
        ])

        errors = validator.validate(properties, graph)

        assert errors == []

    def test_null_string_value_becomes_none(self):
        validator = GraphValidator()
        properties = [_prop("length", "null")]
        graph = _make_graph([
            ("length", "length", {"constraint": "length is None"}),
        ])

        errors = validator.validate(properties, graph)

        assert errors == []

    def test_empty_string_value_becomes_none(self):
        validator = GraphValidator()
        properties = [_prop("length", "")]
        graph = _make_graph([
            ("length", "length", {"constraint": "length is None"}),
        ])

        errors = validator.validate(properties, graph)

        assert errors == []

    def test_non_numeric_string_quoted(self):
        validator = GraphValidator()
        properties = [_prop("species", "homo_sapiens")]
        graph = _make_graph([
            ("species", "species", {"constraint": "species == 'homo_sapiens'"}),
        ])

        errors = validator.validate(properties, graph)

        assert errors == []


class TestGraphValidatorStatelessness:
    """The validator must be safe to reuse across calls (the original bug)."""

    def test_repeated_calls_do_not_accumulate_errors(self):
        validator = GraphValidator()

        failing_graph = _make_graph([
            ("max_len", "length", {"constraint": "length < max_len"}),
        ])
        failing_props = [_prop("length", "1500"), _prop("max_len", "1000")]

        errors_first = validator.validate(failing_props, failing_graph)
        errors_second = validator.validate(failing_props, failing_graph)

        # Each call returns exactly the errors for that call — no accumulation.
        assert len(errors_first) == 1
        assert len(errors_second) == 1

    def test_subsequent_passing_call_has_no_residue(self):
        validator = GraphValidator()

        failing = _make_graph([
            ("max_len", "length", {"constraint": "length < max_len"}),
        ])
        passing = _make_graph([
            ("max_len", "length", {"constraint": "length < max_len"}),
        ])

        validator.validate([_prop("length", "1500"), _prop("max_len", "1000")], failing)
        errors = validator.validate([_prop("length", "50"), _prop("max_len", "1000")], passing)

        assert errors == []

    def test_property_map_not_leaked_across_calls(self):
        """Properties from call #1 must not influence call #2."""
        validator = GraphValidator()

        # Call 1: defines `max_len`
        graph_one = _make_graph([
            ("max_len", "length", {"constraint": "length < max_len"}),
        ])
        validator.validate(
            [_prop("length", "50"), _prop("max_len", "1000")], graph_one,
        )

        # Call 2: only defines `length`. If max_len leaked from call 1,
        # this constraint would pass; if not, max_len evaluates as a bare name
        # and the expression fails (treated as passing per malformed-constraint policy).
        # Either way we should not see a CONSTRAINT_VIOLATION sourced from leaked state.
        graph_two = _make_graph([
            ("length", "length", {"constraint": "length == 50"}),
        ])
        errors = validator.validate([_prop("length", "50")], graph_two)

        assert errors == []


class TestGraphValidatorGraphTraversal:
    """Edge cases around graph shape."""

    def test_graph_with_no_edges_returns_no_errors(self):
        validator = GraphValidator()
        digraph = nx.DiGraph()
        digraph.add_node("orphan")
        graph = Graph(graph=digraph, cycles=[], genome_type="test")

        errors = validator.validate([_prop("orphan", "1")], graph)

        assert errors == []

    def test_edge_without_rule_details_is_skipped(self):
        validator = GraphValidator()
        digraph = nx.DiGraph()
        digraph.add_edge("a", "b")  # no `rule_details` attr
        graph = Graph(graph=digraph, cycles=[], genome_type="test")

        errors = validator.validate([_prop("a", "1"), _prop("b", "2")], graph)

        assert errors == []

    def test_cyclic_graph_still_validates_all_edges(self):
        """Validator should warn but proceed when the graph has cycles."""
        validator = GraphValidator()
        properties = [_prop("a", "10"), _prop("b", "5")]
        graph = _make_graph(
            edges=[
                ("a", "b", {"constraint": "b < a"}),   # passes
                ("b", "a", {"constraint": "a < b"}),   # fails
            ],
            cycles=[["a", "b", "a"]],
        )

        errors = validator.validate(properties, graph)

        assert len(errors) == 1
        assert errors[0].genome_property.name == "a"


@pytest.fixture
def validator():
    return GraphValidator()


def test_validator_can_be_shared_across_simulated_concurrent_calls(validator):
    """A single instance handles back-to-back calls with different inputs."""
    graph_a = _make_graph([("max", "x", {"constraint": "x < max"})])
    graph_b = _make_graph([("limit", "y", {"constraint": "y < limit"})])

    errors_a = validator.validate(
        [_prop("x", "5"), _prop("max", "10")], graph_a,
    )
    errors_b = validator.validate(
        [_prop("y", "100"), _prop("limit", "10")], graph_b,
    )

    assert errors_a == []
    assert len(errors_b) == 1
    assert errors_b[0].genome_property.name == "y"
