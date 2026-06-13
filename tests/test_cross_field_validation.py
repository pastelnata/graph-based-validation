"""Unit tests for cross-field validation endpoint."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.genome_properties import GenomeProperty
from app.schemas.validation_request import ValidationRequest
from app.schemas.validation_response import ValidationResponse

client = TestClient(app)


class TestCrossFieldValidationBasic:
    """Basic input validation tests for the cross-field validation endpoint."""

    def test_cross_field_validation_with_empty_properties(self):
        """Endpoint returns 400 when properties list is empty."""
        response = client.post(
            "/cross-field-validation/",
            json={"properties": []},
        )

        assert response.status_code == 400
        assert "at least one property" in response.json()["detail"]

    def test_cross_field_validation_invalid_request_schema(self):
        """Request missing required fields is rejected with 422."""
        # `unit` is now optional, but `value` and `genome_type` are still required.
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD"
                    # Missing required: value, genome_type
                }
            ]
        }

        response = client.post("/cross-field-validation/", json=request_data)
        assert response.status_code == 422


    def test_cross_field_validation_missing_unit_is_accepted(self):
        """Request missing optional `unit` field is accepted (200)."""
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "genome_type": "human",
                    # `unit` omitted — should be allowed.
                }
            ]
        }

        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:
            mock_builder.load_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = []

            response = client.post("/cross-field-validation/", json=request_data)

        assert response.status_code == 200
        assert response.json() == {"errors": []}

    def test_cross_field_validation_missing_properties_field(self):
        """Missing `properties` field is rejected with 422."""
        response = client.post("/cross-field-validation/", json={})
        assert response.status_code == 422


class TestCrossFieldValidationLogic:
    """Tests for schema parsing and request/response shapes."""

    def test_extracts_genome_type_from_first_property(self):
        """genome_type is correctly read off the first property."""
        properties = [
            GenomeProperty(
                property_type="STANDARD",
                name="length",
                value="100",
                unit="bp",
                genome_type="mouse",
            ),
            GenomeProperty(
                property_type="STANDARD",
                name="gc_content",
                value="45",
                unit="%",
                genome_type="human",
            ),
        ]
        assert properties[0].genome_type == "mouse"

    def test_validation_request_schema(self):
        """ValidationRequest accepts well-formed input."""
        request = ValidationRequest(
            properties=[
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human",
                }
            ]
        )
        assert len(request.properties) == 1
        assert request.properties[0].name == "length"
        assert request.properties[0].genome_type == "human"

    def test_validation_request_unit_optional(self):
        """ValidationRequest accepts properties without a unit."""
        request = ValidationRequest(
            properties=[
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "genome_type": "human",
                }
            ]
        )
        assert request.properties[0].unit is None

    def test_multiple_properties_parsing(self):
        """Multiple properties parse correctly."""
        request = ValidationRequest(
            properties=[
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human",
                },
                {
                    "property_type": "STANDARD",
                    "name": "gc_content",
                    "value": "45",
                    "unit": "%",
                    "genome_type": "human",
                },
            ]
        )
        names = [p.name for p in request.properties]
        assert "length" in names
        assert "gc_content" in names

    def test_validation_response_schema(self):
        """ValidationResponse correctly validates output."""
        property_obj = GenomeProperty(
            property_type="STANDARD",
            name="length",
            value="100",
            unit="bp",
            genome_type="human",
        )
        response = ValidationResponse(
            errors=[
                {
                    "genome_property": property_obj,
                    "reason": "Value out of range",
                    "message": "Length cannot exceed 1000 bp",
                    "error_type": "VALUE_ERROR",
                }
            ]
        )
        assert len(response.errors) == 1
        assert response.errors[0].error_type == "VALUE_ERROR"

    def test_empty_errors_in_response(self):
        """ValidationResponse with no errors is valid."""
        response = ValidationResponse(errors=[])
        assert response.errors == []


class TestCrossFieldValidationEndpointFlow:
    """Endpoint behavior with mocked dependencies."""

    def _request(self, genome_type: str = "human", extra_props=None):
        props = [
            {
                "property_type": "STANDARD",
                "name": "length",
                "value": "100",
                "unit": "bp",
                "genome_type": genome_type,
            }
        ]
        if extra_props:
            props.extend(extra_props)
        return {"properties": props}

    def test_load_graph_called_with_genome_type(self):
        """GRAPH_BUILDER.load_graph is called with the correct genome type."""
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules"
            mock_rules.parse_rules.return_value = []
            mock_builder.build_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = []

            response = client.post("/cross-field-validation/", json=self._request())

            assert response.status_code == 200
            mock_builder.load_graph.assert_called_once_with(genome_type="human")

    def test_graph_exists_skips_generation(self):
        """When a graph already exists, AI rule generation is skipped."""
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = []

            response = client.post("/cross-field-validation/", json=self._request())

            assert response.status_code == 200
            mock_ai.return_value.generate_rules.assert_not_called()
            mock_prompt.build_prompt.assert_not_called()
            mock_rules.parse_rules.assert_not_called()
            mock_builder.build_graph.assert_not_called()

    def test_graph_load_failure_triggers_generation(self):
        """When load returns None, the generation pipeline runs."""
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules"
            mock_rules.parse_rules.return_value = []
            mock_builder.build_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = []

            response = client.post("/cross-field-validation/", json=self._request())

            assert response.status_code == 200
            mock_prompt.build_prompt.assert_called_once()
            mock_ai.return_value.generate_rules.assert_called_once()
            mock_rules.parse_rules.assert_called_once()
            mock_builder.build_graph.assert_called_once()

    def test_property_names_passed_to_prompt_builder(self):
        """Property names are forwarded to the prompt builder."""
        extra = [{
            "property_type": "STANDARD",
            "name": "gc_content",
            "value": "45",
            "unit": "%",
            "genome_type": "human",
        }]
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules"
            mock_rules.parse_rules.return_value = []
            mock_builder.build_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = []

            response = client.post(
                "/cross-field-validation/",
                json=self._request(extra_props=extra),
            )

            assert response.status_code == 200
            (passed_names,), _ = mock_prompt.build_prompt.call_args
            assert "length" in passed_names
            assert "gc_content" in passed_names

    def test_rules_passed_to_graph_builder(self):
        """Parsed rules flow into build_graph."""
        expected_rules = ["rule1", "rule2", "rule3"]
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules response"
            mock_rules.parse_rules.return_value = expected_rules
            mock_builder.build_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = []

            response = client.post("/cross-field-validation/", json=self._request())

            assert response.status_code == 200
            args, _ = mock_builder.build_graph.call_args
            assert args[0] == expected_rules

    def test_genome_type_passed_to_graph_builder(self):
        """genome_type flows into build_graph."""
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules"
            mock_rules.parse_rules.return_value = []
            mock_builder.build_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = []

            response = client.post("/cross-field-validation/", json=self._request("mouse"))

            assert response.status_code == 200
            args, _ = mock_builder.build_graph.call_args
            assert args[1] == "mouse"

    def test_validator_instantiated_per_request(self):
        """GraphValidator() is constructed inside the endpoint on every call."""
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = []

            client.post("/cross-field-validation/", json=self._request())
            client.post("/cross-field-validation/", json=self._request())
            client.post("/cross-field-validation/", json=self._request())

            assert mock_validator_cls.call_count == 3

    def test_validator_invoked_with_properties_and_graph(self):
        """validator.validate() is called with the request props and the built graph."""
        mock_graph = MagicMock()
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = mock_graph
            mock_validator_instance = mock_validator_cls.return_value
            mock_validator_instance.validate.return_value = []

            response = client.post("/cross-field-validation/", json=self._request())

            assert response.status_code == 200
            assert mock_validator_instance.validate.call_count == 1
            args, _ = mock_validator_instance.validate.call_args
            assert args[1] is mock_graph
            assert len(args[0]) == 1
            assert args[0][0].name == "length"

    def test_endpoint_returns_validator_errors(self):
        """Errors produced by the validator are returned in the response body."""
        error_property = GenomeProperty(
            property_type="STANDARD",
            name="length",
            value="100",
            unit="bp",
            genome_type="human",
        )
        from app.schemas.genome_error import GenomeError
        sample_error = GenomeError(
            genome_property=error_property,
            reason="too long",
            message="Length exceeds maximum",
            error_type="CONSTRAINT_VIOLATION",
        )

        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = [sample_error]

            response = client.post("/cross-field-validation/", json=self._request())

            assert response.status_code == 200
            body = response.json()
            assert len(body["errors"]) == 1
            assert body["errors"][0]["error_type"] == "CONSTRAINT_VIOLATION"
            assert body["errors"][0]["message"] == "Length exceeds maximum"


class TestCrossFieldValidationIntegration:
    """End-to-end-ish tests across the endpoint's full call sequence."""

    def _request(self):
        return {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human",
                }
            ]
        }

    def test_complete_flow_no_existing_graph(self):
        """Full flow when no cached graph exists."""
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules"
            mock_rules.parse_rules.return_value = ["rule1", "rule2"]
            mock_builder.build_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = []

            response = client.post("/cross-field-validation/", json=self._request())

            assert response.status_code == 200
            assert mock_builder.load_graph.call_count == 1
            assert mock_prompt.build_prompt.call_count == 1
            assert mock_ai.return_value.generate_rules.call_count == 1
            assert mock_rules.parse_rules.call_count == 1
            assert mock_builder.build_graph.call_count == 1
            assert mock_validator_cls.return_value.validate.call_count == 1

    def test_complete_flow_with_existing_graph(self):
        """Full flow when a cached graph exists — generation skipped."""
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules, \
             patch("app.routers.cross_field_validation.GraphValidator") as mock_validator_cls:

            mock_builder.load_graph.return_value = MagicMock()
            mock_validator_cls.return_value.validate.return_value = []

            response = client.post("/cross-field-validation/", json=self._request())

            assert response.status_code == 200
            assert mock_builder.load_graph.call_count == 1
            assert mock_prompt.build_prompt.call_count == 0
            assert mock_ai.return_value.generate_rules.call_count == 0
            assert mock_rules.parse_rules.call_count == 0
            assert mock_builder.build_graph.call_count == 0
            assert mock_validator_cls.return_value.validate.call_count == 1
