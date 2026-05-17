"""FastAPI application entrypoint."""

import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from app.routers.cross_field_validation import (
    router as cross_field_router
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cross-Field Validation API",
    description="Validation of genome properties against cross-field rules",
    version="1.0.0"
)

app.include_router(cross_field_router)


@app.get("/")
async def root():
    """Health-check/root endpoint."""
    return {"status": "healthy", "message": "Cross-Field Validation API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
