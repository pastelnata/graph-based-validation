"""FastAPI application entrypoint."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    """Health-check/root endpoint."""
    return {"message": "Hello World!"}
