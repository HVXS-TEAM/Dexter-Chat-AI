"""Diagnostic end-to-end de l'ecran Chat (auth, conversation, upload, chat).

Usage :
    python scripts/upload_test.py [base_url]
    (base_url par defaut : http://127.0.0.1:8000)

Le script s'adresse a l'API REELLE (uvicorn), pas a un TestClient : il mesure
donc exactement ce que voit le navigateur. Il cree le compte de test si besoin,
puis enchaine :

  1. login
  2. creation d'une conversation
  3. upload d'une image PNG   (met en evidence le support OCR)
  4. upload d'un fichier .txt (verifie le chemin nominal)
  5. POST /chat/message       (verifie la generation LLM)

Chaque appel affiche le code HTTP reel et la reponse brute.
"""
from __future__ import annotations

import sys

import httpx

DEFAULT_API = "http://127.0.0.1:8000"
CREDS = {"email": "etudiant.test@dexter.dev", "password": "Etudiant2026!"}
REGISTER = {
    "email": CREDS["email"],
    "password": CREDS["password"],
    "role": "etudiant",
    "langue_preferee": "fr",
    "filiere": "Comptabilité",
    "annee": "BTS 2",
}

PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"
)
TXT_BYTES = "Question de test : comment calculer la TVA sur 1000 euros ?\n".encode("utf-8")


def show(label: str, response: httpx.Response) -> None:
    body = response.text.replace("\r", " ").replace("\n", " ")[:400]
    print(f"{label}: HTTP {response.status_code} -> {body}")


def safe(label: str, call):
    """Execute un appel HTTP en isolant les erreurs (le diagnostic continue)."""
    try:
        response = call()
    except httpx.TimeoutException:
        print(f"{label}: TIMEOUT (aucune reponse HTTP dans la limite du client)")
        return None
    except httpx.HTTPError as exc:
        print(f"{label}: ERREUR RESEAU -> {type(exc).__name__}: {exc}")
        return None
    show(label, response)
    return response


def main(argv: list[str]) -> int:
    api = argv[1] if len(argv) > 1 else DEFAULT_API
    print(f"=== DIAGNOSTIC CHAT / UPLOAD (API reelle) : {api} ===")

    with httpx.Client(base_url=api, timeout=90.0) as client:
        safe("HEALTH", lambda: client.get("/health"))
        safe("REGISTER", lambda: client.post("/auth/register", json=REGISTER))

        login = safe("LOGIN", lambda: client.post("/auth/login", json=CREDS))
        if login is None or login.status_code != 200:
            print("=> AUTH IMPOSSIBLE : la suite du diagnostic est inutile.")
            return 1
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        created = safe(
            "CREATE_CONVERSATION",
            lambda: client.post("/conversations", json={"titre": "Diag upload"}, headers=headers),
        )
        if created is None or created.status_code != 201:
            print("=> CREATION DE CONVERSATION IMPOSSIBLE.")
            return 1
        conversation_id = created.json()["id"]
        print(f"CONVERSATION_ID = {conversation_id}")

        safe(
            "UPLOAD_PNG (image)",
            lambda: client.post(
                f"/conversations/{conversation_id}/documents",
                files={"file": ("diag_image.png", PNG_BYTES, "image/png")},
                headers=headers,
            ),
        )

        safe(
            "UPLOAD_TXT (texte)",
            lambda: client.post(
                f"/conversations/{conversation_id}/documents",
                files={"file": ("diag_note.txt", TXT_BYTES, "text/plain")},
                headers=headers,
            ),
        )

        safe(
            "LIST_DOCUMENTS",
            lambda: client.get(f"/conversations/{conversation_id}/documents", headers=headers),
        )

        safe(
            "CHAT_MESSAGE",
            lambda: client.post(
                "/chat/message",
                json={
                    "question": "Peux-tu me rappeler la formule de calcul de la TVA ?",
                    "conversation_id": conversation_id,
                },
                headers=headers,
            ),
        )

        safe(
            "CHAT_STREAM",
            lambda: client.post(
                "/chat/stream",
                json={
                    "question": "Qu'est-ce que le bilan comptable ?",
                    "conversation_id": conversation_id,
                },
                headers=headers,
            ),
        )

    print("=== FIN DIAGNOSTIC ===")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

