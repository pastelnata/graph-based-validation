"""Tests for Gemini service."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.gemini_service import GeminiService


class TestGeminiService:
    """Test suite for GeminiService."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        service = GeminiService(api_key="test-key-123")
        assert service.client is not None
        assert service.model == "gemini-2.0-flash"

    def test_init_without_api_key_env_var(self):
        """Test initialization fails when no API key is provided."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                GeminiService()

    def test_init_with_env_var(self, monkeypatch):
        """Test initialization with API key from environment variable."""
        monkeypatch.setenv("GEMINI_API_KEY", "env-key-123")
        service = GeminiService()
        assert service.client is not None

    @patch('app.services.gemini_service.genai.Client')
    def test_query_success(self, mock_client_class):
        """Test successful API query."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = '[{"inputs": ["field1", "field2"], "expression": "field1 > field2"}]'
        mock_client.models.generate_content.return_value = mock_response

        # Test
        service = GeminiService(api_key="test-key")
        service.client = mock_client
        result = service.query("test prompt")

        # Assert
        assert result == '[{"inputs": ["field1", "field2"], "expression": "field1 > field2"}]'
        mock_client.models.generate_content.assert_called_once()

    @patch('app.services.gemini_service.genai.Client')
    def test_query_empty_response(self, mock_client_class):
        """Test handling of empty API response."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client.models.generate_content.return_value = mock_response

        service = GeminiService(api_key="test-key")
        service.client = mock_client
        result = service.query("test prompt")

        assert result == ""

    @patch('app.services.gemini_service.genai.Client')
    def test_query_api_error(self, mock_client_class):
        """Test handling of API errors."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("API Error")

        service = GeminiService(api_key="test-key")
        service.client = mock_client

        with pytest.raises(Exception, match="API Error"):
            service.query("test prompt")

    def test_parse_rules_json_valid(self):
        """Test parsing valid JSON response."""
        service = GeminiService(api_key="test-key")
        
        response = '[{"inputs": ["age", "height"], "expression": "age > 18 -> height > 150"}]'
        rules = service.parse_rules_json(response)

        assert len(rules) == 1
        assert rules[0]["inputs"] == ["age", "height"]
        assert rules[0]["expression"] == "age > 18 -> height > 150"

    def test_parse_rules_json_with_extra_text(self):
        """Test parsing JSON response with surrounding text."""
        service = GeminiService(api_key="test-key")
        
        response = """Here are the rules:
[
  {"inputs": ["field1", "field2"], "expression": "field1 <= field2"},
  {"inputs": ["field3", "field4"], "expression": "field3 == field4"}
]
End of rules."""
        
        rules = service.parse_rules_json(response)

        assert len(rules) == 2
        assert rules[0]["inputs"] == ["field1", "field2"]
        assert rules[1]["inputs"] == ["field3", "field4"]

    def test_parse_rules_json_empty_array(self):
        """Test parsing empty JSON array."""
        service = GeminiService(api_key="test-key")
        
        response = "[]"
        rules = service.parse_rules_json(response)

        assert rules == []

    def test_parse_rules_json_invalid(self):
        """Test parsing invalid JSON raises error."""
        service = GeminiService(api_key="test-key")
        
        response = "This is not JSON {invalid}"
        
        with pytest.raises(json.JSONDecodeError):
            service.parse_rules_json(response)

    def test_parse_rules_json_no_array(self):
        """Test parsing response without JSON array."""
        service = GeminiService(api_key="test-key")
        
        response = "This response doesn't contain JSON"
        rules = service.parse_rules_json(response)

        assert rules == []
