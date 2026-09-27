import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.services.sandbox import local as local_sandbox_module
from app.services.sandbox.local import LocalSandbox


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    # Isolated in-memory SQLite DB per test.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Isolated temp directory per test, so tests never touch the real
    # workspaces/ directory and never interfere with each other.
    tmp_root = tempfile.mkdtemp(prefix="devpilot-test-workspaces-")
    test_sandbox = LocalSandbox(tmp_root)

    app.dependency_overrides[get_db] = override_get_db
    local_sandbox_module.local_sandbox = test_sandbox
    # The routers imported `local_sandbox` by reference at import time, so
    # patch it in each module that holds its own reference too.
    import app.api.files as files_module
    import app.api.projects as projects_module

    files_module.local_sandbox = test_sandbox
    projects_module.local_sandbox = test_sandbox

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
