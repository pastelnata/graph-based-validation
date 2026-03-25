"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.routers.graphs import router as graphs_router

app = FastAPI()

app.include_router(graphs_router)


@app.get("/")
async def root():
    """Health-check/root endpoint."""
    return {"message": "Hello World!"}
