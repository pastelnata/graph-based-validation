from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class PromptBuilderError(Exception):
    """Base exception for PromptBuilder errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error

class PromptBuilder:
    def __init__(self, template: str):
        if not template:
            raise PromptBuilderError("Prompt template cannot be empty")
        self.template = template

    def build_prompt(self, attributes: list[str]) -> str:
        try:
            if not attributes:
                raise ValueError("Attributes list cannot be empty")
            
            if not all(isinstance(attr, str) for attr in attributes):
                raise TypeError("All attributes must be strings")
            
            attributes_str = "\n".join(f"- {item}" for item in attributes)
            prompt = self.template.format(attributes=attributes_str)
            return prompt
                
        except Exception as e:
            error_msg = f"Invalid prompt builder input: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PromptBuilderError(error_msg, original_error=e) from e
    