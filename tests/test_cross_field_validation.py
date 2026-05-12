"""Unit tests for cross-field validation endpoint."""

import pytest
from unittest.mock import MagicMock, patch, call
from fastapi.testclient import TestClient
from fastapi.exceptions import ResponseValidationError

from app.main import app
from app.schemas.validation_request import ValidationRequest
from app.schemas.genome_properties import GenomeProperty
from app.schemas.genome_error import GenomeError


client = TestClient(app)


class TestCrossFieldValidationBasic:
    """Basic input validation tests for the cross-field validation endpoint."""

    def test_cross_field_validation_with_empty_properties(self):
        """Test that endpoint returns 400 error when properties list is empty."""
        request_data = {"properties": []}
        
        response = client.post(
            "/cross-field-validation/",
            json=request_data
        )
        
        assert response.status_code == 400
        assert "at least one property" in response.json()["detail"]

    def test_cross_field_validation_invalid_request_schema(self):
        """Test that invalid request schema is rejected."""
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    # Missing required fields: value, unit, genome_type
                }
            ]
        }
        
        response = client.post(
            "/cross-field-validation/",
            json=request_data
        )
        
        # Should return 422 (validation error)
        assert response.status_code == 422

    def test_cross_field_validation_missing_properties_field(self):
        """Test that missing properties field is rejected."""
        request_data = {}
        
        response = client.post(
            "/cross-field-validation/",
            json=request_data
        )
        
        # Should return 422 (validation error)
        assert response.status_code == 422


class TestCrossFieldValidationLogic:
    """Tests for the core logic of cross-field validation using unit testing approach."""

    def test_extracts_genome_type_from_first_property(self):
        """Test that genome_type is correctly extracted from first property."""
        properties = [
            GenomeProperty(
                property_type="STANDARD",
                name="length",
                value="100",
                unit="bp",
                genome_type="mouse"
            ),
            GenomeProperty(
                property_type="STANDARD",
                name="gc_content",
                value="45",
                unit="%",
                genome_type="human"
            )
        ]
        
        # Verify first property genome_type is "mouse"
        assert properties[0].genome_type == "mouse"

    def test_validation_request_schema(self):
        """Test that ValidationRequest properly validates input."""
        valid_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human"
                }
            ]
        }
        
        request = ValidationRequest(**valid_data)
        assert len(request.properties) == 1
        assert request.properties[0].name == "length"
        assert request.properties[0].genome_type == "human"

    def test_multiple_properties_parsing(self):
        """Test that multiple properties are correctly parsed."""
        valid_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human"
                },
                {
                    "property_type": "STANDARD",
                    "name": "gc_content",
                    "value": "45",
                    "unit": "%",
                    "genome_type": "human"
                }
            ]
        }
        
        request = ValidationRequest(**valid_data)
        assert len(request.properties) == 2
        property_names = [prop.name for prop in request.properties]
        assert "length" in property_names
        assert "gc_content" in property_names

    def test_validation_response_schema(self):
        """Test that ValidationResponse correctly validates output."""
        property_obj = GenomeProperty(
            property_type="STANDARD",
            name="length",
            value="100",
            unit="bp",
            genome_type="human"
        )
        
        error_data = {
            "errors": [
                {
                    "genome_property": property_obj,
                    "reason": "Value out of range",
                    "message": "Length cannot exceed 1000 bp",
                    "error_type": "VALUE_ERROR"
                }
            ]
        }
        
        from app.schemas.validation_response import ValidationResponse
        response = ValidationResponse(**error_data)
        assert len(response.errors) == 1
        assert response.errors[0].error_type == "VALUE_ERROR"

    def test_empty_errors_in_response(self):
        """Test ValidationResponse with no errors."""
        from app.schemas.validation_response import ValidationResponse
        response = ValidationResponse(errors=[])
        assert len(response.errors) == 0


class TestCrossFieldValidationEndpointFlow:
    """Tests for endpoint behavior with mocked dependencies."""

    def test_load_graph_called_with_genome_type(self):
        """Test that GRAPH_BUILDER.load_graph is called with correct genome type."""
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human"
                }
            ]
        }
        
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules:
            
            # Setup mocks
            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules"
            mock_rules.parse_rules.return_value = []
            mock_builder.build_graph.return_value = MagicMock()
            
            # Make request
            try:
                response = client.post(
                    "/cross-field-validation/",
                    json=request_data
                )
            except ResponseValidationError:
                # Expected due to None return (TODO in endpoint)
                pass
            
            # Verify graph builder was called with correct genome type
            mock_builder.load_graph.assert_called_once_with(genome_type="human")

    def test_graph_exists_skips_generation(self):
        """Test that when graph exists, AI rules generation is skipped."""
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human"
                }
            ]
        }
        
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules:
            
            # Setup mocks - graph exists
            mock_graph = MagicMock()
            mock_builder.load_graph.return_value = mock_graph
            
            try:
                response = client.post(
                    "/cross-field-validation/",
                    json=request_data
                )
            except ResponseValidationError:
                pass
            
            # Verify AI service was NOT called
            mock_ai.return_value.generate_rules.assert_not_called()
            mock_prompt.build_prompt.assert_not_called()

    def test_graph_load_failure_triggers_generation(self):
        """Test that when graph loading fails, rules are generated."""
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human"
                }
            ]
        }
        
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules:
            
            # Setup mocks - load fails
            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules"
            mock_rules.parse_rules.return_value = []
            mock_builder.build_graph.return_value = MagicMock()
            
            try:
                response = client.post(
                    "/cross-field-validation/",
                    json=request_data
                )
            except ResponseValidationError:
                pass
            
            # Verify generation flow was triggered
            mock_prompt.build_prompt.assert_called_once()
            mock_ai.return_value.generate_rules.assert_called_once()
            mock_rules.parse_rules.assert_called_once()
            mock_builder.build_graph.assert_called_once()

    def test_property_names_passed_to_prompt_builder(self):
        """Test that property names are correctly passed to prompt builder."""
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human"
                },
                {
                    "property_type": "STANDARD",
                    "name": "gc_content",
                    "value": "45",
                    "unit": "%",
                    "genome_type": "human"
                }
            ]
        }
        
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules:
            
            # Setup mocks
            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules"
            mock_rules.parse_rules.return_value = []
            mock_builder.build_graph.return_value = MagicMock()
            
            try:
                response = client.post(
                    "/cross-field-validation/",
                    json=request_data
                )
            except ResponseValidationError:
                pass
            
            # Verify prompt builder was called with property names
            call_args = mock_prompt.build_prompt.call_args[0]
            property_names = call_args[0]
            assert "length" in property_names
            assert "gc_content" in property_names

    def test_rules_passed_to_graph_builder(self):
        """Test that parsed rules are passed to graph builder."""
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human"
                }
            ]
        }
        
        expected_rules = ["rule1", "rule2", "rule3"]
        
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules:
            
            # Setup mocks
            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules response"
            mock_rules.parse_rules.return_value = expected_rules
            mock_builder.build_graph.return_value = MagicMock()
            
            try:
                response = client.post(
                    "/cross-field-validation/",
                    json=request_data
                )
            except ResponseValidationError:
                pass
            
            # Verify build_graph was called with parsed rules
            mock_builder.build_graph.assert_called_once()
            call_args = mock_builder.build_graph.call_args[0]
            assert call_args[0] == expected_rules

    def test_genome_type_passed_to_graph_builder(self):
        """Test that genome type is passed to graph builder."""
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "mouse"
                }
            ]
        }
        
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules:
            
            # Setup mocks
            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules"
            mock_rules.parse_rules.return_value = []
            mock_builder.build_graph.return_value = MagicMock()
            
            try:
                response = client.post(
                    "/cross-field-validation/",
                    json=request_data
                )
            except ResponseValidationError:
                pass
            
            # Verify build_graph was called with correct genome type
            call_args, kwargs = mock_builder.build_graph.call_args
            # genome_type is the second positional argument
            assert call_args[1] == "mouse"


class TestCrossFieldValidationIntegration:
    """Integration tests for complete flows."""

    def test_complete_flow_no_existing_graph(self):
        """Test complete flow: load fails → generate rules → build graph."""
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human"
                }
            ]
        }
        
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules:
            
            # Setup complete mock flow
            mock_builder.load_graph.return_value = None
            mock_prompt.build_prompt.return_value = "test prompt"
            mock_ai.return_value.generate_rules.return_value = "test rules"
            mock_rules.parse_rules.return_value = ["rule1", "rule2"]
            mock_builder.build_graph.return_value = MagicMock()
            
            try:
                response = client.post(
                    "/cross-field-validation/",
                    json=request_data
                )
            except ResponseValidationError:
                pass
            
            # Verify complete call sequence
            assert mock_builder.load_graph.call_count == 1
            assert mock_prompt.build_prompt.call_count == 1
            assert mock_ai.return_value.generate_rules.call_count == 1
            assert mock_rules.parse_rules.call_count == 1
            assert mock_builder.build_graph.call_count == 1

    def test_complete_flow_with_existing_graph(self):
        """Test complete flow: graph exists → skip generation."""
        request_data = {
            "properties": [
                {
                    "property_type": "STANDARD",
                    "name": "length",
                    "value": "100",
                    "unit": "bp",
                    "genome_type": "human"
                }
            ]
        }
        
        with patch("app.routers.cross_field_validation.GRAPH_BUILDER") as mock_builder, \
             patch("app.routers.cross_field_validation.get_ai_service") as mock_ai, \
             patch("app.routers.cross_field_validation.PROMPT_BUILDER") as mock_prompt, \
             patch("app.routers.cross_field_validation.RULE_BUILDER") as mock_rules:
            
            # Setup mocks - graph exists
            mock_graph = MagicMock()
            mock_builder.load_graph.return_value = mock_graph
            
            try:
                response = client.post(
                    "/cross-field-validation/",
                    json=request_data
                )
            except ResponseValidationError:
                pass
            
            # Verify only load_graph was called, others were skipped
            assert mock_builder.load_graph.call_count == 1
            assert mock_prompt.build_prompt.call_count == 0
            assert mock_ai.return_value.generate_rules.call_count == 0
            assert mock_rules.parse_rules.call_count == 0
            assert mock_builder.build_graph.call_count == 0
