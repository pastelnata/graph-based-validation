"""Service for interacting with Google Gemini API to generate validation rules."""

import json
import logging
from typing import Any

import google.generativeai as genai
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Raised when AI service fails."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class AIService:
    """
    Service for calling Google Gemini API to generate validation rules
    from a prompt and genome attribute data.
    """

    def __init__(self, api_key: str):
        """
        Initialize the AI service with Gemini API key.

        Args:
            api_key: Google Gemini API key

        Raises:
            AIServiceError: If API key is invalid or empty
        """
        if not api_key or not isinstance(api_key, str):
            raise AIServiceError("Invalid API key provided to AIService")

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
        except Exception as e:
            error_msg = f"Failed to initialize Gemini API: {str(e)}"
            logger.error(error_msg)
            raise AIServiceError(error_msg, original_error=e) from e

    def generate_rules(self, prompt: str, genome_attributes: dict[str, Any]) -> str:
        """
        Send prompt to Gemini API and get JSON response with validation rules.

        Args:
            prompt: The formatted prompt from PromptBuilder
            genome_attributes: Dictionary containing genome attribute schema and data

        Returns:
            JSON string containing validation rules in the expected format

        Raises:
            AIServiceError: If the API call fails or returns invalid response
        """
        try:
            # Build the enriched prompt with genome attributes context
            enriched_prompt = self._build_enriched_prompt(prompt, genome_attributes)

            # Call Gemini API
            response = self.model.generate_content(
                enriched_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Low temperature for consistent JSON output
                    max_output_tokens=2048,
                ),
            )

            if not response.text:
                error_msg = "Gemini API returned empty response"
                logger.error(error_msg)
                raise AIServiceError(error_msg)

            logger.debug("Received response from Gemini API: %s", response.text[:200])

            # Validate response is valid JSON
            self._validate_json_response(response.text)

            return response.text

        except AIServiceError:
            raise
        except Exception as e:
            error_msg = f"Gemini API call failed: {str(e)}"
            logger.error(error_msg)
            raise AIServiceError(error_msg, original_error=e) from e

    def _build_enriched_prompt(
        self, prompt: str, genome_attributes: dict[str, Any]
    ) -> str:
        """
        Enrich the prompt with genome attribute context and constraints.

        Args:
            prompt: Base prompt from PromptBuilder
            genome_attributes: Genome attribute schema and data

        Returns:
            Enhanced prompt with attribute context
        """
        attributes_json = json.dumps(genome_attributes, indent=2)

        enriched = f"""{prompt}

## Genome Attributes Context:

{attributes_json}

## Additional Instructions:
- Analyze the provided attributes and their data types
- Identify logical relationships based on domain knowledge
- Consider constraints that would apply in a real-world validation scenario
- Return ONLY the JSON array, no other text
"""
        return enriched

    def _validate_json_response(self, response_text: str) -> None:
        """
        Validate that the response is valid JSON.

        Args:
            response_text: Response text from API

        Raises:
            AIServiceError: If response is not valid JSON
        """
        try:
            # Try to parse as JSON
            parsed = json.loads(response_text)

            # Validate it's a list
            if not isinstance(parsed, list):
                raise AIServiceError(
                    f"Expected JSON array, got {type(parsed).__name__}"
                )

            logger.debug("Response validation successful: JSON array with %d items",
                        len(parsed))
        except json.JSONDecodeError as e:
            error_msg = f"API response is not valid JSON: {str(e)}"
            logger.error(error_msg)
            raise AIServiceError(error_msg, original_error=e) from e
