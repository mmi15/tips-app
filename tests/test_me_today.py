# ==============================
# Integration Test: User Subscription and Daily Tip Delivery
# ==============================
# This test covers the end-to-end flow where:
# 1. An admin creates a topic and adds tips to it.
# 2. A user subscribes to that topic.
# 3. The user retrieves their daily tips via /me/tips/today.

def test_user_subscribes_and_gets_today_tip(client, admin_headers, user_headers):
    """
    End-to-end test for the daily tips delivery flow.
    Ensures that a user who subscribes to a topic receives tips for that topic.
    """

    # ------------------------------
    # 1) Admin creates a topic
    # ------------------------------
    r = client.post(
        "/topics",
        headers=admin_headers,
        json={"name": "Daily", "slug": "daily", "is_active": True},
    )
    assert r.status_code in (200, 201)
    topic_id = r.json()["id"]

    # ------------------------------
    # 2) Admin adds tips under that topic
    # ------------------------------
    for i in range(2):
        r = client.post(
            "/tips",
            headers=admin_headers,
            json={
                "topic_id": topic_id,
                "title": f"Tip #{i+1}",
                "body": f"Body {i+1}",
                "source_url": "https://example.com/a",
            },
        )
        assert r.status_code in (200, 201), r.text

    # ------------------------------
    # 3) User subscribes to the topic
    # ------------------------------
    r = client.post(
        "/subscriptions",
        headers=user_headers,
        json={"topic_id": topic_id},
    )
    assert r.status_code in (200, 201, 204), r.text

    # ------------------------------
    # 4) User requests their daily tips
    # ------------------------------
    r = client.get("/me/tips/today", headers=user_headers)
    assert r.status_code == 200, r.text
    data = r.json()

    # ------------------------------
    # 5) Validate response
    # ------------------------------
    assert data["count"] >= 1  # At least one tip should be returned
    assert len(data["items"]) >= 1
    # Tip belongs to the correct topic
    assert data["items"][0]["topic_id"] == topic_id
