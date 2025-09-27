def test_register_and_login(client):
    email = "auth1@test.local"
    r = client.post("/auth/register",
                    json={"email": email, "password": "123456"})
    assert r.status_code in (200, 201)

    r = client.post("/auth/login", json={"email": email, "password": "123456"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data and data["token_type"] == "bearer"


def test_me_returns_user(client):
    email = "auth2@test.local"
    client.post("/auth/register", json={"email": email, "password": "123456"})
    r = client.post("/auth/login", json={"email": email, "password": "123456"})
    token = r.json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == email
    assert "is_admin" in me
