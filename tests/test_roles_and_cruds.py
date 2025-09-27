def test_admin_can_create_topic(client, admin_headers):
    payload = {"name": "Nutrition", "slug": "nutrition", "is_active": True}
    r = client.post("/topics", headers=admin_headers, json=payload)
    assert r.status_code in (200, 201), r.text
    topic = r.json()
    assert topic["name"] == "Nutrition"
    assert topic["is_active"] is True


def test_non_admin_cannot_create_topic(client, user_headers):
    payload = {"name": "Football", "slug": "football", "is_active": True}
    r = client.post("/topics", headers=user_headers, json=payload)
    assert r.status_code == 403
    assert r.json()["detail"].lower().startswith("admin")


def test_admin_can_create_tip(client, admin_headers):
    r = client.post("/topics", headers=admin_headers,
                    json={"name": "Manga", "slug": "manga", "is_active": True})
    assert r.status_code in (200, 201), r.text
    topic_id = r.json()["id"]

    tip_payload = {
        "topic_id": topic_id,
        "title": "Stay hydrated during workouts",
        "body": "Water improves endurance and temperature regulation.",
        "source_url": "https://example.com/water"
    }
    r = client.post("/tips", headers=admin_headers, json=tip_payload)
    assert r.status_code in (200, 201), r.text
    tip = r.json()
    assert tip["topic_id"] == topic_id
    assert tip["title"] == tip_payload["title"]


def test_non_admin_cannot_create_tip(client, user_headers):
    admin_login = client.post(
        "/auth/login", json={"email": "admin@test.local", "password": "123456"})
    admin_headers2 = {
        "Authorization": f"Bearer {admin_login.json()['access_token']}"}
    r = client.post("/topics", headers=admin_headers2,
                    json={"name": "Sci", "slug": "sci", "is_active": True})
    topic_id = r.json()["id"]

    r = client.post("/tips", headers=user_headers, json={
        "topic_id": topic_id,
        "title": "Only admins can write tips",
        "body": "This should be forbidden",
        "source_url": "https://example.com/forbidden"
    })
    assert r.status_code == 403
