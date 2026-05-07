"""Routes for working with genome properties."""

import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.genome_properties import GenomeProperty
from app.services.rule_generation.prompt_builder import PromptBuilder
from app.services.rule_generation.prompt_template import TEMPLATE
from app.services.rule_generation.rule_builder import (
    RuleBuilder,
    RuleParsingError,
    RuleValidationError,
)

router = APIRouter(prefix="/graphs", tags=["graphs"])

PROMPT_BUILDER = PromptBuilder(TEMPLATE)
RULE_BUILDER = RuleBuilder()

# Lazy initialization of AI_SERVICE
AI_SERVICE = None

logger = logging.getLogger(__name__)


# Define the request model inline if needed
class GraphRequest(BaseModel):
    """Request model for graph building endpoint."""
    genome_properties: list[GenomeProperty]


def get_ai_service():
    """Lazily initialize AI_SERVICE on first use."""
    global AI_SERVICE
    
    if AI_SERVICE is None:
        from app.services.rule_generation.ai_service import AIService
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please set it before starting the application."
            )
        
        try:
            AI_SERVICE = AIService(api_key)
            logger.info("AIService initialized successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AIService: {str(e)}") from e
    
    return AI_SERVICE


@router.post("/", response_model=dict[str, Any])
async def build_graph(request: GraphRequest) -> dict[str, Any]:
    """
    Build validation graph for the given properties.

    Process:
    1. Extract property names and create a prompt
    2. Send prompt to Gemini AI with genome attribute context
    3. Parse AI response into Rule objects
    4. Return graph containing rules and metadata

    Args:
        request: GraphRequest containing list of genome properties

    Returns:
        Dictionary containing:
        - rules: List of Rule objects in dict format
        - count: Number of rules generated
        - status: Success status
        - properties: List of property names

    Raises:
        HTTPException: If any step in the pipeline fails
    """
    try:
        # Get AI service (initialized lazily)
        ai_service = get_ai_service()
        
        # Extract genome properties from request
        genome_properties = request.genome_properties
        
        # Step 1: Build prompt from property names
        property_names = [prop.name for prop in genome_properties]
        prompt = PROMPT_BUILDER.build_prompt(property_names)
        logger.debug("Generated prompt length: %d", len(prompt))

        # Step 2: Prepare genome attributes context
        genome_attributes = _prepare_genome_attributes(genome_properties)

        # Step 3: Send to AI Service
        logger.info("Calling Gemini API to generate validation rules")
        ai_response = ai_service.generate_rules(prompt, genome_attributes)
        logger.debug("AI response received, length: %d", len(ai_response))

        # Step 4: Parse AI response into Rule objects
        rules = RULE_BUILDER.get_rules(ai_response)
        logger.info("Successfully parsed %d rules from AI response", len(rules))

        # Step 5: Build response
        response = {
            "status": "success",
            "rules": [rule.model_dump() for rule in rules],
            "count": len(rules),
            "properties": property_names,
        }
        return response

    except RuleParsingError as e:
        error_msg = f"Rule parsing error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=422, detail=error_msg) from e

    except RuleValidationError as e:
        error_msg = f"Rule validation error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=422, detail=error_msg) from e

    except RuntimeError as e:
        error_msg = str(e)
        logger.error(error_msg)
        raise HTTPException(status_code=503, detail=error_msg) from e

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg) from e


def _prepare_genome_attributes(
    properties: list[GenomeProperty],
) -> dict[str, Any]:
    """
    Prepare genome attributes in a structured format for AI analysis.

    Args:
        properties: List of GenomeProperty objects

    Returns:
        Dictionary with schema and data for AI context
    """
    attributes_schema = {}
    attributes_data = {}

    for prop in properties:
        attr_key = prop.name

        # Build schema entry
        attributes_schema[attr_key] = {
            "type": prop.property_type,
            "genome_type": prop.genome_type,
            "unit": prop.unit,
        }

        # Store sample data
        attributes_data[attr_key] = {
            "value": prop.value,
            "unit": prop.unit,
            "type": prop.property_type,
        }

    return {
        "schema": attributes_schema,
        "sample_data": attributes_data,
        "count": len(properties),
    }