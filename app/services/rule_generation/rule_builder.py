from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from app.schemas.rule import Rule


logger = logging.getLogger(__name__)


class RuleBuilderError(Exception):
    """Base exception for RuleBuilder errors."""
    
    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error
class RuleParsingError(RuleBuilderError):
    """Raised when AI response cannot be parsed as JSON."""


class RuleValidationError(RuleBuilderError):
    """Raised when Pydantic validation fails."""


class InvalidRuleDataError(RuleBuilderError):
    """Raised when rule data violates business logic constraints."""

class RuleBuilder:
    
    def parse_rules(self, ai_response: str) -> list[Rule]:
        try:
            parsed_data = json.loads(ai_response)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in AI response: {str(e)}"
            logger.error(error_msg)
            raise RuleParsingError(error_msg, original_error=e) from e
        
        if not isinstance(parsed_data, list):  
            error_msg = (  
                "Invalid JSON structure in AI response: expected a list of rule "  
                f"objects, got {type(parsed_data).__name__}"  
            )  
            logger.error(error_msg)  
            raise RuleParsingError(error_msg)
       
        rules = []
        for item in parsed_data:
            if not isinstance(item, dict):  
                error_msg = (  
                    "Invalid rule item in AI response: expected an object, "  
                    f"got {type(item).__name__}"  
                )  
                logger.error(error_msg)  
                raise RuleParsingError(error_msg)
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
        try:
            rule = Rule(**data)
            return rule
        except (TypeError, ValueError, PydanticValidationError) as e:
            error_msg = f"Rule validation failed: {str(e)}"
            logger.warning(error_msg)
            raise RuleValidationError(error_msg, original_error=e) from e
