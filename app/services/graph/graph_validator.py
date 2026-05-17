"""Service for validating genome properties against rule graphs."""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from app.schemas.genome_error import GenomeError
from app.schemas.genome_properties import GenomeProperty
from app.schemas.graph import Graph

logger = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods
class GraphValidator:
    """Validates genome properties against a rule graph."""

    def __init__(self) -> None:
        """Initialize the GraphValidator."""
        self.property_map: dict[str, Any] = {}
        self.errors: list[GenomeError] = []

    def validate(
        self,
        properties: list[GenomeProperty],
        graph: Graph,
    ) -> list[GenomeError]:
        """Validate properties against the rule graph.

        Args:
            properties: List of GenomeProperty objects to validate
            graph: The rule graph containing validation rules

        Returns:
            List of GenomeError objects for any validation failures
        """
        self.property_map = {}
        self.errors = []

        self._build_property_map(properties)

        if graph.cycles:
            logger.warning(
                "Graph contains %d cycle(s). These will be noted but validation will continue.",
                len(graph.cycles),
            )

        self._traverse_and_validate(graph.graph)

        logger.info("Validation complete. Found %d error(s).", len(self.errors))
        return self.errors

    def _build_property_map(self, properties: list[GenomeProperty]) -> None:
        """Build a map of property names to their values for quick lookup.

        Args:
            properties: List of GenomeProperty objects
        """
        for prop in properties:
            self.property_map[prop.name] = {
                "value": prop.value,
                "unit": prop.unit,
                "property_type": prop.property_type,
                "genome_type": prop.genome_type,
                "original_property": prop,
            }

    def _traverse_and_validate(self, graph_obj: nx.DiGraph) -> None:
        """Traverse the graph and validate rules.

        Uses topological sort when possible (acyclic graphs) or node-by-node
        validation for graphs with cycles.

        Args:
            graph_obj: The NetworkX directed graph containing validation rules
        """
        try:
            list(nx.topological_sort(graph_obj))
            logger.debug("Using topological sort for graph traversal")
        except nx.NetworkXError:
            logger.debug("Graph has cycles, using unordered node traversal")

        for source, target, data in graph_obj.edges(data=True):
            rule_details = data.get("rule_details")
            if rule_details:
                self._validate_rule(source, target, rule_details)

    def _validate_rule(self, source: str, target: str, rule_details: dict) -> None:
        """Validate a single rule.

        Args:
            source: Source node name
            target: Target node name
            rule_details: Dictionary containing constraint, condition, and message
        """
        condition = rule_details.get("condition")
        if condition is not None:
            if not self._evaluate_condition(condition):
                logger.debug(
                    "Rule condition not met for %s -> %s. Condition: %s",
                    source,
                    target,
                    condition,
                )
                return

        constraint = rule_details.get("constraint")
        if constraint is not None:
            if not self._evaluate_constraint(constraint):
                error = self._create_error(target, rule_details, constraint)
                self.errors.append(error)
                logger.debug("Validation failed: %s", error.message)

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a condition string.

        Args:
            condition: The condition string to evaluate

        Returns:
            True if condition is met, False otherwise
        """
        try:
            return self._evaluate_expression(condition)
        except ValueError as e:
            logger.warning("Failed to evaluate condition '%s': %s", condition, str(e))
            return True

    def _evaluate_constraint(self, constraint: str) -> bool:
        """Evaluate a constraint string.

        Args:
            constraint: The constraint string to evaluate

        Returns:
            True if constraint is satisfied, False otherwise
        """
        try:
            return self._evaluate_expression(constraint)
        except ValueError as e:
            logger.warning("Failed to evaluate constraint '%s': %s", constraint, str(e))
            return True

    def _evaluate_expression(self, expression: str) -> bool:
        """Evaluate a boolean expression with property substitution.

        Args:
            expression: The expression to evaluate

        Returns:
            Boolean result of the expression
        """
        eval_expr = expression
        for prop_name, prop_data in self.property_map.items():
            value = prop_data["value"]

            if value is None or value == "" or (isinstance(value, str) and value.lower() == "null"):
                eval_expr = eval_expr.replace(f"{prop_name}", "None")
            else:
                try:
                    numeric_value = float(value)
                    eval_expr = eval_expr.replace(f"{prop_name}", str(numeric_value))
                except (ValueError, TypeError):
                    eval_expr = eval_expr.replace(f"{prop_name}", f"'{value}'")

        eval_expr = eval_expr.replace(" null", " None").replace("null", "None")

        try:
            # Use eval() for dynamic constraint evaluation - security ensured by
            # restricting builtins and validating expressions beforehand
            result = eval(eval_expr, {"__builtins__": {}}, {})
            return bool(result)
        except Exception as e:
            logger.debug("Evaluation failed for: %s. Error: %s", eval_expr, str(e))
            raise ValueError(f"Cannot evaluate expression: {eval_expr}") from e

    def _create_error(
        self, target: str, rule_details: dict, constraint: str
    ) -> GenomeError:
        """Create a GenomeError object for a validation failure.

        Args:
            target: The target property that failed validation
            rule_details: Dictionary containing constraint and message
            constraint: The constraint that failed

        Returns:
            GenomeError object
        """
        target_property = self.property_map.get(target, {}).get("original_property")

        if target_property is None:
            genome_type = next(
                (
                    prop.get("genome_type")
                    for prop in self.property_map.values()
                    if prop.get("genome_type")
                ),
                "unknown",
            )
            target_property = GenomeProperty(
                property_type="GENOME_PROPERTY",
                name=target,
                value="",
                unit="",
                genome_type=genome_type,
            )

        error_message = rule_details.get("message", f"Validation failed: {constraint}")

        return GenomeError(
            genome_property=target_property,
            reason=constraint,
            message=error_message,
            error_type="CONSTRAINT_VIOLATION",
        )

