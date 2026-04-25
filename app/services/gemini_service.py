"""Gemini AI service for querying the Gemini API."""

import json
import logging
import os

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Gemini API."""

    def __init__(self, api_key: str | None = None):
        """Initialize the Gemini service.
        
        Args:
            api_key: Gemini API key. If None, will try to read from GEMINI_API_KEY env var.
        """
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY not provided and not found in environment variables"
                )
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def query(self, prompt: str) -> str:
        """Send a prompt to Gemini and get the response.
        
        Args:
            prompt: The prompt to send to Gemini.
            
        Returns:
            The response text from Gemini.
            
        Raises:
            Exception: If the API call fails.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            
            if response.text:
                logger.info("Received response from Gemini")
                return response.text
            else:
                logger.warning("Empty response from Gemini")
                return ""
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise

    def parse_rules_json(self, response: str) -> list[dict]:
        """Parse JSON rules from Gemini response.
        
        Args:
            response: The response text from Gemini containing JSON.
            
        Returns:
            A list of rule dictionaries with 'inputs' and 'expression'.
            
        Raises:
            json.JSONDecodeError: If the response doesn't contain valid JSON.
        """
        try:
            # Try to extract JSON from the response
            # Sometimes the model might include extra text
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                rules = json.loads(json_str)
                logger.info(f"Parsed {len(rules)} rules from Gemini response")
                return rules
            else:
                logger.warning("No JSON array found in response")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {str(e)}")
            raise
