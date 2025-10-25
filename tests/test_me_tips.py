import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import Tip, Topic, Subscription, Delivery

# ==============================
# Helper factory functions
# ==============================
# Small helpers to create topics, tips and subscriptions via API
# so tests remain readable and DRY.


def _create_topic(client, admin_headers, name="Nutrición", slug="nutricion"):
    # Create a topic as admin and return its JSON payload
    res = client.post(
        "/topics", json={"name": name, "slug": slug, "is_active": True}, headers=admin_headers)
    assert res.status_code == 201
    return res.json()


def _create_tip(client, admin_headers, topic_id, title, body):
    # Create a tip under a given topic and return its JSON payload
    res = client.post("/tips", json={"topic_id": topic_id, "title": title,
                      "body": body, "source_url": None}, headers=admin_headers)
    assert res.status_code == 201
    return res.json()


def _subscribe(client, user_headers, topic_id):
    # Subscribe the current user to a given topic
    res = client.post("/subscriptions",
                      json={"topic_id": topic_id}, headers=user_headers)
    assert res.status_code in (200, 201)
    return res.json()


# ==============================
# /me/tips/today + history tests
# ==============================
# Validates delivery registration, uniqueness, history listing,
# and parameterized per-topic selection.

@pytest.mark.parametrize("per_topic", [1, 2])
def test_today_registers_deliveries_and_history(client, db_session: Session, admin_headers, user_headers, per_topic):
    # 1) Create a topic and several tips
    topic = _create_topic(client, admin_headers(), name="Manga", slug="manga")
    for i in range(5):
        _create_tip(client, admin_headers(),
                    topic_id=topic["id"], title=f"Tip {i}", body=f"Cuerpo {i}")

    # 2) Subscribe the user to that topic
    _subscribe(client, user_headers(), topic_id=topic["id"])

    # 3) Call /me/tips/today to register today's deliveries
    r = client.get(
        f"/me/tips/today?per_topic={per_topic}", headers=user_headers())
    assert r.status_code == 200
    payload = r.json()
    assert payload["count"] == per_topic

    # 4) Verify deliveries in DB (uniqueness by (tip_id, user_id))
    deliveries = db_session.execute(select(Delivery)).scalars().all()
    assert len(deliveries) == per_topic

    # 5) Repeating /today must NOT create duplicates due to UNIQUE constraint
    r2 = client.get(
        f"/me/tips/today?per_topic={per_topic}", headers=user_headers())
    assert r2.status_code == 200
    deliveries_after = db_session.execute(select(Delivery)).scalars().all()
    assert len(deliveries_after) == len(deliveries)  # no new records

    # 6) /me/tips/history lists what was created
    h = client.get("/me/tips/history?page=1&size=50", headers=user_headers())
    assert h.status_code == 200
    hist = h.json()
    assert hist["total"] == len(deliveries_after)
    assert len(hist["items"]) == len(deliveries_after)
    assert hist["items"][0]["tip"]["title"].startswith("Tip")


def test_today_fallback_when_no_undelivered(client, db_session: Session, admin_headers, user_headers):
    # Topic with a single tip:
    # - First /today creates 1 delivery
    # - Second /today triggers fallback (returns something but should not create a new delivery)
    topic = _create_topic(client, admin_headers(),
                          name="Fútbol", slug="futbol")
    tip = _create_tip(client, admin_headers(),
                      topic_id=topic["id"], title="Unico tip", body="...")

    _subscribe(client, user_headers(), topic_id=topic["id"])

    r1 = client.get("/me/tips/today?per_topic=1", headers=user_headers())
    assert r1.status_code == 200

    # One delivery must exist now
    c1 = db_session.query(Delivery).count()
    assert c1 == 1

    # Second call: fallback should NOT create a new delivery
    r2 = client.get("/me/tips/today?per_topic=1", headers=user_headers())
    assert r2.status_code == 200

    c2 = db_session.query(Delivery).count()
    assert c2 == c1  # still 1


def test_history_filter_by_topic(client, db_session: Session, admin_headers, user_headers):
    # Create 2 topics and several tips under each
    t1 = _create_topic(client, admin_headers(),
                       name="Nutrición", slug="nutricion")
    t2 = _create_topic(client, admin_headers(), name="Fútbol", slug="futbol")

    for i in range(3):
        _create_tip(client, admin_headers(),
                    topic_id=t1["id"], title=f"N{i}", body=f"N{i}")
    for i in range(2):
        _create_tip(client, admin_headers(),
                    topic_id=t2["id"], title=f"F{i}", body=f"F{i}")

    # Subscribe to both topics
    _subscribe(client, user_headers(), topic_id=t1["id"])
    _subscribe(client, user_headers(), topic_id=t2["id"])

    # Generate deliveries via /today
    client.get("/me/tips/today?per_topic=1", headers=user_headers())

    # History without filter: should be one per topic (total 2)
    all_hist = client.get("/me/tips/history?page=1&size=50",
                          headers=user_headers()).json()
    assert all_hist["total"] == 2  # one per topic

    # Filter by first topic
    h1 = client.get(
        f"/me/tips/history?page=1&size=50&topic_id={t1['id']}", headers=user_headers()).json()
    assert h1["total"] == 1
    assert h1["items"][0]["topic"]["id"] == t1["id"]

    # Filter by second topic
    h2 = client.get(
        f"/me/tips/history?page=1&size=50&topic_id={t2['id']}", headers=user_headers()).json()
    assert h2["total"] == 1
    assert h2["items"][0]["topic"]["id"] == t2["id"]


def test_mark_delivery_read_idempotent(client, db_session: Session, admin_headers, user_headers):
    # 1) Create topic/tip and subscribe
    t = _create_topic(client, admin_headers(),
                      name="Nutrición", slug="nutricion2")
    tip = _create_tip(client, admin_headers(),
                      topic_id=t["id"], title="Tip X", body="Body X")
    _subscribe(client, user_headers(), topic_id=t["id"])

    # 2) Generate a delivery with /today
    r = client.get("/me/tips/today?per_topic=1", headers=user_headers())
    assert r.status_code == 200

    # 3) Fetch history to get the delivery_id
    h = client.get("/me/tips/history?page=1&size=10",
                   headers=user_headers()).json()
    assert h["total"] >= 1
    delivery_id = h["items"][0]["delivery_id"]

    # 4) PATCH /read should set status to "read"
    p1 = client.patch(f"/me/tips/{delivery_id}/read", headers=user_headers())
    assert p1.status_code == 200
    assert p1.json()["status"] == "read"

    # 5) Idempotency: repeating PATCH keeps status as "read"
    p2 = client.patch(f"/me/tips/{delivery_id}/read", headers=user_headers())
    assert p2.status_code == 200
    assert p2.json()["status"] == "read"
