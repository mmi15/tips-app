def test_user_subscribes_and_gets_today_tip(client, admin_headers, user_headers):
    r = client.post("/topics", headers=admin_headers,
                    json={"name": "Daily", "slug": "daily", "is_active": True})
    assert r.status_code in (200, 201)
    topic_id = r.json()["id"]

    for i in range(2):
        r = client.post("/tips", headers=admin_headers, json={
            "topic_id": topic_id,
            "title": f"Tip #{i+1}",
            "body": f"Body {i+1}",
            "source_url": "https://example.com/a"
        })
        assert r.status_code in (200, 201), r.text

    r = client.post("/subscriptions", headers=user_headers,
                    json={"topic_id": topic_id})
    assert r.status_code in (200, 201, 204), r.text

    r = client.get("/me/tips/today", headers=user_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["count"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["topic_id"] == topic_id
