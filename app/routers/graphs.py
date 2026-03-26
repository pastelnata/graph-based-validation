"""Routes for working with genome properties."""

import logging

from fastapi import APIRouter

from app.schemas.genome_properties import GenomeProperty
from app.services.rule_generation.prompt_builder import PromptBuilder
from app.services.rule_generation.prompt_template import TEMPLATE

router = APIRouter(prefix="/graphs", tags=["graphs"])

PROMPT_BUILDER = PromptBuilder(TEMPLATE)

logger = logging.getLogger(__name__)


# TODO: REPLACE THE RETURN WITH THE ACTUAL GRAPH MODEL
@router.post("/", response_model=str)
async def build_graph(
    genome_properties: list[GenomeProperty]
) -> str:
    """Return graph for the given properties."""
    property_names = [prop.name for prop in genome_properties]
    prompt = PROMPT_BUILDER.build_prompt(property_names)
    logger.debug("Generated prompt length: %d", len(prompt))
    # TODO: send prompt to AIService, build graph from response, and return it
    return "Generated graph"
