"""Validation runtime de l'étage 2 - route /chat/message.

Teste les cas reels :
1. Inscription + login -> token
2. Cas comptabilite avec referentiel explicite
3. Cas finance sans referentiel -> clarification
4. Cas hors domaine -> clarification
5. Cas sans token -> 401
"""

import sys
import uuid

import httpx

BASE_URL = "http://127.0.0.1:8000"
results = []


def check(name: str, condition: bool, detail: str = ""):
    status = "[OK]" if condition else "[FAIL]"
    results.append((name, condition, detail))
    print(f"{status} {name}" + (f" - {detail}" if detail and not condition else ""))


def main():
    client = httpx.Client(base_url=BASE_URL, timeout=60.0)

    # 1. Health check
    try:
        r = client.get("/health")
        check("GET /health", r.status_code == 200 and r.json().get("status") == "ok", f"status={r.status_code}")
    except Exception as e:
        check("GET /health", False, str(e))
        print("\n[FAIL] Serveur non joignable. Lance d'abord uvicorn.")
        sys.exit(1)

    # 2. Inscription d'un utilisateur de test
    email = f"validation-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"
    payload = {
        "email": email,
        "password": password,
        "role": "etudiant",
        "filiere": "Comptabilite",
        "annee": "2025",
    }
    r = client.post("/auth/register", json=payload)
    check("POST /auth/register", r.status_code == 201, f"status={r.status_code}, body={r.text[:200]}")

    # 3. Login -> token
    r = client.post("/auth/login", json={"email": email, "password": password})
    check("POST /auth/login", r.status_code == 200, f"status={r.status_code}, body={r.text[:200]}")
    if r.status_code != 200:
        print("\n[FAIL] Impossible d'obtenir un token. Arret.")
        sys.exit(1)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Cas sans token -> 401
    r = client.post("/chat/message", json={"question": "explique le bilan"})
    check("POST /chat/message sans token -> 401", r.status_code == 401, f"status={r.status_code}")

    # 5. Cas comptabilite avec referentiel explicite
    r = client.post(
        "/chat/message",
        json={"question": "explique-moi le bilan comptable en OHADA"},
        headers=headers,
    )
    body = r.json()
    check(
        "Cas comptabilite OHADA -> reponse generee",
        r.status_code == 200 and body.get("reponse") is not None,
        f"status={r.status_code}, clarification={body.get('clarification_demandee')}, domaine={body.get('domaine')}",
    )
    if body.get("reponse"):
        print(f"   -> Reponse ({len(body['reponse'])} chars): {body['reponse'][:150]}...")
    print(f"   -> Domaine: {body.get('domaine')}, Sous-theme: {body.get('sous_theme')}, Referentiel: {body.get('referentiel')}")

    # 6. Cas finance sans referentiel -> clarification
    r = client.post(
        "/chat/message",
        json={"question": "comment calculer la VAN"},
        headers=headers,
    )
    body = r.json()
    check(
        "Cas finance sans referentiel -> clarification",
        r.status_code == 200 and body.get("clarification_demandee") is True,
        f"status={r.status_code}, clarification={body.get('clarification_demandee')}, domaine={body.get('domaine')}",
    )
    print(f"   -> Referentiels proposes: {body.get('referentiels_proposes')}")
    print(f"   -> Sous-themes proposes: {body.get('question_sous_themes')}")

    # 7. Cas hors domaine -> clarification
    r = client.post(
        "/chat/message",
        json={"question": "raconte-moi une blague"},
        headers=headers,
    )
    body = r.json()
    check(
        "Cas hors domaine -> clarification",
        r.status_code == 200 and body.get("clarification_demandee") is True,
        f"status={r.status_code}, clarification={body.get('clarification_demandee')}, domaine={body.get('domaine')}",
    )

    # 8. Cas comptabilite sans referentiel -> clarification
    r = client.post(
        "/chat/message",
        json={"question": "explique le bilan"},
        headers=headers,
    )
    body = r.json()
    check(
        "Cas comptabilite sans referentiel -> clarification",
        r.status_code == 200 and body.get("clarification_demandee") is True,
        f"status={r.status_code}, clarification={body.get('clarification_demandee')}, domaine={body.get('domaine')}",
    )
    print(f"   -> Referentiels proposes: {body.get('referentiels_proposes')}")

    # Resume
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"RESULTAT : {passed}/{total} verifications passees")
    if passed == total:
        print("[OK] VALIDATION RUNTIME ETAGE 2 : COMPLETE")
    else:
        print("[FAIL] DES VERIFICATIONS ONT ECHOUE")
        for name, ok, detail in results:
            if not ok:
                print(f"   [FAIL] {name}: {detail}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())