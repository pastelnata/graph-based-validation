from __future__ import annotations

import json
import logging
from typing import Any

from app.schemas.rule import Rule


logger = logging.getLogger(__name__)


class RuleParsingError(Exception):
    """Raised when AI response cannot be parsed as JSON."""
    
    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class RuleValidationError(Exception):
    """Raised when Pydantic validation fails."""
    
    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class InvalidRuleDataError(Exception):
    """Raised when rule data violates business logic constraints."""
    
    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class RuleBuilder:
    """
    Service for parsing and building Rule objects from AI-generated JSON responses.
    """
    
    def get_rules(self, ai_response: str) -> list[Rule]:
        """
        Parse an AI-generated JSON response into a list of Rule objects.
        """
        try:
            parsed_data = json.loads(ai_response)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in AI response: {str(e)}"
            logger.error(error_msg)
            raise RuleParsingError(error_msg, original_error=e) from e
        
        rules = []
        for item in parsed_data:
            try:
                rule = self.convert_to_rule(item)
                rules.append(rule)
            except (RuleValidationError, InvalidRuleDataError) as e:
                error_msg = (
                    f"Failed to parse rule: {str(e)}. "
                    f"Item: {json.dumps(item)[:100]}"
                )
                logger.error(error_msg)
                raise RuleValidationError(error_msg, original_error=e) from e
        
        logger.info(
            f"Successfully parsed {len(rules)} rules from AI response. "
            f"Rules: {[r.source for r in rules]}"
        )
        return rules
    
    def convert_to_rule(self, data: dict[str, Any]) -> Rule:
        """
        Convert raw data to Rule object.
        """
        try:
            rule = Rule(**data)
            return rule
        except ValueError as e:
            error_msg = f"Rule validation failed: {str(e)}"
            logger.warning(error_msg)
            raise RuleValidationError(error_msg, original_error=e) from e
