"""Tests for calculator routes."""
import os
from fastapi.testclient import TestClient

os.environ["DB_URL"] = "sqlite:///./test_calculators.db"

from app.main import app
from app.models.user import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_calculators():
    resp = client.get("/calculators/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 4
    domains = {c["domain"] for c in data["calculators"]}
    assert "comptabilite" in domains
    assert "finance" in domains
    assert "banque" in domains


def test_list_calculators_filtered():
    resp = client.get("/calculators/?domain=comptabilite")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["calculators"][0]["domain"] == "comptabilite"


def test_calculate_tva():
    payload = {"amount_ht": 1000, "tau": 0.2}
    resp = client.post("/calculators/comptabilite/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == 200.0
    assert data["extra"]["montant_ttc"] == 1200.0


def test_calculate_ttc_to_ht():
    payload = {"amount_ttc": 1200, "tau": 0.2}
    resp = client.post("/calculators/comptabilite/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == 1000.0


def test_calculate_van():
    payload = {"base_amount": 10000, "flows": [3000, 4000, 5000], "discount_rate": 0.1}
    resp = client.post("/calculators/finance/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "van" in data["extra"]
    assert "ica" in data["extra"]


def test_calculate_credit():
    payload = {"base_amount": 12000, "tau": 0.05, "period_months": 24}
    resp = client.post("/calculators/banque/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["extra"]["interet_simple"] == 1200.0
    assert data["extra"]["capital_final"] == 13200.0


def test_calculate_amortissement():
    payload = {"domain": "finance", "base_amount": 12000, "periods": 5, "period_years": 2, "sous_theme": "amortissement"}
    resp = client.post("/calculators/resolve", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["extra"]["dotation_annuelle"] == 2400.0


def test_calculate_van_with_sous_theme():
    payload = {"domain": "finance", "base_amount": 10000, "flows": [3000, 4000, 5000], "discount_rate": 0.1, "sous_theme": "van"}
    resp = client.post("/calculators/resolve", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "van" in data["extra"]


def test_calculate_missing_params():
    resp = client.post("/calculators/comptabilite/calculate", json={})
    assert resp.status_code == 400


def test_resolve_and_calculate():
    payload = {"domain": "comptabilite", "amount_ht": 500, "tau": 0.2}
    resp = client.post("/calculators/resolve", json=payload)
    assert resp.status_code == 200
    assert resp.json()["result"] == 100.0

