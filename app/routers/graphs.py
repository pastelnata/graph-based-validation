"""Routes for working with genome properties."""

import logging

from fastapi import APIRouter, HTTPException
from app.schemas.genome_properties import GenomeProperty
from app.schemas.rule import Rule
from app.services.rule_generation.prompt_builder import PromptBuilder
from app.services.rule_generation.prompt_template import TEMPLATE
from app.services.gemini_service import GeminiService

router = APIRouter(prefix="/graphs", tags=["graphs"])

PROMPT_BUILDER = PromptBuilder(TEMPLATE)
GEMINI_SERVICE = GeminiService()

logger = logging.getLogger(__name__)


@router.post("/", response_model=list[Rule])
async def build_graph(
    genome_properties: list[GenomeProperty]
) -> list[Rule]:
    """Return validation rules for the given properties using Gemini API."""
    try:
        property_names = [prop.name for prop in genome_properties]
        prompt = PROMPT_BUILDER.build_prompt(property_names)
        logger.debug("Generated prompt length: %d", len(prompt))
        
        # Send prompt to Gemini API
        response = GEMINI_SERVICE.query(prompt)
        logger.debug("Received response from Gemini: %s", response[:200])
        
        # Parse rules from response
        rules_data = GEMINI_SERVICE.parse_rules_json(response)
        
        # Convert to Rule objects
        rules = [Rule(**rule) for rule in rules_data]
        logger.info(f"Generated {len(rules)} rules")
        
        return rules
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API configuration error: {str(e)}")
    except Exception as e:
        logger.error(f"Error building graph: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
