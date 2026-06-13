"""Service for interacting with Google Gemini API to generate validation rules."""

import json
import logging
import os

from google import genai
from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
        retry=retry_if_exception_type((APIError, TimeoutError)),
        reraise=True,
    )
    def generate_rules(self, prompt: str) -> str:
        """Send prompt to Gemini API and get JSON response."""
        try:
            response = self.client.models.generate_content(
                model=self.api_model,
                contents=prompt,
                config={
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json"
                }
            )

            if not response.text:
                raise AIServiceError("Gemini API returned empty response")
            
            candidate = response.candidates[0] if response.candidates else None
            if candidate and candidate.finish_reason == "MAX_TOKENS":
                raise AIServiceError(
                    "Gemini response was truncated (hit max_output_tokens). "
                    "Consider reducing prompt size or splitting the request."
                )
            
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
                f"No JSON array found in response. Response starts with: {text[:100]}"
            )

        json_str = text[start : end + 1]
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON extracted: %s", json_str[:500])
            raise AIServiceError(
                f"Extracted text is not valid JSON: {str(e)}"
            ) from e

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

