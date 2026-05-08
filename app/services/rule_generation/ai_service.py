"""Service for interacting with Google Gemini API to generate validation rules."""

import json
import logging
from typing import Any

import google.generativeai as genai

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
        """
        try:
            enriched_prompt = self._build_enriched_prompt(prompt, genome_attributes)

            response = self.model.generate_content(
                enriched_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=2048,
                ),
            )

            if not response.text:
                raise AIServiceError("Gemini API returned empty response")

            logger.debug(
                "Raw Gemini response (truncated): %s",
                response.text[:300],
            )

            clean_json = self._extract_json(response.text)
            self._validate_json_response(clean_json)

            return clean_json

        except AIServiceError:
            raise
        except Exception as e:
            error_msg = f"Gemini API call failed: {str(e)}"
            logger.error(error_msg)
            raise AIServiceError(error_msg, original_error=e) from e

    def _build_enriched_prompt(
        self, prompt: str, genome_attributes: dict[str, Any]
    ) -> str:
        attributes_json = json.dumps(genome_attributes, indent=2)

        return f"""{prompt}

## Genome Attributes Context:

{attributes_json}

## Instructions:
- Return ONLY a valid JSON array
- No markdown, no explanations, no extra text
"""

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON array from model output safely.
        Handles markdown fences and extra explanation text.
        """

        if not text:
            raise AIServiceError("Empty response from Gemini")

        text = text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        # Extract JSON array boundaries
        start = text.find("[")
        end = text.rfind("]")

        if start == -1 or end == -1:
            raise AIServiceError(
                f"No JSON array found in response: {text[:300]}"
            )

        return text[start:end + 1]

    def _validate_json_response(self, response_text: str) -> None:
        """
        Validate that the response is valid JSON and is a list.
        """
        try:
            parsed = json.loads(response_text)

            if not isinstance(parsed, list):
                raise AIServiceError(
                    f"Expected JSON array, got {type(parsed).__name__}"
                )

        except json.JSONDecodeError as e:
            raise AIServiceError(
                f"Invalid JSON after extraction: {str(e)}\nRaw: {response_text[:300]}",
                original_error=e,
            ) from e