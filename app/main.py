"""FastAPI application entrypoint."""

from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI

from app.routers.graphs import router as graphs_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(graphs_router)


@app.get("/")
async def root():
    """Health-check/root endpoint."""
    return {"message": "Hello World!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)