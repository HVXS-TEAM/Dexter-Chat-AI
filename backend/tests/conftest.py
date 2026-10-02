"""Shared pytest configuration for the Dexter backend tests.

Every test session uses its own temporary SQLite database. The environment
variable is set before importing the application so SQLAlchemy cannot connect
to the developer PostgreSQL database during collection.
"""

from __future__ import annotations

import os
import tempfile
import time
import uuid
import warnings
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / f"dexter_test_{uuid.uuid4().hex}.db"
_TEST_DATABASE_URL = f"sqlite:///{_TEST_DATABASE_PATH.as_posix()}"
os.environ["DB_URL"] = _TEST_DATABASE_URL

from app.db.session import engine as app_engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


def _remove_database_file(path: Path) -> None:
    """Delete the temporary database file, retrying briefly on Windows.

    If the file is still locked after ~3 seconds, a visible warning carrying
    the orphaned path is emitted; the error is never silently swallowed.
    """
    for _attempt in range(10):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            time.sleep(0.3)
    warnings.warn(
        f"Could not delete the temporary test database: {path}. "
        "It remains in the system temp directory; remove it manually.",
        RuntimeWarning,
        stacklevel=2,
    )


@pytest.fixture(scope="session", autouse=True)
def test_database():
    """Create a disposable database for the whole pytest session."""
    engine = create_engine(
        _TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    try:
        yield testing_session
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        # app.db.session.engine points at the same temporary URL: routes or
        # tests that used it directly may still hold the SQLite file open,
        # which blocks deletion on Windows.
        app_engine.dispose()
        _remove_database_file(_TEST_DATABASE_PATH)


@pytest.fixture(autouse=True)
def isolated_test_database(test_database):
    """Use a clean schema and inject the test session for every test."""
    engine = test_database.kw["bind"]

    def override_get_db():
        db = test_database()
        try:
            yield db
        finally:
            db.close()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        # Only remove the override installed by this fixture. Some tests
        # install their own get_db overrides and clean up after themselves.
        if app.dependency_overrides.get(get_db) is override_get_db:
            app.dependency_overrides.pop(get_db, None)
