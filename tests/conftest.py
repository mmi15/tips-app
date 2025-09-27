import os
import pathlib
import shutil
import time
import pytest
from app.main import app
from app.db.models import Base
from app.db.session import engine
from fastapi.testclient import TestClient

TEST_DB_PATH = pathlib.Path("./tips.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ.setdefault("JWT_SECRET", "testingsecret")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.local")


@pytest.fixture(scope="session", autouse=True)
def _prepare_db():
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:

            TEST_DB_PATH.rename(TEST_DB_PATH.with_suffix(".old"))

    Base.metadata.create_all(bind=engine)
    yield
    #
    for _ in range(3):
        try:
            if TEST_DB_PATH.exists():
                TEST_DB_PATH.unlink()
            break
        except PermissionError:
            time.sleep(0.2)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

# Helpers


def _register(client, email, pwd="123456"):
    r = client.post("/auth/register", json={"email": email, "password": pwd})
    assert r.status_code in (200, 201), r.text
    return r.json()


def _login(client, email, pwd="123456"):
    r = client.post("/auth/login", json={"email": email, "password": pwd})
    assert r.status_code == 200, r.text
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture
def admin_headers(client):
    _register(client, os.environ.get("ADMIN_EMAIL", "admin@test.local"))

    return _login(client, os.environ.get("ADMIN_EMAIL", "admin@test.local"))


@pytest.fixture
def user_headers(client):
    _register(client, "user@test.local")
    return _login(client, "user@test.local")
