"""FastAPI application entrypoint."""

import logging

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from app.routers.cross_field_validation import router as cross_field_router #pylint: disable=wrong-import-position

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(cross_field_router)


@app.get("/")
async def root():
    """Health-check/root endpoint."""
    return {"message": "Hello World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
