import os
import pathlib
import shutil
import time
import pytest
from app.main import app
from app.db.models import Base
from app.db.session import engine
from fastapi.testclient import TestClient

# ==============================
# Test Environment Configuration
# ==============================
# This file sets up a temporary SQLite database and
# provides reusable pytest fixtures for testing the FastAPI app.

# ------------------------------
# Environment setup
# ------------------------------
TEST_DB_PATH = pathlib.Path("./tips.db")

# Use a temporary SQLite database file for testing
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

# Default values for required environment variables
os.environ.setdefault("JWT_SECRET", "testingsecret")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.local")


# ------------------------------
# Database preparation fixture
# ------------------------------
@pytest.fixture(scope="session", autouse=True)
def _prepare_db():
    """
    Automatically runs once per test session.
    Creates a clean database before tests and removes it afterward.
    """
    # If a previous test DB exists, try to remove or rename it
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:
            # If the file is locked, rename it instead
            TEST_DB_PATH.rename(TEST_DB_PATH.with_suffix(".old"))

    # Create a new database schema from models
    Base.metadata.create_all(bind=engine)
    yield
    # After tests complete, attempt to delete the DB file
    for _ in range(3):
        try:
            if TEST_DB_PATH.exists():
                TEST_DB_PATH.unlink()
            break
        except PermissionError:
            # Retry if the file is temporarily locked
            time.sleep(0.2)


# ------------------------------
# FastAPI TestClient fixture
# ------------------------------
@pytest.fixture(scope="session")
def client():
    """
    Provides a shared FastAPI TestClient for making HTTP requests.
    """
    with TestClient(app) as c:
        yield c


# ==============================
# Helper functions
# ==============================
# These functions simplify common testing operations
# such as user registration and authentication.

def _register(client, email, pwd="123456"):
    """
    Helper to register a new user.
    Asserts the registration request succeeds and returns the response JSON.
    """
    r = client.post("/auth/register", json={"email": email, "password": pwd})
    assert r.status_code in (200, 201), r.text
    return r.json()


def _login(client, email, pwd="123456"):
    """
    Helper to log in an existing user.
    Returns the authorization header for authenticated requests.
    """
    r = client.post("/auth/login", json={"email": email, "password": pwd})
    assert r.status_code == 200, r.text
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


# ------------------------------
# Authenticated client fixtures
# ------------------------------
@pytest.fixture
def admin_headers(client):
    """
    Registers and logs in the admin user.
    Returns the headers required for authorized admin requests.
    """
    _register(client, os.environ.get("ADMIN_EMAIL", "admin@test.local"))
    return _login(client, os.environ.get("ADMIN_EMAIL", "admin@test.local"))


@pytest.fixture
def user_headers(client):
    """
    Registers and logs in a regular user.
    Returns the headers required for authorized user requests.
    """
    _register(client, "user@test.local")
    return _login(client, "user@test.local")
