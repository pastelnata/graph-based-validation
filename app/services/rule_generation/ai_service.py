"""Service for interacting with Google Gemini API to generate validation rules."""

import json
import logging
import os

from google import genai


logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Exception raised when AI service operations fail."""

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None
        ):
        """Initialize AIServiceError."""
        super().__init__(message)
        self.original_error = original_error


class AIService:
    """Service for communicating with Google Gemini API."""

    def __init__(self, api_key: str):
        """Initialize AIService with API key."""
        if not api_key or not isinstance(api_key, str):
            raise AIServiceError(
                "Invalid API key provided to AIService"
            )

        self.api_model = os.getenv("GEMINI_MODEL")
        if not self.api_model:
            raise AIServiceError(
                "GEMINI_MODEL environment variable is not set"
            )

        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as error:
            error_msg = (f"Failed to initialize Gemini API: {str(error)}")
            logger.error(error_msg)
            raise AIServiceError(error_msg, original_error=error) from error

    def generate_rules(self, prompt: str) -> str:
        """Send prompt to Gemini API and get JSON response."""
        try:
            response = self.client.models.generate_content(
                model=self.api_model,
                contents=prompt
            )

            if not response.text:
                raise AIServiceError("Gemini API returned empty response")


            clean_json = self._extract_json(response.text)
            self._validate_json_response(clean_json)

            return clean_json

        except AIServiceError:
            raise
        except Exception as error:
            error_msg = f"Gemini API call failed: {str(error)}"
            logger.error(error_msg)
            raise AIServiceError(error_msg, original_error=error) from error


    def _extract_json(self, text: str) -> str:
        """Extract JSON array from Gemini response."""
        if not text:
            raise AIServiceError(
                "Empty response from Gemini"
            )

        text = text.strip()

        if text.startswith("```json"):
            text = (
                text.removeprefix("```json")
                .removesuffix("```")
                .strip()
            )

        elif text.startswith("```"):
            text = (
                text.removeprefix("```")
                .removesuffix("```")
                .strip()
            )

        start = text.find("[")
        end = text.rfind("]")

        if start == -1 or end == -1:
            raise AIServiceError(
                f"No JSON array found in response: "
                f"{text[:300]}"
            )

        return text[start : end + 1]

    def _validate_json_response(
        self,
        response_text: str,
    ) -> None:
        """Validate that response is a valid JSON array."""
        try:
            parsed = json.loads(response_text)

            if not isinstance(parsed, list):
                raise AIServiceError(
                    "Expected JSON array response"
                )

        except json.JSONDecodeError as error:
            raise AIServiceError(
                f"Invalid JSON after extraction: {str(error)}",
                original_error=error,
            ) from error

