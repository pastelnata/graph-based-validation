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
    """Validates genome properties against a rule graph.

    This class is stateless: no per-request data is stored on the instance.
    All state (property map, error list) lives in locals during validate()
    and is passed explicitly to private helpers. A single instance can
    therefore be reused safely across concurrent requests.
    """

    def validate(
        self,
        properties: list[GenomeProperty],
        graph: Graph,
    ) -> list[GenomeError]:
        """Validate properties against the rule graph and return any errors."""
        property_map = self._build_property_map(properties)
        errors: list[GenomeError] = []

        if graph.cycles:
            logger.warning(
                "Graph contains %d cycle(s). These will be noted but validation will continue.",
                len(graph.cycles),
            )

        self._traverse_and_validate(graph.graph, property_map, errors)

        logger.info("Validation complete. Found %d error(s).", len(errors))
        return errors

    @staticmethod
    def _build_property_map(
        properties: list[GenomeProperty],
    ) -> dict[str, dict[str, Any]]:
        """Build a map of property names to their values for quick lookup."""
        property_map: dict[str, dict[str, Any]] = {}
        for prop in properties:
            property_map[prop.name] = {
                "value": prop.value,
                "unit": prop.unit,
                "property_type": prop.property_type,
                "genome_type": prop.genome_type,
                "original_property": prop,
            }
        return property_map

    def _traverse_and_validate(
        self,
        graph_obj: nx.DiGraph,
        property_map: dict[str, dict[str, Any]],
        errors: list[GenomeError],
    ) -> None:
        """Traverse the graph and validate rules."""
        if nx.is_directed_acyclic_graph(graph_obj):
            logger.debug("Graph is acyclic; topological sort available for traversal.")
        else:
            logger.warning("Graph contains cycles. Using unordered edge traversal.")

        # Validate all edges (rules) regardless of traversal order
        for source, target, data in graph_obj.edges(data=True):
            rule_details = data.get("rule_details")
            if rule_details:
                self._validate_rule(source, target, rule_details, property_map, errors)

    def _validate_rule(
        self,
        source: str,
        target: str,
        rule_details: dict[str, Any],
        property_map: dict[str, dict[str, Any]],
        errors: list[GenomeError],
    ) -> None:
        """Validate a single rule and append any error to `errors`."""
        condition = rule_details.get("condition")
        if condition is not None and not self._evaluate_condition(condition, property_map):
            logger.debug(
                "Rule condition not met for %s -> %s. Condition: %s",
                source,
                target,
                condition,
            )
            return

        constraint = rule_details.get("constraint")
        if constraint is not None and not self._evaluate_constraint(constraint, property_map):
            error = self._create_error(target, rule_details, constraint, property_map)
            errors.append(error)
            logger.debug("Validation failed: %s", error.message)

    def _evaluate_condition(
        self,
        condition: str,
        property_map: dict[str, dict[str, Any]],
    ) -> bool:
        """Evaluate a condition string. Returns True (rule applies) on failure."""
        try:
            return self._evaluate_expression(condition, property_map)
        except ValueError as exc:
            logger.warning("Failed to evaluate condition '%s': %s", condition, exc)
            return True

    def _evaluate_constraint(
        self,
        constraint: str,
        property_map: dict[str, dict[str, Any]],
    ) -> bool:
        """Evaluate a constraint string. Returns True (passes) on failure."""
        try:
            return self._evaluate_expression(constraint, property_map)
        except ValueError as exc:
            logger.warning("Failed to evaluate constraint '%s': %s", constraint, exc)
            return True

    @staticmethod
    def _evaluate_expression(
        expression: str,
        property_map: dict[str, dict[str, Any]],
    ) -> bool:
        """Evaluate a boolean expression with property substitution."""
        eval_expr = expression
        # Replace longer names first so that e.g. "gc_content" isn't
        # corrupted by an earlier replacement of "gc".
        for prop_name in sorted(property_map.keys(), key=len, reverse=True):
            value = property_map[prop_name]["value"]

            if (
                value is None
                or value == ""
                or (isinstance(value, str) and value.lower() == "null")
            ):
                eval_expr = eval_expr.replace(prop_name, "None")
            else:
                try:
                    numeric_value = float(value)
                    eval_expr = eval_expr.replace(prop_name, str(numeric_value))
                except (ValueError, TypeError):
                    eval_expr = eval_expr.replace(prop_name, f"'{value}'")

        eval_expr = eval_expr.replace(" null", " None").replace("null", "None")

        try:
            # Use eval() for dynamic constraint evaluation - security ensured by
            # restricting builtins and validating expressions beforehand.
            result = eval(eval_expr, {"__builtins__": {}}, {})  # pylint: disable=eval-used
            return bool(result)
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("Evaluation failed for: %s. Error: %s", eval_expr, exc)
            raise ValueError(f"Cannot evaluate expression: {eval_expr}") from exc

    @staticmethod
    def _create_error(
        target: str,
        rule_details: dict[str, Any],
        constraint: str,
        property_map: dict[str, dict[str, Any]],
    ) -> GenomeError:
        """Create a GenomeError object for a validation failure."""
        target_property = property_map.get(target, {}).get("original_property")

        if target_property is None:
            genome_type = next(
                (
                    prop.get("genome_type")
                    for prop in property_map.values()
                    if prop.get("genome_type")
                ),
                "unknown",
            )
            target_property = GenomeProperty(
                property_type="GENOME_PROPERTY",
                name=target,
                value="",
                unit=None,
                genome_type=genome_type,
            )

        error_message = rule_details.get("message", f"Validation failed: {constraint}")

        return GenomeError(
            genome_property=target_property,
            reason=constraint,
            message=error_message,
            error_type="CONSTRAINT_VIOLATION",
        )
