"""Routes for working with genome properties."""

import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.validation_request import ValidationRequest
from app.services.rule_generation.ai_service import (
    AIService,
    AIServiceError,
)
from app.services.rule_generation.prompt_builder import PromptBuilder
from app.services.rule_generation.prompt_template import TEMPLATE
from app.services.rule_generation.rule_builder import (
    RuleBuilder,
    RuleParsingError,
    RuleValidationError,
)

router = APIRouter(prefix="/graphs", tags=["graphs"])

logger = logging.getLogger(__name__)

PROMPT_BUILDER = PromptBuilder(TEMPLATE)
RULE_BUILDER = RuleBuilder()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set"
    )

AI_SERVICE = AIService(api_key)


@router.post("/", response_model=dict[str, Any])
async def build_graph(
    request: ValidationRequest,
) -> dict[str, Any]:
    """
    generate rules from properties
    """

    try:
        genome_properties = request.properties

        property_names = [
            prop.name
            for prop in genome_properties
        ]

        prompt = PROMPT_BUILDER.build_prompt(
            property_names
        )

        logger.info(
            "Calling Gemini API to generate rules"
        )

        ai_response = AI_SERVICE.generate_rules(prompt)

        rules = RULE_BUILDER.get_rules(ai_response)

        logger.info(
            "Successfully generated %d rules",
            len(rules),
        )

        return {
            "status": "success",
            "rules": [
                rule.model_dump()
                for rule in rules
            ],
            "count": len(rules),
            "properties": property_names,
        }

    except RuleParsingError as error:
        logger.error(
            "Rule parsing error: %s",
            str(error),
        )

        raise HTTPException(
            status_code=422,
            detail=f"Rule parsing error: {str(error)}",
        ) from error

    except RuleValidationError as error:
        logger.error(
            "Rule validation error: %s",
            str(error),
        )

        raise HTTPException(
            status_code=422,
            detail=(
                f"Rule validation error: "
                f"{str(error)}"
            ),
        ) from error

    except AIServiceError as error:
        logger.error(
            "AI service error: %s",
            str(error),
        )

        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.error(
            "Unexpected error",
            exc_info=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(error)}",
        ) from error
