"""Runtime validation of the RAG / documents layer against a live server.

Checks:
1. Health endpoint
2. Register + login -> token (student + professor)
3. Create conversation
4. Upload a TXT document in the conversation
5. Wait for indexing to complete (poll status)
6. Ask a question about the document content -> RAG answer
7. Professor can share a document (visibilite)
8. Student cannot change visibility -> 403
9. Unsupported file type -> 400
"""

import sys
import time
import uuid

import httpx

BASE_URL = "http://127.0.0.1:8000"
results = []


def check(name: str, condition: bool, detail: str = ""):
    status = "[OK]" if condition else "[FAIL]"
    results.append((name, condition, detail))
    print(f"{status} {name}" + (f" - {detail}" if detail and not condition else ""), flush=True)


def main():
    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    # 1. Health
    try:
        r = client.get("/health")
        check("GET /health", r.status_code == 200, f"status={r.status_code}")
    except Exception as e:
        check("GET /health", False, str(e))
        print("\n[FAIL] Server unreachable. Start uvicorn first.")
        return 1

    # 2. Register + login (student)
    email = f"rag-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"
    r = client.post("/auth/register", json={
        "email": email, "password": password, "role": "etudiant",
        "filiere": "Comptabilite", "annee": "2025",
    })
    check("POST /auth/register (student)", r.status_code == 201, f"status={r.status_code} body={r.text[:150]}")
    r = client.post("/auth/login", json={"email": email, "password": password})
    check("POST /auth/login (student)", r.status_code == 200, f"status={r.status_code}")
    student_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # 2b. Register + login (professor)
    email_prof = f"ragprof-{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/auth/register", json={
        "email": email_prof, "password": password, "role": "professeur",
    })
    check("POST /auth/register (professor)", r.status_code == 201, f"status={r.status_code} body={r.text[:150]}")
    r = client.post("/auth/login", json={"email": email_prof, "password": password})
    check("POST /auth/login (professor)", r.status_code == 200, f"status={r.status_code}")
    prof_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # 3. Create conversation
    r = client.post("/conversations", headers=student_headers, json={"titre": "RAG validation"})
    check("POST /conversations", r.status_code == 201, f"status={r.status_code} body={r.text[:150]}")
    conversation_id = r.json()["id"]

    # 4. Upload TXT document
    doc_content = (
        "Le bilan comptable OHADA se compose de trois grandes masses: "
        "l'actif immobilise, l'actif circulant et la tresorerie. "
        "Le passif comprend les capitaux propres, les dettes financieres "
        "et le passif circulant. Le referentiel OHADA est applique dans "
        "les etats financiers des entreprises d'Afrique de l'Ouest."
    ).encode("utf-8")
    r = client.post(
        f"/conversations/{conversation_id}/documents",
        headers=student_headers,
        files={"file": ("cours_bilan.txt", doc_content, "text/plain")},
    )
    check("POST upload TXT document", r.status_code == 201, f"status={r.status_code} body={r.text[:200]}")
    if r.status_code != 201:
        print(f"\n[FAIL] Upload failed: {r.text}")
        return 1
    document_id = r.json()["id"]

    # 5. Indexing is synchronous: status is already final in the upload response.
    # Confirm via GET /documents/{id} that chunks were persisted.
    upload_status = r.json().get("statut_indexation")
    check("Upload response status = 'indexe'", upload_status == "indexe", f"statut={upload_status}")
    r = client.get(f"/documents/{document_id}", headers=student_headers)
    body = r.json() if r.status_code == 200 else {}
    check(
        "GET /documents/{id} -> indexed with chunks",
        r.status_code == 200 and body.get("statut_indexation") == "indexe" and body.get("nombre_chunks", 0) > 0,
        f"status={r.status_code} body={r.text[:200]}",
    )
    print(f"   -> statut: {body.get('statut_indexation')}, chunks: {body.get('nombre_chunks')}, domaine: {body.get('domaine_associe')}", flush=True)

    # 6. Ask a question about the document -> RAG mode
    r = client.post(
        "/chat/message",
        headers=student_headers,
        json={"question": "Quelles sont les grandes masses du bilan OHADA ?", "conversation_id": conversation_id},
    )
    body = r.json() if r.status_code == 200 else {}
    check(
        "POST /chat/message with document -> RAG answer",
        r.status_code == 200 and bool(body.get("reponse")),
        f"status={r.status_code} body={r.text[:200]}",
    )
    print(f"   -> mode: {body.get('mode')}, domaine: {body.get('domaine')}", flush=True)
    if body.get("reponse"):
        print(f"   -> reponse: {body['reponse'][:200]}...", flush=True)

    # 7. Professor uploads and shares a document
    r = client.post("/conversations", headers=prof_headers, json={"titre": "Prof sharing"})
    prof_conv_id = r.json()["id"]
    r = client.post(
        f"/conversations/{prof_conv_id}/documents",
        headers=prof_headers,
        files={"file": ("cours_van.txt", "La VAN est la somme des flux actualises moins l'investissement initial.".encode("utf-8"), "text/plain")},
    )
    check("Professor uploads document", r.status_code == 201, f"status={r.status_code} body={r.text[:150]}")
    prof_doc_id = r.json()["id"] if r.status_code == 201 else None

    r = client.patch(
        f"/documents/{prof_doc_id}/visibility",
        headers=prof_headers,
        json={"visibilite": "partage_classe"},
    )
    check("PATCH visibility (professor) -> 200", r.status_code == 200, f"status={r.status_code} body={r.text[:200]}")

    # 8. Student cannot change visibility
    r = client.patch(
        f"/documents/{document_id}/visibility",
        headers=student_headers,
        json={"visibilite": "partage_classe"},
    )
    check("PATCH visibility (student) -> 403", r.status_code == 403, f"status={r.status_code}")

    # 9. Unsupported file type
    r = client.post(
        f"/conversations/{conversation_id}/documents",
        headers=student_headers,
        files={"file": ("malware.exe", b"MZfake", "application/octet-stream")},
    )
    check("Upload unsupported type -> 400", r.status_code == 400, f"status={r.status_code}")

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{'=' * 60}", flush=True)
    print(f"RESULT: {passed}/{total} checks passed", flush=True)
    print("[OK] RAG RUNTIME VALIDATION: COMPLETE" if passed == total else "[FAIL] SOME CHECKS FAILED", flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
