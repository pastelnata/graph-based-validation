"""Routes for cross-field validation."""

import logging
import os
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from app.schemas.validation_request import ValidationRequest
from app.schemas.validation_response import ValidationResponse
from app.services.graph.graph_builder import GraphBuilder
from app.services.graph.graph_validator import GraphValidator
from app.services.rule_generation.ai_service import AIService, AIServiceError
from app.services.rule_generation.prompt_builder import PromptBuilder
from app.services.rule_generation.prompt_template import TEMPLATE
from app.services.rule_generation.rule_builder import RuleBuilder, RuleBuilderError


router = APIRouter(prefix="/cross-field-validation", tags=["cross-field-validation"])

logger = logging.getLogger(__name__)

PROMPT_BUILDER = PromptBuilder(TEMPLATE)
RULE_BUILDER = RuleBuilder()
GRAPH_BUILDER = GraphBuilder()


@lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    """Initialize AIService"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set")
        raise HTTPException(
            status_code=503,
            detail="AI service is unavailable"
        )

    try:
        return AIService(api_key)
    except AIServiceError as error:
        logger.error("Failed to initialize AI service: %s", error)
        raise HTTPException(
            status_code=503,
            detail="AI service is unavailable"
        ) from error


@router.post("/", response_model=ValidationResponse)
async def cross_field_validation(
    request: ValidationRequest,
) -> ValidationResponse:
    """Endpoint for cross-field validation."""
    if not request.properties or len(request.properties) < 1:
        logger.warning("Validation request received with insufficient properties")
        raise HTTPException(
            status_code=400,
            detail="Request must contain at least one property"
        )

    genome_type = request.properties[0].genome_type

    logger.info("Loading graph for genome type: %s.", genome_type)
    graph = GRAPH_BUILDER.load_graph(genome_type=genome_type)

    logger.info("Generating graph for %s.", genome_type)

    if graph is None:
        try:
            property_names = [prop.name for prop in request.properties]
            prompt = PROMPT_BUILDER.build_prompt(property_names)
            ai_service = get_ai_service()
            ai_response = ai_service.generate_rules(prompt)
            rules = RULE_BUILDER.parse_rules(ai_response)
            graph = GRAPH_BUILDER.build_graph(rules, genome_type)
            logger.info("Graph for genome type %s built successfully", genome_type)
        except (AIServiceError, RuleBuilderError) as error:
            logger.error(
                "Failed to generate graph for genome type %s: %s",
                genome_type,
                error
            )
            raise HTTPException(
                status_code=503,
                detail=(
                    "Rule generation temporarily unavailable. "
                    "Please retry shortly."
                )
            ) from error

    logger.info("Traversing graph...")
    validator = GraphValidator()
    errors = validator.validate(request.properties, graph)

    return ValidationResponse(errors=errors)
