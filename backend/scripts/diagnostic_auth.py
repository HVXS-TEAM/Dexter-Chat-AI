"""Diagnostic auth : crée (si besoin) et vérifie les comptes de test via l'API réelle.

Exécution : backend/.venv/Scripts/python.exe scripts/diagnostic_auth.py
Utilise la base de dev configurée dans backend/.env (DB_URL). Aucune donnée mockée.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STUDENT = {
    "email": "etudiant.test@dexter.dev",
    "password": "Etudiant2026!",
    "role": "etudiant",
    "langue_preferee": "fr",
    "filiere": "Comptabilité",
    "annee": "BTS 2",
}
PROF = {
    "email": "professeur.test@dexter.dev",
    "password": "Professeur2026!",
    "role": "professeur",
    "langue_preferee": "fr",
    "etablissement": "Lycée de test",
    "matieres_enseignees": ["Comptabilité", "Finance"],
}


def show(label: str, response) -> None:
    print(f"{label}: HTTP {response.status_code} -> {response.text[:200]}")


def main() -> None:
    print("=== DIAGNOSTIC AUTH (API réelle, base de dev) ===")
    for name, payload in (("REGISTER_ETUDIANT", STUDENT), ("REGISTER_PROFESSEUR", PROF)):
        show(name, client.post("/auth/register", json=payload))

    for name, payload in (("LOGIN_ETUDIANT", STUDENT), ("LOGIN_PROFESSEUR", PROF)):
        response = client.post(
            "/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        )
        show(name, response)
        if response.status_code == 200:
            tokens = response.json()
            me = client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            show(f"ME ({payload['role']})", me)


if __name__ == "__main__":
    main()