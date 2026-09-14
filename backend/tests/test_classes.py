from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.auth.dependencies import get_current_user
from app.db.session import get_db

client = TestClient(app)


class FakeUser:
    def __init__(self, user_id: int, role: str):
        self.id = user_id
        self.role = role
        self.email = f"user{user_id}@example.com"


class DummySession:
    def __init__(self):
        self.items = []

    def add(self, obj):
        self.items.append(obj)
        return None

    def commit(self):
        return None

    def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = 1
        return None

    def query(self, *args, **kwargs):
        raise AssertionError("DummySession should not be used for these tests.")


def _override_user():
    return FakeUser(10, "professeur")


def _override_db():
    return DummySession()


def test_create_class_as_professor_returns_code(monkeypatch):
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr(
            "app.routers.classes.create_class",
            lambda db, professeur, nom: type(
                "C",
                (),
                {"id": 1, "nom": nom, "professeur_id": professeur.id, "code_invitation": "ABC12345", "created_at": None},
            )(),
        )
        response = client.post("/classes", json={"nom": "Maths"})
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["nom"] == "Maths"
        assert body["code_invitation"] == "ABC12345"
    finally:
        app.dependency_overrides.clear()


def test_create_class_as_student_is_403(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(11, "etudiant")
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post("/classes", json={"nom": "Maths"})
        assert response.status_code == 403, response.text
    finally:
        app.dependency_overrides.clear()


def test_list_classes_professor_lists_owned(monkeypatch):
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr(
            "app.routers.classes.list_classes",
            lambda db, user: [type("C", (), {"id": 1, "nom": "Maths", "professeur_id": user.id, "code_invitation": "ABC12345", "created_at": None})()],
        )
        response = client.get("/classes")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body[0]["nom"] == "Maths"
        assert "code_invitation" in body[0]
    finally:
        app.dependency_overrides.clear()


def test_list_classes_student_lists_joined(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(12, "etudiant")
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr(
            "app.routers.classes.list_classes",
            lambda db, user: [type("C", (), {"id": 2, "nom": "Physique", "professeur_id": 99, "created_at": None})()],
        )
        response = client.get("/classes")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body[0]["nom"] == "Physique"
        assert "code_invitation" not in body[0]
    finally:
        app.dependency_overrides.clear()


def test_join_class_with_valid_code(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(13, "etudiant")
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr("app.routers.classes.get_class", lambda db, classe_id: type("C", (), {"id": 7, "nom": "Biologie", "code_invitation": "ABC12345"})())
        monkeypatch.setattr("app.routers.classes.join_class", lambda db, classe, etudiant, code: type("C", (), {"id": 7, "nom": "Biologie", "code_invitation": "ABC12345"})())
        response = client.post("/classes/7/join", json={"code_invitation": "ABC12345"})
        assert response.status_code == 200, response.text
        assert response.json()["id"] == 7
    finally:
        app.dependency_overrides.clear()


def test_join_class_wrong_code_is_400(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(14, "etudiant")
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr("app.routers.classes.get_class", lambda db, classe_id: type("C", (), {"id": 7, "nom": "Biologie", "code_invitation": "ABC12345"})())
        def boom(db, classe, etudiant, code):
            raise ValueError("Invalid invitation code.")
        monkeypatch.setattr("app.routers.classes.join_class", boom)
        response = client.post("/classes/7/join", json={"code_invitation": "BAD"})
        assert response.status_code == 400, response.text
        assert "Invalid invitation code." in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_join_class_already_member_is_400(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(15, "etudiant")
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr("app.routers.classes.get_class", lambda db, classe_id: type("C", (), {"id": 7, "nom": "Biologie", "code_invitation": "ABC12345"})())
        def boom(db, classe, etudiant, code):
            raise ValueError("Already a member of this class.")
        monkeypatch.setattr("app.routers.classes.join_class", boom)
        response = client.post("/classes/7/join", json={"code_invitation": "ABC12345"})
        assert response.status_code == 400, response.text
        assert "Already a member of this class." in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_join_class_not_found_is_404(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(16, "etudiant")
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr("app.routers.classes.get_class", lambda db, classe_id: None)
        response = client.post("/classes/999/join", json={"code_invitation": "ABC12345"})
        assert response.status_code == 404, response.text
    finally:
        app.dependency_overrides.clear()


def test_join_class_as_professor_is_403(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(17, "professeur")
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post("/classes/7/join", json={"code_invitation": "ABC12345"})
        assert response.status_code == 403, response.text
    finally:
        app.dependency_overrides.clear()
