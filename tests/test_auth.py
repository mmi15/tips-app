# ==============================
# Authentication Tests
# ==============================
# These tests verify the registration, login, and "me" endpoints
# of the FastAPI application. They use the shared `client` fixture
# from the test setup to simulate HTTP requests.

def test_register_and_login(client):
    """
    Test user registration and login process.
    Ensures that a new user can register and then log in successfully.
    """
    email = "auth1@test.local"

    # Register a new user
    r = client.post("/auth/register",
                    json={"email": email, "password": "123456"})
    assert r.status_code in (200, 201)

    # Log in with the same credentials
    r = client.post("/auth/login", json={"email": email, "password": "123456"})
    assert r.status_code == 200

    # Validate that the response contains a valid token
    data = r.json()
    assert "access_token" in data and data["token_type"] == "bearer"


def test_me_returns_user(client):
    """
    Test the /auth/me endpoint.
    Ensures that an authenticated user can retrieve their own data.
    """
    email = "auth2@test.local"

    # Register and log in to obtain a token
    client.post("/auth/register", json={"email": email, "password": "123456"})
    r = client.post("/auth/login", json={"email": email, "password": "123456"})
    token = r.json()["access_token"]

    # Call the /auth/me endpoint with the authorization header
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200

    # Validate the returned user data
    me = r.json()
    assert me["email"] == email
    assert "is_admin" in me
