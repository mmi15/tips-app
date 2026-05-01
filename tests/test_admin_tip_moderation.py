def test_admin_can_filter_tips_by_status(client, admin_headers):
    r_topic = client.post(
        "/topics",
        headers=admin_headers,
        json={"name": "Status Topic", "slug": "status-topic", "is_active": True},
    )
    assert r_topic.status_code in (200, 201), r_topic.text
    topic_id = r_topic.json()["id"]

    for title, status in (
        ("Tip Draft", "draft"),
        ("Tip Pub", "published"),
        ("Tip Hidden", "hidden"),
    ):
        r_tip = client.post(
            "/tips",
            headers=admin_headers,
            json={
                "topic_id": topic_id,
                "title": title,
                "body": f"Body {title}",
                "status": status,
            },
        )
        assert r_tip.status_code in (200, 201), r_tip.text

    r = client.get("/admin/tips?status=hidden", headers=admin_headers)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["total"] >= 1
    assert all(item["status"] == "hidden" for item in payload["items"])


def test_admin_can_update_tip_status(client, admin_headers):
    r_topic = client.post(
        "/topics",
        headers=admin_headers,
        json={"name": "Moderate Topic", "slug": "moderate-topic", "is_active": True},
    )
    assert r_topic.status_code in (200, 201), r_topic.text
    topic_id = r_topic.json()["id"]

    r_tip = client.post(
        "/tips",
        headers=admin_headers,
        json={
            "topic_id": topic_id,
            "title": "Tip to moderate",
            "body": "Body",
            "status": "draft",
        },
    )
    assert r_tip.status_code in (200, 201), r_tip.text
    tip_id = r_tip.json()["id"]

    r_patch = client.patch(
        f"/admin/tips/{tip_id}/status?status=published",
        headers=admin_headers,
    )
    assert r_patch.status_code == 200, r_patch.text
    assert r_patch.json()["status"] == "published"


def test_non_admin_cannot_moderate_tips(client, admin_headers, user_headers):
    r_topic = client.post(
        "/topics",
        headers=admin_headers,
        json={"name": "No Admin Topic", "slug": "no-admin-topic", "is_active": True},
    )
    assert r_topic.status_code in (200, 201), r_topic.text
    topic_id = r_topic.json()["id"]

    r_tip = client.post(
        "/tips",
        headers=admin_headers,
        json={
            "topic_id": topic_id,
            "title": "Tip",
            "body": "Body",
        },
    )
    assert r_tip.status_code in (200, 201), r_tip.text
    tip_id = r_tip.json()["id"]

    r_list = client.get("/admin/tips", headers=user_headers)
    assert r_list.status_code == 403

    r_patch = client.patch(
        f"/admin/tips/{tip_id}/status?status=hidden",
        headers=user_headers,
    )
    assert r_patch.status_code == 403
