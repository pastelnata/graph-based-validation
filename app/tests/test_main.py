"""Tests for the main application."""

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_read_root():
    """Test health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World!"}


def test_build_graph_missing_api_key(monkeypatch):
    """Test that the endpoint fails gracefully when API key is missing."""
    import os
    # Remove the GEMINI_API_KEY if it exists
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    payload = {
        "properties": [
            {
                "property_type": "STANDARD",
                "name": "age",
                "value": "25",
                "unit": "years",
                "genome_type": "integer"
            },
            {
                "property_type": "STANDARD",
                "name": "weight",
                "value": "70",
                "unit": "kg",
                "genome_type": "float"
            }
        ]
    }
    
    response = client.post("/graphs/", json=payload)
    # Should fail because no API key is set
    assert response.status_code == 500
