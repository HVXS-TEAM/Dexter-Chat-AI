"""Tests for the public domain catalogue route (GET /domains)."""
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_domains_returns_catalogue():
    response = client.get("/domains")
    assert response.status_code == 200, response.text
    data = response.json()
    ids = [item["id"] for item in data]
    assert "comptabilite" in ids
    assert "finance" in ids
    for item in data:
        assert isinstance(item["label"], str) and item["label"]
        assert isinstance(item["keywords"], list)
        assert isinstance(item["sous_themes"], list)
        assert isinstance(item["referentiels"], list)


def test_get_domains_comptabilite_has_referentiels():
    response = client.get("/domains")
    data = response.json()
    comptabilite = next(item for item in data if item["id"] == "comptabilite")
    assert comptabilite["referentiels"], "comptabilite doit exposer ses referentiels"
