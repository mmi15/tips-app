# ==============================
# Admin and Permission Tests
# ==============================
# These tests verify access control and permissions for
# creating topics and tips. Only admin users should be
# allowed to perform these operations.

def test_admin_can_create_topic(client, admin_headers):
    """
    Verify that an admin user can successfully create a topic.
    """
    payload = {"name": "Nutrition", "slug": "nutrition", "is_active": True}

    # Admin creates a new topic
    r = client.post("/topics", headers=admin_headers, json=payload)
    assert r.status_code in (200, 201), r.text

    # Validate response data
    topic = r.json()
    assert topic["name"] == "Nutrition"
    assert topic["is_active"] is True


def test_non_admin_cannot_create_topic(client, user_headers):
    """
    Verify that a non-admin user cannot create topics.
    The endpoint should return a 403 Forbidden response.
    """
    payload = {"name": "Football", "slug": "football", "is_active": True}

    # Regular user attempts to create a topic
    r = client.post("/topics", headers=user_headers, json=payload)

    # Ensure the request is forbidden
    assert r.status_code == 403
    assert r.json()["detail"].lower().startswith("admin")


def test_admin_can_create_tip(client, admin_headers):
    """
    Verify that an admin can create a tip under a topic.
    """
    # 1) Create a topic first
    r = client.post(
        "/topics",
        headers=admin_headers,
        json={"name": "Manga", "slug": "manga", "is_active": True},
    )
    assert r.status_code in (200, 201), r.text
    topic_id = r.json()["id"]

    # 2) Create a tip associated with that topic
    tip_payload = {
        "topic_id": topic_id,
        "title": "Stay hydrated during workouts",
        "body": "Water improves endurance and temperature regulation.",
        "source_url": "https://example.com/water",
    }
    r = client.post("/tips", headers=admin_headers, json=tip_payload)
    assert r.status_code in (200, 201), r.text

    # Validate response
    tip = r.json()
    assert tip["topic_id"] == topic_id
    assert tip["title"] == tip_payload["title"]


def test_non_admin_cannot_create_tip(client, user_headers):
    """
    Verify that non-admin users cannot create tips.
    """
    # Log in as admin to create a topic
    admin_login = client.post(
        "/auth/login", json={"email": "admin@test.local", "password": "123456"}
    )
    admin_headers2 = {
        "Authorization": f"Bearer {admin_login.json()['access_token']}"
    }

    # Admin creates a topic
    r = client.post(
        "/topics",
        headers=admin_headers2,
        json={"name": "Sci", "slug": "sci", "is_active": True},
    )
    topic_id = r.json()["id"]

    # Regular user tries to create a tip in that topic
    r = client.post(
        "/tips",
        headers=user_headers,
        json={
            "topic_id": topic_id,
            "title": "Only admins can write tips",
            "body": "This should be forbidden",
            "source_url": "https://example.com/forbidden",
        },
    )

    # Request should be forbidden
    assert r.status_code == 403
