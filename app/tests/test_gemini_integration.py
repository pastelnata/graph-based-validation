"""Integration test with real Gemini API (optional)."""

import os
import pytest
from app.services.gemini_service import GeminiService
from app.schemas.genome_properties import GenomeProperty
from app.services.rule_generation.prompt_builder import PromptBuilder
from app.services.rule_generation.prompt_template import TEMPLATE


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set - skipping real API tests"
)
class TestGeminiIntegration:
    """Integration tests using real Gemini API."""

    def test_real_api_call(self):
        """Test with real Gemini API (requires GEMINI_API_KEY env var)."""
        service = GeminiService()
        
        prompt_builder = PromptBuilder(TEMPLATE)
        properties = ["age", "weight", "height"]
        prompt = prompt_builder.build_prompt(properties)
        
        # Call real API
        response = service.query(prompt)
        
        assert response is not None
        assert len(response) > 0
        
    def test_real_api_json_parsing(self):
        """Test parsing real API response."""
        service = GeminiService()
        
        prompt_builder = PromptBuilder(TEMPLATE)
        properties = ["user_age", "minimum_age", "user_score", "passing_score"]
        prompt = prompt_builder.build_prompt(properties)
        
        # Call real API
        response = service.query(prompt)
        
        # Parse response
        rules = service.parse_rules_json(response)
        
        # Should return list of rules
        assert isinstance(rules, list)
        
        if rules:  # If API returns any rules
            for rule in rules:
                assert "inputs" in rule
                assert "expression" in rule
                assert isinstance(rule["inputs"], list)
                assert len(rule["inputs"]) >= 2
